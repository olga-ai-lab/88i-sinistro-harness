"""88i Sinistro Tools — Wrappers around Phase 1 skills for agent orchestration.

These tools allow the Hermes agent to invoke sinistro skills (analyzer, fraude-detector, etc.)
directly. Each tool maps to a skill trigger and returns structured JSON for downstream tools.
"""

import json
import logging
from typing import Any, Dict, Optional

from tools.registry import registry

logger = logging.getLogger(__name__)


# Tool: Extract fields from a sinistro document
async def extract_fields_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured fields from a sinistro document using sinistro-analyzer skill."""
    try:
        documento_tipo = args.get("documento_tipo", "boletim_ocorrencia")
        documento_texto = args.get("documento_texto", "")
        sinistro_id = args.get("sinistro_id", "unknown")
        
        # In Phase 2.2, this will call the actual sinistro-analyzer skill
        # For now, return mock structured data
        campos_extraidos = {
            "numero_bo": documento_texto.split("Número BO:")[1].split("\n")[0].strip() if "Número BO:" in documento_texto else "N/A",
            "data": documento_texto.split("Data:")[1].split("\n")[0].strip() if "Data:" in documento_texto else "N/A",
            "tipo": documento_texto.split("Tipo:")[1].split("\n")[0].strip() if "Tipo:" in documento_texto else "N/A",
            "documento_tipo": documento_tipo,
        }
        
        return {
            "sucesso": True,
            "sinistro_id": sinistro_id,
            "campos_extraidos": campos_extraidos,
            "confianca": 0.95,
            "skill_usado": "sinistro-analyzer"
        }
    except Exception as e:
        logger.error(f"Erro ao extrair campos: {e}")
        return {
            "sucesso": False,
            "erro": str(e),
            "sinistro_id": args.get("sinistro_id", "unknown")
        }


# Tool: Score fraud risk for a sinistro
async def fraud_score_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Score fraud risk using fraude-detector skill."""
    try:
        sinistro_id = args.get("sinistro_id", "unknown")
        segurado_id = args.get("segurado_id", "unknown")
        campos_extraidos = args.get("campos_extraidos", {})
        
        # In Phase 2.2, this will call the actual fraude-detector skill
        # For now, return mock fraud score
        score = 35 if campos_extraidos.get("valor_indenizacao", 0) > 10000 else 15
        
        return {
            "sucesso": True,
            "sinistro_id": sinistro_id,
            "segurado_id": segurado_id,
            "score_fraude": score,
            "risco_nivel": "medio" if score > 30 else "baixo",
            "skill_usado": "fraude-detector"
        }
    except Exception as e:
        logger.error(f"Erro ao calcular score de fraude: {e}")
        return {
            "sucesso": False,
            "erro": str(e),
            "sinistro_id": args.get("sinistro_id", "unknown")
        }


# Register tools
registry.register(
    name="sinistro_extract_fields",
    toolset="delegated_ai",
    schema={
        "type": "object",
        "properties": {
            "documento_tipo": {
                "type": "string",
                "description": "Tipo de documento (boletim_ocorrencia, laudo, etc.)"
            },
            "documento_texto": {
                "type": "string",
                "description": "Texto extraído do documento"
            },
            "sinistro_id": {
                "type": "string",
                "description": "ID do sinistro na base de dados"
            }
        },
        "required": ["documento_tipo", "documento_texto", "sinistro_id"]
    },
    handler=extract_fields_handler,
    check_fn=lambda: True,
    description="Extract structured fields from a sinistro document using sinistro-analyzer skill",
    is_async=True
)

registry.register(
    name="sinistro_fraud_score",
    toolset="delegated_ai",
    schema={
        "type": "object",
        "properties": {
            "sinistro_id": {
                "type": "string",
                "description": "ID do sinistro"
            },
            "segurado_id": {
                "type": "string",
                "description": "ID do segurado"
            },
            "campos_extraidos": {
                "type": "object",
                "description": "Campos já extraídos do documento"
            }
        },
        "required": ["sinistro_id", "segurado_id", "campos_extraidos"]
    },
    handler=fraud_score_handler,
    check_fn=lambda: True,
    description="Score fraud risk for a sinistro claim using fraude-detector skill",
    is_async=True
)
