"""Health check and readiness probe endpoints."""

import logging
import os
from typing import Dict, Any
from datetime import datetime
import asyncio

import httpx
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


class HealthChecker:
    """Performs system health checks."""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.check_timeout = 5.0  # seconds

    async def check_database(self) -> bool:
        """Check Supabase connectivity."""
        try:
            from supabase import create_client
            
            client = create_client(
                url=os.getenv("SUPABASE_URL"),
                key=os.getenv("SUPABASE_KEY")
            )
            response = client.table("context_cache").select("id").limit(1).execute()
            return response is not None
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return False

    async def check_external_services(self) -> Dict[str, bool]:
        """Check external service connectivity."""
        services = {}

        # Check Inngest
        try:
            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get("https://api.inngest.com/health")
                services["inngest"] = response.status_code == 200
        except Exception as e:
            logger.warning(f"Inngest check failed: {e}")
            services["inngest"] = False

        # Check Langfuse
        try:
            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get("https://cloud.langfuse.com/health")
                services["langfuse"] = response.status_code == 200
        except Exception as e:
            logger.warning(f"Langfuse check failed: {e}")
            services["langfuse"] = False

        return services

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        db_ok = await self.check_database()
        services = await self.check_external_services()

        return {
            "status": "healthy" if db_ok else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "database": "ok" if db_ok else "error",
            "services": services,
            "version": os.getenv("VERSION", "unknown")
        }


health_checker = HealthChecker()


@router.get("", name="health-check")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint (for load balancers).
    Returns immediately without expensive checks.
    """
    return {"status": "ok"}


@router.get("/live", name="liveness-probe")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes-style liveness probe.
    Returns 200 if app is running (even if degraded).
    """
    return {"status": "alive"}


@router.get("/ready", name="readiness-probe")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.
    Returns 200 only if app is ready to accept traffic.
    """
    status = await health_checker.get_health_status()
    
    if status["status"] == "healthy":
        return status
    else:
        raise HTTPException(status_code=503, detail=status)


@router.get("/detailed", name="detailed-health")
async def detailed_health() -> Dict[str, Any]:
    """Detailed health status with all checks."""
    return await health_checker.get_health_status()
