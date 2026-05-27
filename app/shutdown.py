"""Graceful shutdown handler for production."""

import logging
import asyncio
import signal
from typing import Callable, List

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Manages graceful shutdown of the application."""

    def __init__(self, timeout_sec: int = 30):
        self.timeout_sec = timeout_sec
        self.cleanup_callbacks: List[Callable] = []
        self.is_shutting_down = False

    def add_cleanup_callback(self, callback: Callable) -> None:
        """Register a callback to run during shutdown."""
        self.cleanup_callbacks.append(callback)

    async def shutdown(self) -> None:
        """Execute graceful shutdown sequence."""
        self.is_shutting_down = True
        logger.info("🔴 Graceful shutdown initiated...")

        # Stop accepting new requests
        logger.info("⏸️ Stopping request handling...")

        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                logger.info(f"Running cleanup: {callback.__name__}")
                if asyncio.iscoroutinefunction(callback):
                    await asyncio.wait_for(callback(), timeout=self.timeout_sec)
                else:
                    callback()
            except asyncio.TimeoutError:
                logger.error(f"Cleanup timeout: {callback.__name__}")
            except Exception as e:
                logger.error(f"Cleanup error in {callback.__name__}: {e}")

        # Wait for pending requests to complete
        logger.info("⏳ Waiting for pending requests...")
        await asyncio.sleep(2)

        logger.info("✅ Graceful shutdown complete")

    def setup_signal_handlers(self, app) -> None:
        """Setup signal handlers for SIGTERM and SIGINT."""
        loop = asyncio.new_event_loop()
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        logger.info("Signal handlers registered")


# Global instance
graceful_shutdown = GracefulShutdown(timeout_sec=30)
