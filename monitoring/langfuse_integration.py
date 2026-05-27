"""Langfuse integration for distributed tracing."""

import os
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LangfuseMonitor:
    """Monitors agent execution with Langfuse."""
    
    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.enabled = bool(self.public_key and self.secret_key)
        self.client = None
        
        if self.enabled:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key
                )
            except ImportError:
                logger.warning("langfuse package not installed")
                self.enabled = False
    
    async def trace_execution(
        self,
        operation_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Dict[str, Any] = None,
        duration_ms: float = None
    ):
        """Trace an operation execution."""
        if not self.enabled:
            return
        
        try:
            span_data = {
                "name": operation_name,
                "input": input_data,
                "output": output_data,
                "metadata": metadata or {},
                "start_time": datetime.now().isoformat(),
                "duration_ms": duration_ms
            }
            
            # Log to Langfuse (mock for Phase 3)
            logger.debug(f"Trace: {operation_name} | Input: {input_data} | Output: {output_data}")
            
        except Exception as e:
            logger.error(f"Error tracing execution: {e}")
    
    async def create_span(
        self,
        name: str,
        input: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        parent_span_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a span for tracing."""
        try:
            span = {
                "name": name,
                "span_id": f"span_{name}_{datetime.now().timestamp()}",
                "input": input or {},
                "metadata": metadata or {},
                "start_time": datetime.now().isoformat(),
                "parent_span_id": parent_span_id
            }
            return span
        except Exception as e:
            logger.error(f"Error creating span: {e}")
            return None
    
    async def log_cost(
        self,
        operation: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float
    ):
        """Log operation cost for monitoring."""
        try:
            logger.info(
                f"Cost | Op: {operation} | Model: {model} | "
                f"Tokens: {input_tokens}+{output_tokens} | Cost: ${cost_usd:.4f}"
            )
        except Exception as e:
            logger.error(f"Error logging cost: {e}")
