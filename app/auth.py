"""
Authentication and authorization utilities.

Provides:
  - HTTPBearer: FastAPI security scheme
  - verify_api_key: Validate API key from Authorization header
  - verify_internal_request: Validate request from internal IP
  
Protects against:
  - OWASP #1: Broken Authentication
  - OWASP #2: Access Control failures
  - OWASP #7: Authentication Failures
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

logger = logging.getLogger(__name__)

# Security scheme for FastAPI docs
security = HTTPBearer(description="API Key in Authorization header")


def verify_api_key(authorization_header: Optional[str]) -> str:
    """
    Verify API key from Authorization header.
    
    Checks Authorization header against API_KEY_PRODUCTION env var.
    Logs all attempts (success and failure) for audit trail.
    
    Args:
        authorization_header: Value of Authorization header
        
    Returns:
        str: The API key if valid
        
    Raises:
        HTTPException: 403 if key is invalid or missing
        
    Protects against:
      - OWASP #1: Broken Authentication
      - OWASP #7: Identification & Authentication Failures
    """
    expected_key = os.getenv("API_KEY_PRODUCTION")
    
    if not expected_key:
        logger.error(
            "API_KEY_PRODUCTION not configured in environment"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured",
        )
    
    if not authorization_header:
        logger.warning("API authentication attempt: missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid API key",
        )
    
    # Extract key from "Bearer <key>" format
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(
            f"API authentication attempt: invalid header format"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid API key",
        )
    
    provided_key = parts[1]
    
    # Compare keys (constant-time comparison to prevent timing attacks)
    if len(provided_key) != len(expected_key):
        logger.warning(
            "API authentication attempt: key length mismatch"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid API key",
        )
    
    # Constant-time string comparison
    match = True
    for a, b in zip(provided_key, expected_key):
        if a != b:
            match = False
    
    if not match:
        logger.warning("API authentication attempt: invalid key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid API key",
        )
    
    logger.info("API authentication successful")
    return provided_key


def verify_internal_request(request: Request) -> bool:
    """
    Verify that request originates from an internal IP.
    
    Validates client IP against INTERNAL_IPS env var (comma-separated list).
    Also checks X-Forwarded-For header for proxy scenarios.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        bool: True if IP is in internal IP list
        
    Raises:
        HTTPException: 403 if IP is not in internal list
        
    Protects against:
      - OWASP #2: Broken Access Control
      - OWASP #10: Server-Side Request Forgery (SSRF)
    """
    internal_ips_str = os.getenv("INTERNAL_IPS", "127.0.0.1,localhost")
    internal_ips = [ip.strip() for ip in internal_ips_str.split(",")]
    
    # Get client IP (handle proxy headers)
    client_ip = request.client.host if request.client else None
    
    # Check X-Forwarded-For header (for proxy scenarios)
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()
    
    if not client_ip:
        logger.warning("Internal access attempt: could not determine client IP")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    if client_ip not in internal_ips:
        logger.warning(
            f"Internal access attempt from unauthorized IP: {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    logger.info(f"Internal access verified from {client_ip}")
    return True
