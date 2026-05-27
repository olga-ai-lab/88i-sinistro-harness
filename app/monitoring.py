"""Monitoring and logging configuration."""

import logging
import os
from typing import Optional
from pythonjsonlogger import jsonlogger
from langfuse import Langfuse

# Initialize Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)


def setup_logging() -> None:
    """Configure structured JSON logging for production."""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if os.getenv("ENVIRONMENT") == "development" else logging.INFO)
    
    # JSON formatter for structured logs
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d'
    )
    
    # Console handler (for Railway logs)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional, for local development)
    if os.getenv("ENVIRONMENT") == "development":
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def log_deployment_info() -> None:
    """Log deployment information on startup."""
    logger = logging.getLogger(__name__)
    
    logger.info(
        "Deployment info",
        extra={
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "version": os.getenv("VERSION", "unknown"),
            "python_version": os.getenv("PYTHON_VERSION", "unknown"),
            "port": os.getenv("PORT", "8000"),
        }
    )


async def log_request_trace(request_id: str, operation: str, input_data: dict, output_data: dict) -> None:
    """Log request trace to Langfuse."""
    try:
        trace = langfuse.trace(name=operation, id=request_id)
        trace.span(
            name=f"{operation}_execution",
            input=input_data,
            output=output_data,
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log trace to Langfuse: {e}")


# Setup logging on import
setup_logging()
