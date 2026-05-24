"""
shadow_comparator.py — Comparação de outputs OCTA vs Novo Agente (Semana 7)

Recebe dois dicts de resultado e retorna uma análise de divergência estruturada.

Campos comparados e severidade de divergência:
  rota          → CRITICA  (define fluxo operacional — discordância é risco alto)
  tipo_sinistro → ALTA     (impacta cobertura e documentação)
  plataforma    → ALTA     (impacta regime de regras D6/D7)
  cobertura     → ALTA     (impacto financeiro direto)
  elegivel      → CRITICA  (aprovar quando não devia = prejuízo; recusar indevido = reclamação SUSEP)

Lógica OCTA de referência (saídas conhecidas do bot n8n):
  O OCTA v4.0 retorna apenas: {proxima_acao, tipo_sinistro, mensagem_ao_segurado}
  Não tem plataforma, não tem cobertura, não tem elegibilidade.
  Mapeamento: proxima_acao → rota (campo em comum para comparação).

Uso:
  from shadow_comparator import comparar, ResultadoComparacao
  resultado = comparar(output_octa, output_novo_agente)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# Tipos
# ============================================================

@dataclass
class Divergencia:
    campo: str
    severidade: str        # "critica" | "alta" | "media" | "informativa"
    valor_octa: Optional[str]
    valor_novo: Optional[str]
    descricao: str


@dataclass
class ResultadoComparacao:
    concordancia: bool             # True se nenhuma divergência crítica/alta
    score_concordancia: float      # 0.0 a 1.0 (1.0 = concordância total)
    divergencias: list[Divergencia]
    # Campos comparados
    rota_octa: Optional[str]
    rota_novo: Optional[str]
    tipo_octa: Optional[str]
    tipo_novo: Optional[str]
    # Resumo
    resumo: str
    requer_revisao_manual: bool    # True se divergência crítica


# ============================================================
# Mapeamentos
# ============================================================

# Mapeia saída do OCTA (proxima_acao do n8n) para rota canônica
_OCTA_ROTA_MAP = {
    "pronto_para_analise":      "pronto_para_analise",
    "solicitar_esclarecimento": "solicitar_esclarecimento",
    "escalar_humano":           "escalar_humano",
    # Nomes antigos do OCTA v4.0
    "analise":                  "pronto_para_analise",
    "esclarecimento":           "solicitar_esclarecimento",
    "humano":                   "escalar_humano",
    "aprovado":                 "pronto_para_analise",
    "pendente":                 "solicitar_esclarecimento",
    "manual":                   "escalar_humano",
}

# Pesos por campo para cálculo de score
_PESOS = {
    "rota":          4,
    "tipo_sinistro": 2,
    "plataforma":    1,
    "cobertura":     2,
    "elegivel":      3,
}

# Severidade por campo
_SEVERIDADE = {
    "rota":          "critica",
    "tipo_sinistro": "alta",
    "plataforma":    "alta",
    "cobertura":     "alta",
    "elegivel":      "critica",
}


# ============================================================
# Funções auxiliares
# ============================================================

def _normalizar_rota(rota: Optional[str]) -> Optional[str]:
    if rota is None:
        return None
    return _OCTA_ROTA_MAP.get(rota.lower().strip(), rota.lower().strip())


def _normalizar(val) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "value"):
        return str(val.value).upper()
    return str(val).upper()


def _extrair_octa(output_octa: dict) -> dict:
    """Extrai campos normalizados do output do OCTA."""
    rota_raw = (
        output_octa.get("proxima_acao")
        or output_octa.get("rota")
        or output_octa.get("next_action")
    )
    tipo_raw = (
        output_octa.get("tipo_sinistro")
        or output_octa.get("type")
        or output_octa.get("sinistro_type")
    )
    return {
        "rota":          _normalizar_rota(rota_raw),
        "tipo_sinistro": _normalizar(tipo_raw),
        "plataforma":    _normalizar(output_octa.get("plataforma")),
        "cobertura":     _normalizar(output_octa.get("cobertura")),
        "elegivel":      output_octa.get("elegivel"),
    }


def _extrair_novo(output_novo: dict) -> dict:
    """Extrai campos normalizados do output do novo agente."""
    extracao = output_novo.get("extracao")
    veredicto = output_novo.get("veredicto_cobertura")

    tipo = None
    plataforma = None
    if extracao is not None:
        if isinstance(extracao, dict):
            ts = extracao.get("tipo_sinistro")
            pl = extracao.get("plataforma_mencionada")
        else:
            ts = getattr(extracao, "tipo_sinistro", None)
            pl = getattr(extracao, "plataforma_mencionada", None)
        tipo = _normalizar(ts)
        plataforma = _normalizar(pl)

    cobertura = None
    elegivel = None
    if veredicto is not None:
        if isinstance(veredicto, dict):
            cobertura = _normalizar(veredicto.get("cobertura"))
            elegivel = veredicto.get("elegivel")
        else:
            cobertura = _normalizar(getattr(veredicto, "cobertura", None))
            elegivel = getattr(veredicto, "elegivel", None)

    return {
        "rota":          _normalizar_rota(output_novo.get("proxima_acao")),
        "tipo_sinistro": tipo,
        "plataforma":    plataforma,
        "cobertura":     cobertura,
        "elegivel":      elegivel,
    }


# ============================================================
# Comparador principal
# ============================================================

def comparar(
    output_octa: dict,
    output_novo: dict,
    narrativa_id: str = "",
) -> ResultadoComparacao:
    """
    Compara os outputs do OCTA e do novo agente.

    Args:
        output_octa: dict com campos do OCTA (proxima_acao, tipo_sinistro, etc.)
        output_novo: state do novo agente (resultado de processar_narrativa())
        narrativa_id: ID opcional para rastreabilidade

    Returns:
        ResultadoComparacao com divergências e score de concordância.
    """
    octa = _extrair_octa(output_octa)
    novo = _extrair_novo(output_novo)

    divergencias: list[Divergencia] = []

    # Comparações campo a campo
    campos = [
        ("rota",          octa["rota"],          novo["rota"]),
        ("tipo_sinistro", octa["tipo_sinistro"],  novo["tipo_sinistro"]),
        ("plataforma",    octa["plataforma"],     novo["plataforma"]),
        ("cobertura",     octa["cobertura"],      novo["cobertura"]),
        ("elegivel",      octa["elegivel"],       novo["elegivel"]),
    ]

    scores_pesos = []
    for campo, val_octa, val_novo in campos:
        peso = _pesos = _PESOS[campo]

        # Pula se um dos lados não tem o campo (OCTA não tem plataforma/cobertura)
        if val_octa is None and val_novo is None:
            continue
        if val_octa is None:
            # OCTA não tem esse campo — informativo, não divergência
            scores_pesos.append((1.0, peso))
            continue

        # Ambos têm valor — compara
        concordam = str(val_octa).upper() == str(val_novo).upper() if val_novo is not None else False
        scores_pesos.append((1.0 if concordam else 0.0, peso))

        if not concordam:
            sev = _SEVERIDADE.get(campo, "media")
            divergencias.append(Divergencia(
                campo=campo,
                severidade=sev,
                valor_octa=str(val_octa) if val_octa is not None else None,
                valor_novo=str(val_novo) if val_novo is not None else None,
                descricao=_descrever_divergencia(campo, val_octa, val_novo, sev),
            ))

    # Score de concordância
    score = (
        sum(s * w for s, w in scores_pesos) / sum(w for _, w in scores_pesos)
        if scores_pesos else 1.0
    )

    tem_critica = any(d.severidade == "critica" for d in divergencias)
    tem_alta    = any(d.severidade == "alta"    for d in divergencias)
    concordancia = not tem_critica and not tem_alta

    resumo = _gerar_resumo(divergencias, score, concordancia)

    return ResultadoComparacao(
        concordancia=concordancia,
        score_concordancia=round(score, 3),
        divergencias=divergencias,
        rota_octa=octa["rota"],
        rota_novo=novo["rota"],
        tipo_octa=octa["tipo_sinistro"],
        tipo_novo=novo["tipo_sinistro"],
        resumo=resumo,
        requer_revisao_manual=tem_critica,
    )


def _descrever_divergencia(
    campo: str,
    val_octa: Optional[str],
    val_novo: Optional[str],
    sev: str,
) -> str:
    if campo == "rota":
        return (
            f"DIVERGÊNCIA CRÍTICA DE ROTA: OCTA={val_octa} vs NOVO={val_novo}. "
            f"O novo agente tomaria uma decisão de fluxo diferente."
        )
    if campo == "tipo_sinistro":
        return (
            f"Tipo de sinistro diferente: OCTA={val_octa} vs NOVO={val_novo}. "
            f"Pode impactar cobertura e documentação exigida."
        )
    if campo == "plataforma":
        return (
            f"Plataforma identificada diferente: OCTA={val_octa} vs NOVO={val_novo}. "
            f"Pode impactar regras D6/D7 e cooldown."
        )
    if campo == "cobertura":
        return (
            f"Cobertura diferente: OCTA={val_octa} vs NOVO={val_novo}. "
            f"Impacto financeiro direto."
        )
    if campo == "elegivel":
        return (
            f"Elegibilidade diferente: OCTA={val_octa} vs NOVO={val_novo}. "
            f"Risco de aprovação indevida ou recusa incorreta."
        )
    return f"{campo}: OCTA={val_octa} vs NOVO={val_novo}"


def _gerar_resumo(
    divergencias: list[Divergencia],
    score: float,
    concordancia: bool,
) -> str:
    if not divergencias:
        return f"Concordância total ({score:.0%}) — sem divergências"
    criticas = [d for d in divergencias if d.severidade == "critica"]
    altas    = [d for d in divergencias if d.severidade == "alta"]
    if criticas:
        campos = ", ".join(d.campo for d in criticas)
        return f"DIVERGÊNCIA CRÍTICA em: {campos} ({score:.0%} concordância)"
    if altas:
        campos = ", ".join(d.campo for d in altas)
        return f"Divergência alta em: {campos} ({score:.0%} concordância)"
    return f"Divergências menores ({score:.0%} concordância)"
