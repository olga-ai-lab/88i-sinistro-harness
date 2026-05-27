"""Insurance domain context provider."""

from typing import Any, Dict
from context_engine.base import ContextProvider


class InsuranceContextProvider(ContextProvider):
    """Provides insurance-specific context (rules, coverage, workflows)."""
    
    # Domain knowledge lookup tables
    SINISTRO_TIPOS = {
        "roubo": {
            "regras": [
                "Requer Boletim de Ocorrência (BO)",
                "Valor máximo indenização: R$ 50.000",
                "Prazo de análise: 10 dias úteis",
                "Documentos obrigatórios: BO, RG, CPF, comprovante endereço"
            ],
            "cobertura_padrao": "Roubo Total + Parcial",
            "franquia": "10%"
        },
        "colisao": {
            "regras": [
                "Requer fotos do dano",
                "Orçamento de oficina autorizada",
                "Pode não exigir BO se consensual"
            ],
            "cobertura_padrao": "Danos ao veículo",
            "franquia": "5%"
        },
        "incendio": {
            "regras": [
                "Requer laudo de perito",
                "Documentação de perda total",
                "Investigação obrigatória"
            ],
            "cobertura_padrao": "Incêndio Total",
            "franquia": "15%"
        }
    }
    
    VEICULO_TIPOS = {
        "moto": {"cobertura_reduzida": True, "desconto_roubo": 0.15},
        "carro": {"cobertura_reduzida": False, "desconto_roubo": 0.10},
        "caminhao": {"cobertura_reduzida": False, "desconto_roubo": 0.05}
    }
    
    async def get_context(
        self,
        sinistro_tipo: str | None = None,
        veiculo_tipo: str | None = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get insurance context based on sinistro and vehicle type."""
        context = {
            "sistema": "88i Seguradora Digital",
            "versao": "1.0.0",
            "data_referencia": "2026-05-27"
        }
        
        # Add sinistro type context
        if sinistro_tipo and sinistro_tipo in self.SINISTRO_TIPOS:
            context["sinistro_info"] = self.SINISTRO_TIPOS[sinistro_tipo]
        
        # Add vehicle type context
        if veiculo_tipo and veiculo_tipo in self.VEICULO_TIPOS:
            context["veiculo_info"] = self.VEICULO_TIPOS[veiculo_tipo]
        
        # Add workflow
        context["workflow"] = {
            "etapas": [
                "triagem",
                "extração",
                "validação",
                "fraude_scoring",
                "análise_cobertura",
                "decisão",
                "reembolso"
            ],
            "sla_dias": 10
        }
        
        return context
