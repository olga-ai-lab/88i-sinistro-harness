"""Tracing decorators and utilities."""

import functools
import logging
from typing import Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


def trace_tool_execution(tool_name: str):
    """Decorator to trace tool execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.info(
                    f"Tool: {tool_name} | Status: OK | Duration: {duration:.2f}ms"
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Tool: {tool_name} | Status: ERROR | Duration: {duration:.2f}ms | Error: {e}"
                )
                raise
        
        return wrapper
    return decorator


def trace_skill_execution(skill_name: str):
    """Decorator to trace skill execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                logger.info(
                    f"Skill: {skill_name} | Status: OK | Duration: {duration:.2f}ms"
                )
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Skill: {skill_name} | Status: ERROR | Duration: {duration:.2f}ms | Error: {e}"
                )
                raise
        
        return wrapper
    return decorator
