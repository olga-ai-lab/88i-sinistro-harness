"""
Encryption utilities for data protection.

Provides:
  - EncryptionManager: Symmetric encryption/decryption using Fernet
  - encryption_manager: Global instance for application use
  
Encrypts sensitive data at rest (OWASP Vulnerable Components #6, Data Integrity #8)
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages symmetric encryption/decryption using Fernet (AES-128).
    
    Fernet guarantees that data encrypted with it cannot be manipulated
    or read without the key. Includes timestamp and HMAC.
    
    Protects against:
      - OWASP #6: Vulnerable Components (weak cryptography)
      - OWASP #8: Data Integrity Failures
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager with key from environment or parameter.
        
        Args:
            encryption_key: Fernet key (32 URL-safe base64 bytes).
                          If None, reads from ENCRYPTION_KEY env var.
                          If env var not set, generates new key.
        """
        if encryption_key:
            self.key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            key_env = os.getenv("ENCRYPTION_KEY")
            if key_env:
                self.key = key_env.encode() if isinstance(key_env, str) else key_env
            else:
                # Generate new key if not provided
                logger.warning(
                    "ENCRYPTION_KEY not set in environment. "
                    "Generating new key. Set ENCRYPTION_KEY for persistence."
                )
                self.key = Fernet.generate_key()

        try:
            self.cipher = Fernet(self.key)
        except Exception as e:
            logger.error(f"Failed to initialize Fernet cipher: {e}")
            raise ValueError("Invalid encryption key format") from e

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string using Fernet.
        
        Args:
            data: Plaintext string to encrypt
            
        Returns:
            str: Base64-encoded encrypted data
            
        Raises:
            Exception: If encryption fails
        """
        try:
            plaintext = data.encode() if isinstance(data, str) else data
            encrypted = self.cipher.encrypt(plaintext)
            return encrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a Fernet-encrypted string.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            str: Decrypted plaintext
            
        Raises:
            InvalidToken: If token is invalid, tampered, or key is wrong
            Exception: If decryption fails
        """
        try:
            ciphertext = (
                encrypted_data.encode()
                if isinstance(encrypted_data, str)
                else encrypted_data
            )
            decrypted = self.cipher.decrypt(ciphertext)
            return decrypted.decode("utf-8")
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or wrong key")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


# Global encryption manager instance
# Initialize with env var or generate new key
encryption_manager: Optional[EncryptionManager] = None

try:
    encryption_manager = EncryptionManager()
    logger.info("Encryption manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize encryption manager: {e}")
    # Continue without encryption if initialization fails
    encryption_manager = None
