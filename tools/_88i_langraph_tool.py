"""88i LangGraph Tool — Conversation state management for multi-turn sinistro workflows.

Maintains context across turns:
- Save state (campos extraídos, scores, histórico)
- Load state (recuperar contexto anterior)
- Update state (incrementar informações)
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from tools.registry import registry

logger = logging.getLogger(__name__)

# In-memory state store for Phase 2 (will be replaced by Supabase in Phase 3)
_conversation_states: Dict[str, Dict[str, Any]] = {}


async def save_state_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Save conversation state for a sinistro workflow."""
    try:
        conversation_id = args.get("conversation_id")
        sinistro_id = args.get("sinistro_id")
        estado = args.get("estado", {})
        
        if not conversation_id:
            return {"sucesso": False, "erro": "conversation_id is required"}
        
        # Store state with timestamp
        _conversation_states[conversation_id] = {
            "sinistro_id": sinistro_id,
            "estado": estado,
            "timestamp": datetime.now().isoformat(),
            "ultima_atualizacao": "save"
        }
        
        return {
            "sucesso": True,
            "conversation_id": conversation_id,
            "sinistro_id": sinistro_id,
            "estado_salvo": True
        }
    except Exception as e:
        logger.error(f"Error saving state: {e}")
        return {"sucesso": False, "erro": str(e)}


async def load_state_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Load conversation state for a sinistro workflow."""
    try:
        conversation_id = args.get("conversation_id")
        
        if not conversation_id:
            return {"sucesso": False, "erro": "conversation_id is required"}
        
        # Load state or return empty
        state_data = _conversation_states.get(conversation_id, {})
        
        return {
            "sucesso": True,
            "conversation_id": conversation_id,
            "sinistro_id": state_data.get("sinistro_id"),
            "estado": state_data.get("estado", {}),
            "timestamp": state_data.get("timestamp"),
            "encontrado": conversation_id in _conversation_states
        }
    except Exception as e:
        logger.error(f"Error loading state: {e}")
        return {"sucesso": False, "erro": str(e)}


async def update_state_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update conversation state (merge with existing)."""
    try:
        conversation_id = args.get("conversation_id")
        atualizacoes = args.get("atualizacoes", {})
        
        if not conversation_id:
            return {"sucesso": False, "erro": "conversation_id is required"}
        
        # Load existing state or create new
        if conversation_id not in _conversation_states:
            _conversation_states[conversation_id] = {
                "estado": {},
                "timestamp": datetime.now().isoformat(),
                "ultima_atualizacao": "criacao"
            }
        
        # Merge updates
        _conversation_states[conversation_id]["estado"].update(atualizacoes)
        _conversation_states[conversation_id]["timestamp"] = datetime.now().isoformat()
        _conversation_states[conversation_id]["ultima_atualizacao"] = "update"
        
        return {
            "sucesso": True,
            "conversation_id": conversation_id,
            "atualizacoes_aplicadas": list(atualizacoes.keys()),
            "novo_estado": _conversation_states[conversation_id]["estado"]
        }
    except Exception as e:
        logger.error(f"Error updating state: {e}")
        return {"sucesso": False, "erro": str(e)}


# Register tools
registry.register(
    name="langraph_save_state",
    handler=save_state_handler,
    toolset="delegated_ai",
    check_fn=lambda: True,
    is_async=True,
    schema={
        "type": "object",
        "properties": {
            "conversation_id": {
                "type": "string",
                "description": "ID da conversa"
            },
            "sinistro_id": {
                "type": "string",
                "description": "ID do sinistro"
            },
            "estado": {
                "type": "object",
                "description": "Estado a ser salvo (campos, scores, histórico)"
            }
        },
        "required": ["conversation_id", "estado"]
    },
    description="Save conversation state for sinistro workflow"
)

registry.register(
    name="langraph_load_state",
    handler=load_state_handler,
    toolset="delegated_ai",
    check_fn=lambda: True,
    is_async=True,
    schema={
        "type": "object",
        "properties": {
            "conversation_id": {
                "type": "string",
                "description": "ID da conversa"
            }
        },
        "required": ["conversation_id"]
    },
    description="Load conversation state for sinistro workflow"
)

registry.register(
    name="langraph_update_state",
    handler=update_state_handler,
    toolset="delegated_ai",
    check_fn=lambda: True,
    is_async=True,
    schema={
        "type": "object",
        "properties": {
            "conversation_id": {
                "type": "string",
                "description": "ID da conversa"
            },
            "atualizacoes": {
                "type": "object",
                "description": "Atualizações para mesclar (merge) no estado"
            }
        },
        "required": ["conversation_id", "atualizacoes"]
    },
    description="Update conversation state for sinistro workflow"
)
