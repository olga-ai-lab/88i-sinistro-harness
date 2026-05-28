"""88i Inngest Tool — Async workflow orchestration and cron job scheduling.

Triggers background processes:
- Async sinistro workflows (validação, fraude scoring, reembolso)
- Scheduled jobs (cleanup, exports, notifications)
- Event-driven triggers (webhook integrations)
"""

import json
import logging
import os
from typing import Any, Dict, Optional

from tools.registry import registry

logger = logging.getLogger(__name__)


def get_inngest_client():
    """Initialize Inngest client using environment variables."""
    try:
        from inngest import Inngest
        
        api_key = os.getenv("INNGEST_KEY")
        if not api_key:
            logger.warning("INNGEST_KEY not set")
            return None
        
        return Inngest(api_key=api_key, app_id="88i-sinistro-harness")
    except ImportError:
        logger.warning("inngest package not installed")
        return None
    except Exception as e:
        logger.error(f"Error initializing Inngest client: {e}")
        return None


async def trigger_workflow_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger an async workflow (e.g., validação, fraude scoring)."""
    try:
        workflow = args.get("workflow")
        sinistro_id = args.get("sinistro_id")
        
        if not workflow or not sinistro_id:
            return {"sucesso": False, "erro": "workflow and sinistro_id are required"}
        
        client = get_inngest_client()
        if not client:
            return {"sucesso": False, "erro": "Inngest client not available"}
        
        # Build event payload
        event_payload = {
            "name": f"88i/sinistro/{workflow}",
            "data": {
                "sinistro_id": sinistro_id,
                "workflow": workflow,
                "etapa": args.get("etapa", "processamento"),
                "timestamp": args.get("timestamp", None)
            }
        }
        
        # In production, this would use inngest.send()
        # For Phase 2, we mock the response
        event_id = f"event_{sinistro_id}_{workflow}"
        
        return {
            "sucesso": True,
            "event_id": event_id,
            "workflow": workflow,
            "sinistro_id": sinistro_id,
            "status": "agendado"
        }
    except Exception as e:
        logger.error(f"Error triggering workflow: {e}")
        return {"sucesso": False, "erro": str(e)}


async def schedule_job_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule a cron job (e.g., daily cleanup, exports)."""
    try:
        job_name = args.get("job_name")
        schedule = args.get("schedule")
        
        if not job_name or not schedule:
            return {"sucesso": False, "erro": "job_name and schedule are required"}
        
        client = get_inngest_client()
        if not client:
            return {"sucesso": False, "erro": "Inngest client not available"}
        
        # In production, this would configure a cron schedule
        # For Phase 2, we mock the response
        cron_id = f"cron_{job_name}_{schedule}"
        
        return {
            "sucesso": True,
            "cron_id": cron_id,
            "job_name": job_name,
            "schedule": schedule,
            "status": "agendado"
        }
    except Exception as e:
        logger.error(f"Error scheduling job: {e}")
        return {"sucesso": False, "erro": str(e)}


# Register tools
registry.register(
    name="inngest_trigger_workflow",
    toolset="delegated_ai",
    schema={
        "type": "object",
        "properties": {
            "workflow": {
                "type": "string",
                "description": "Workflow name (process_sinistro, validacao, fraude_scoring, reembolso)"
            },
            "sinistro_id": {
                "type": "string",
                "description": "ID do sinistro"
            },
            "etapa": {
                "type": "string",
                "description": "Etapa do workflow (triagem, extração, validação, etc.)"
            },
            "timestamp": {
                "type": "string",
                "description": "Timestamp opcional para agendamento"
            }
        },
        "required": ["workflow", "sinistro_id"]
    },
    handler=trigger_workflow_handler,
    check_fn=lambda: os.getenv("INNGEST_KEY") is not None,
    is_async=True,
    description="Trigger async workflow via Inngest"
)

registry.register(
    name="inngest_schedule_job",
    toolset="delegated_ai",
    schema={
        "type": "object",
        "properties": {
            "job_name": {
                "type": "string",
                "description": "Job name (cleanup_pending, export_daily, notify_delays)"
            },
            "schedule": {
                "type": "string",
                "description": "Cron expression (0 2 * * * for daily at 2am)"
            },
            "payload": {
                "type": "object",
                "description": "Job payload data"
            }
        },
        "required": ["job_name", "schedule"]
    },
    handler=schedule_job_handler,
    check_fn=lambda: os.getenv("INNGEST_KEY") is not None,
    is_async=True,
    description="Schedule cron job via Inngest"
)
