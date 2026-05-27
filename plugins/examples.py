"""Example plugins for Phase 3."""

from typing import Any, Dict
from plugins.base import ToolPlugin, SkillPlugin, ContextPlugin, PluginMetadata


class ReembolsoToolPlugin(ToolPlugin):
    """Example tool plugin for reembolso (reimbursement) processing."""
    
    name = "reembolso_tool"
    version = "1.0.0"
    tool_name = "reembolso_process"
    metadata = PluginMetadata(
        name="reembolso_tool",
        version="1.0.0",
        description="Process reimbursement for approved claims"
    )
    
    async def initialize(self):
        """Initialize reembolso tool."""
        pass
    
    async def execute(
        self,
        sinistro_id: str,
        valor_indenizacao: float,
        metodo_pagamento: str = "transferencia",
        **kwargs
    ) -> Dict[str, Any]:
        """Process reimbursement."""
        return {
            "sucesso": True,
            "sinistro_id": sinistro_id,
            "valor_processado": valor_indenizacao,
            "metodo_pagamento": metodo_pagamento,
            "status": "processando"
        }


class NotificacaoSkillPlugin(SkillPlugin):
    """Example skill plugin for notifications."""
    
    name = "notificacao_skill"
    version = "1.0.0"
    skill_name = "notificar_segurado"
    skill_triggers = ["notificar", "enviar mensagem", "comunicar"]
    metadata = PluginMetadata(
        name="notificacao_skill",
        version="1.0.0",
        description="Notify policyholder of claim status"
    )
    
    async def initialize(self):
        """Initialize notification skill."""
        pass
    
    async def execute(
        self,
        segurado_id: str,
        canal: str = "email",
        mensagem: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Send notification."""
        return {
            "sucesso": True,
            "segurado_id": segurado_id,
            "canal": canal,
            "status": "enviado"
        }


class ComercialContextPlugin(ContextPlugin):
    """Example context plugin for commercial rules."""
    
    name = "comercial_context"
    version = "1.0.0"
    context_provider_name = "comercial_rules"
    metadata = PluginMetadata(
        name="comercial_context",
        version="1.0.0",
        description="Provide commercial rules and pricing"
    )
    
    async def initialize(self):
        """Initialize comercial context."""
        pass
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute (for Plugin interface)."""
        return await self.get_context(**kwargs)
    
    async def get_context(self, segurado_tipo: str = None, **kwargs) -> Dict[str, Any]:
        """Get commercial context."""
        return {
            "comercial": {
                "desconto_fidelidade": 0.15,
                "bonus_multiplas_apolices": 0.10,
                "taxa_administrativo": 50.00,
                "margem_lucro": 0.25
            }
        }
