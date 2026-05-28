"""88i Supabase Tool — CRUD operations for sinistro workflow.

Integrates with Supabase for:
- Reading sinistro details (status, campos, histórico)
- Updating sinistro status (triagem → extração → validação → fraude → decisão → reembolso)
- Inserting new sinistro records
- Querying histórico (audit trail)
"""

import logging
import os
from typing import Any, Dict, Optional

from tools.registry import registry

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Initialize Supabase client using environment variables."""
    try:
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logger.warning("SUPABASE_URL or SUPABASE_KEY not set")
            return None
        
        return create_client(url, key)
    except ImportError:
        logger.warning("supabase package not installed")
        return None
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}")
        return None


async def read_sinistro_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Read sinistro record from database."""
    try:
        sinistro_id = args.get("sinistro_id")
        if not sinistro_id:
            return {"sucesso": False, "erro": "sinistro_id is required"}
        
        client = get_supabase_client()
        if not client:
            return {"sucesso": False, "erro": "Supabase client not available"}
        
        response = client.table("sinistros").select("*").eq("id", sinistro_id).execute()
        
        if response.data:
            return {
                "sucesso": True,
                "sinistro": response.data[0],
                "encontrado": True
            }
        else:
            return {
                "sucesso": True,
                "encontrado": False,
                "sinistro_id": sinistro_id
            }
    except Exception as e:
        logger.error(f"Error reading sinistro: {e}")
        return {"sucesso": False, "erro": str(e)}


async def update_sinistro_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update sinistro status or other fields."""
    try:
        sinistro_id = args.get("sinistro_id")
        if not sinistro_id:
            return {"sucesso": False, "erro": "sinistro_id is required"}
        
        # Build update payload (only provided fields)
        update_payload = {}
        for key in ["status", "score_fraude", "campos_extraidos", "analise_cobertura", "decisao"]:
            if key in args:
                update_payload[key] = args[key]
        
        if not update_payload:
            return {"sucesso": False, "erro": "No fields to update"}
        
        client = get_supabase_client()
        if not client:
            return {"sucesso": False, "erro": "Supabase client not available"}
        
        response = client.table("sinistros").update(update_payload).eq("id", sinistro_id).execute()
        
        if response.data:
            return {
                "sucesso": True,
                "sinistro_id": sinistro_id,
                "novo_status": update_payload.get("status"),
                "campos_atualizados": list(update_payload.keys())
            }
        else:
            return {"sucesso": False, "erro": "No rows updated"}
    except Exception as e:
        logger.error(f"Error updating sinistro: {e}")
        return {"sucesso": False, "erro": str(e)}


async def insert_sinistro_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert new sinistro record."""
    try:
        segurado_id = args.get("segurado_id")
        tipo = args.get("tipo")
        if not segurado_id or not tipo:
            return {"sucesso": False, "erro": "segurado_id and tipo are required"}
        
        sinistro_data = {
            "segurado_id": segurado_id,
            "tipo": tipo,
            "status": "triagem",
            "data_registro": "now()",  # Supabase will set this
            "campos_extraidos": args.get("campos_extraidos", {}),
            "score_fraude": args.get("score_fraude", 0),
            "analise_cobertura": args.get("analise_cobertura", {})
        }
        
        client = get_supabase_client()
        if not client:
            return {"sucesso": False, "erro": "Supabase client not available"}
        
        response = client.table("sinistros").insert([sinistro_data]).execute()
        
        if response.data:
            return {
                "sucesso": True,
                "sinistro_id": response.data[0].get("id"),
                "status_inicial": "triagem"
            }
        else:
            return {"sucesso": False, "erro": "Insert failed"}
    except Exception as e:
        logger.error(f"Error inserting sinistro: {e}")
        return {"sucesso": False, "erro": str(e)}


# Register tools
registry.register(
    name="supabase_read_sinistro",
    handler=read_sinistro_handler,
    toolset="delegated_ai",
    check_fn=lambda: os.getenv("SUPABASE_URL") is not None,
    schema={
        "type": "object",
        "properties": {
            "sinistro_id": {
                "type": "string",
                "description": "ID do sinistro para leitura"
            }
        },
        "required": ["sinistro_id"]
    },
    is_async=True,
    description="Read sinistro record from Supabase"
)

registry.register(
    name="supabase_update_sinistro",
    handler=update_sinistro_handler,
    toolset="delegated_ai",
    check_fn=lambda: os.getenv("SUPABASE_URL") is not None,
    schema={
        "type": "object",
        "properties": {
            "sinistro_id": {"type": "string", "description": "ID do sinistro"},
            "status": {"type": "string", "description": "Novo status (triagem, extração, validação, etc.)"},
            "score_fraude": {"type": "number", "description": "Score de fraude (0-100)"},
            "campos_extraidos": {"type": "object", "description": "Campos extraídos"},
            "analise_cobertura": {"type": "object", "description": "Resultado da análise de cobertura"},
            "decisao": {"type": "object", "description": "Decisão final (aprovado/negado/manual)"}
        },
        "required": ["sinistro_id"]
    },
    is_async=True,
    description="Update sinistro status or fields in Supabase"
)

registry.register(
    name="supabase_insert_sinistro",
    handler=insert_sinistro_handler,
    toolset="delegated_ai",
    check_fn=lambda: os.getenv("SUPABASE_URL") is not None,
    schema={
        "type": "object",
        "properties": {
            "segurado_id": {"type": "string", "description": "ID do segurado"},
            "tipo": {"type": "string", "description": "Tipo de sinistro (roubo, colisão, etc.)"},
            "campos_extraidos": {"type": "object", "description": "Campos já extraídos"},
            "score_fraude": {"type": "number", "description": "Score inicial"},
            "analise_cobertura": {"type": "object", "description": "Dados iniciais de cobertura"}
        },
        "required": ["segurado_id", "tipo"]
    },
    is_async=True,
    description="Insert new sinistro record into Supabase"
)
