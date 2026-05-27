"""
Backup and restoration management for disaster recovery.

Provides BackupManager class for creating, verifying, and restoring database backups.
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages database backups and restoration using pg_dump and psql."""

    def __init__(self, db_host: str, db_port: int, db_user: str, db_name: str, backup_dir: str = "/backups"):
        """
        Initialize BackupManager.

        Args:
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_user: PostgreSQL user
            db_name: Database name
            backup_dir: Directory to store backups
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_name = db_name
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"BackupManager initialized for {db_name} with backup dir {backup_dir}")

    async def backup_database(self) -> Dict[str, Any]:
        """
        Create a backup of the database using pg_dump.

        Returns:
            Dict containing:
                - status: 'success' or 'error'
                - file: Path to backup file (if successful)
                - timestamp: Datetime string of backup
                - size_bytes: Size of backup file in bytes
                - error: Error message (if failed)
        """
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.isoformat()
        backup_filename = f"{self.db_name}_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = self.backup_dir / backup_filename

        logger.info(f"Starting backup of {self.db_name} to {backup_path}")

        try:
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "p",  # plain text format
                "-v",  # verbose
            ]

            # Execute pg_dump
            with open(backup_path, "w") as backup_file:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=backup_file,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, "PGPASSWORD": os.environ.get("PGPASSWORD", "")},
                )
                _, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"pg_dump failed with code {process.returncode}: {error_msg}")
                return {
                    "status": "error",
                    "timestamp": timestamp_str,
                    "error": error_msg,
                }

            # Get file size
            size_bytes = backup_path.stat().st_size
            logger.info(f"Backup completed successfully: {backup_path} ({size_bytes} bytes)")

            return {
                "status": "success",
                "file": str(backup_path),
                "timestamp": timestamp_str,
                "size_bytes": size_bytes,
            }

        except Exception as e:
            logger.error(f"Backup operation failed: {str(e)}", exc_info=True)
            # Clean up partial backup file if it exists
            if backup_path.exists():
                backup_path.unlink()
            return {
                "status": "error",
                "timestamp": timestamp_str,
                "error": str(e),
            }

    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """
        Verify backup file integrity.

        Checks:
        - File exists
        - File has content (size > 0)
        - File contains valid SQL syntax

        Args:
            backup_file: Path to backup file to verify

        Returns:
            Dict containing:
                - status: 'ok', 'warning', or 'error'
                - file: Backup file path
                - timestamp: Verification timestamp
                - checks: Dict with results of each check
                - error: Error message (if any)
        """
        timestamp = datetime.utcnow().isoformat()
        backup_path = Path(backup_file)
        checks = {}

        logger.info(f"Starting verification of {backup_file}")

        try:
            # Check 1: File exists
            if not backup_path.exists():
                logger.error(f"Backup file does not exist: {backup_file}")
                checks["file_exists"] = False
                return {
                    "status": "error",
                    "file": backup_file,
                    "timestamp": timestamp,
                    "checks": checks,
                    "error": "Backup file does not exist",
                }

            checks["file_exists"] = True

            # Check 2: File has content
            file_size = backup_path.stat().st_size
            has_content = file_size > 0
            checks["has_content"] = has_content
            if not has_content:
                logger.warning(f"Backup file is empty: {backup_file}")

            # Check 3: SQL syntax validation (check for basic SQL patterns)
            try:
                with open(backup_path, "r", errors="ignore") as f:
                    content = f.read(4096)  # Read first 4KB to check syntax
                    has_sql_keywords = any(
                        keyword in content.upper() for keyword in ["CREATE", "INSERT", "SELECT", "DROP"]
                    )
                    checks["valid_sql_syntax"] = has_sql_keywords
                    if not has_sql_keywords:
                        logger.warning(f"Backup file does not contain recognizable SQL: {backup_file}")
            except Exception as e:
                logger.warning(f"Could not validate SQL syntax: {str(e)}")
                checks["valid_sql_syntax"] = False

            # Determine overall status
            all_checks_pass = all(checks.values())
            status = "ok" if all_checks_pass else "warning"

            logger.info(f"Verification completed with status: {status}")
            return {
                "status": status,
                "file": backup_file,
                "timestamp": timestamp,
                "checks": checks,
            }

        except Exception as e:
            logger.error(f"Verification operation failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "file": backup_file,
                "timestamp": timestamp,
                "checks": checks,
                "error": str(e),
            }

    async def restore_from_backup(self, backup_file: str, target_db: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore database from a backup file using psql.

        Args:
            backup_file: Path to backup file to restore
            target_db: Target database name (defaults to original db_name)

        Returns:
            Dict containing:
                - status: 'success' or 'error'
                - timestamp: Restoration timestamp
                - database: Database that was restored
                - error: Error message (if failed)
        """
        timestamp = datetime.utcnow().isoformat()
        target_database = target_db or self.db_name
        backup_path = Path(backup_file)

        logger.info(f"Starting restore from {backup_file} to {target_database}")

        try:
            # Verify backup file exists
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return {
                    "status": "error",
                    "timestamp": timestamp,
                    "error": f"Backup file not found: {backup_file}",
                }

            # Build psql command
            cmd = [
                "psql",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", target_database,
                "-f", str(backup_path),
                "-v", "ON_ERROR_STOP=1",  # Stop on first error
            ]

            # Execute restore
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PGPASSWORD": os.environ.get("PGPASSWORD", "")},
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"psql restore failed with code {process.returncode}: {error_msg}")
                return {
                    "status": "error",
                    "timestamp": timestamp,
                    "database": target_database,
                    "error": error_msg,
                }

            logger.info(f"Restore completed successfully for {target_database}")
            return {
                "status": "success",
                "timestamp": timestamp,
                "database": target_database,
            }

        except Exception as e:
            logger.error(f"Restore operation failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "timestamp": timestamp,
                "database": target_database,
                "error": str(e),
            }
