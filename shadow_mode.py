"""
shadow_mode.py — Orquestrador Shadow/Canary/Cutover (Semana 7)

Três modos de operação controlados por variável de ambiente SHADOW_MODE:

  SHADOW  (padrão): novo agente roda em paralelo, resultado descartado.
                    Apenas divergências são logadas no Langfuse.
                    Resultado retornado ao segurado = OCTA.

  CANARY  (N%):     X% dos sinistros (controlado por CANARY_PERCENT) usam o
                    novo agente. O restante continua no OCTA.
                    X é configurável: começa em 5%, vai aumentando conforme
                    a concordância com o OCTA se mantém alta.

  CUTOVER (prod):   100% dos sinistros usam o novo agente. OCTA desativado.
                    Este é o estado final (Semana 8 — CloudWalk).

Fluxo shadow:
  1. Recebe narrativa + output_octa (o que o OCTA decidiu)
  2. Roda o novo agente no mesmo sinistro
  3. Compara outputs via shadow_comparator
  4. Loga resultado no Langfuse (fail-open)
  5. Retorna o output correto conforme o modo

Métricas acumuladas:
  - total_sinistros processados
  - total_concordancias
  - divergencias_criticas
  - divergencias_altas
  - taxa_concordancia = concordancias / total

Em produção: persistir métricas no Supabase (tabela shadow_runs).
Em dev: dict em memória.
"""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from shadow_comparator import comparar, ResultadoComparacao


# ============================================================
# Constantes
# ============================================================

class ShadowModeEnum:
    SHADOW  = "shadow"
    CANARY  = "canary"
    CUTOVER = "cutover"


DEFAULT_CANARY_PERCENT = 5   # começa com 5% dos sinistros no novo agente


# ============================================================
# Estado acumulado (em memória; produção → Supabase)
# ============================================================

@dataclass
class MetricasShadow:
    total_sinistros: int = 0
    total_concordancias: int = 0
    divergencias_criticas: int = 0
    divergencias_altas: int = 0
    divergencias_por_campo: dict = field(default_factory=dict)
    ultimo_run: Optional[str] = None

    @property
    def taxa_concordancia(self) -> float:
        if self.total_sinistros == 0:
            return 1.0
        return self.total_concordancias / self.total_sinistros

    @property
    def taxa_divergencia_critica(self) -> float:
        if self.total_sinistros == 0:
            return 0.0
        return self.divergencias_criticas / self.total_sinistros


_METRICAS = MetricasShadow()


@dataclass
class ResultadoShadowRun:
    modo_efetivo: str          # "shadow" | "canary_octa" | "canary_novo" | "cutover"
    output_retornado: dict     # o que vai para o segurado/cliente
    comparacao: Optional[ResultadoComparacao]
    novo_agente_rodou: bool
    log_divergencias: list[str]


# ============================================================
# Configuração
# ============================================================

def get_modo() -> str:
    return os.getenv("SHADOW_MODE", ShadowModeEnum.SHADOW).lower()


def get_canary_percent() -> int:
    try:
        return int(os.getenv("CANARY_PERCENT", str(DEFAULT_CANARY_PERCENT)))
    except ValueError:
        return DEFAULT_CANARY_PERCENT


def _deve_usar_novo_agente(narrativa: str) -> bool:
    """
    Determina deterministicamente se este sinistro vai para o novo agente.
    Usa hash da narrativa para garantir que o mesmo sinistro sempre vai para
    o mesmo agente (idempotente entre retries).
    """
    pct = get_canary_percent()
    if pct <= 0:
        return False
    if pct >= 100:
        return True
    # Hash determinístico: mesma narrativa → mesmo resultado
    h = int(hashlib.md5(narrativa.encode()).hexdigest(), 16)
    return (h % 100) < pct


# ============================================================
# Logging de divergências
# ============================================================

def _logar_langfuse(
    narrativa: str,
    comparacao: ResultadoComparacao,
    modo: str,
    protocolo: Optional[str],
) -> None:
    """Loga divergências no Langfuse. Fail-open."""
    try:
        pub = os.getenv("LANGFUSE_PUBLIC_KEY")
        sec = os.getenv("LANGFUSE_SECRET_KEY")
        if not pub or not sec:
            return
        from langfuse import Langfuse
        lf = Langfuse(public_key=pub, secret_key=sec,
                      host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"))
        trace_id = lf.create_trace_id()
        lf.create_score(trace_id=trace_id, name="shadow_concordancia",
                        value=comparacao.score_concordancia,
                        comment=f"modo={modo} protocolo={protocolo} {comparacao.resumo}")
        if comparacao.divergencias:
            for div in comparacao.divergencias:
                lf.create_score(
                    trace_id=trace_id,
                    name=f"shadow_div_{div.campo}",
                    value=0.0,
                    comment=f"[{div.severidade}] {div.descricao}",
                )
        lf.flush()
    except Exception:
        pass  # fail-open: Langfuse nunca bloqueia o pipeline


# ============================================================
# Orquestrador principal
# ============================================================

def processar_shadow(
    narrativa: str,
    output_octa: dict,
    segurado_id: Optional[str] = None,
) -> ResultadoShadowRun:
    """
    Ponto de entrada do shadow mode.

    Args:
        narrativa:    texto livre do sinistro
        output_octa:  o que o OCTA v4.0 decidiu (dict com proxima_acao, tipo_sinistro, etc.)
        segurado_id:  ID do segurado (opcional)

    Returns:
        ResultadoShadowRun com o output a ser retornado e as divergências.
    """
    from agent import processar_narrativa

    modo = get_modo()
    log: list[str] = []
    comparacao = None

    _METRICAS.total_sinistros += 1
    _METRICAS.ultimo_run = datetime.now().isoformat()

    # ---- CUTOVER: 100% novo agente ----
    if modo == ShadowModeEnum.CUTOVER:
        resultado_novo = processar_narrativa(narrativa, segurado_id=segurado_id)
        protocolo = resultado_novo.get("protocolo")
        log.append(f"[cutover] novo agente usado — protocolo={protocolo}")
        _METRICAS.total_concordancias += 1  # cutover não compara com OCTA
        return ResultadoShadowRun(
            modo_efetivo="cutover",
            output_retornado=resultado_novo,
            comparacao=None,
            novo_agente_rodou=True,
            log_divergencias=log,
        )

    # ---- CANARY: X% novo agente, restante OCTA ----
    if modo == ShadowModeEnum.CANARY:
        usar_novo = _deve_usar_novo_agente(narrativa)
        if usar_novo:
            resultado_novo = processar_narrativa(narrativa, segurado_id=segurado_id)
            # Mesmo em canary, compara para coletar métricas
            comparacao = comparar(output_octa, resultado_novo)
            _atualizar_metricas(comparacao)
            _logar_langfuse(narrativa, comparacao, "canary_novo", resultado_novo.get("protocolo"))
            log.append(f"[canary] novo agente ativo — concordância={comparacao.score_concordancia:.0%}")
            return ResultadoShadowRun(
                modo_efetivo="canary_novo",
                output_retornado=resultado_novo,
                comparacao=comparacao,
                novo_agente_rodou=True,
                log_divergencias=log,
            )
        else:
            # Este sinistro vai para o OCTA — mas ainda roda o novo em background para comparar
            resultado_novo = _rodar_silencioso(narrativa, segurado_id)
            if resultado_novo:
                comparacao = comparar(output_octa, resultado_novo)
                _atualizar_metricas(comparacao)
                _logar_langfuse(narrativa, comparacao, "canary_octa", None)
                log.append(f"[canary_shadow] OCTA retornado, novo rodou em background — concordância={comparacao.score_concordancia:.0%}")
            else:
                _METRICAS.total_concordancias += 1
                log.append("[canary_shadow] falha no novo agente em background")
            return ResultadoShadowRun(
                modo_efetivo="canary_octa",
                output_retornado=output_octa,
                comparacao=comparacao,
                novo_agente_rodou=resultado_novo is not None,
                log_divergencias=log,
            )

    # ---- SHADOW: 0% novo agente (só observa) ----
    resultado_novo = _rodar_silencioso(narrativa, segurado_id)
    if resultado_novo:
        comparacao = comparar(output_octa, resultado_novo)
        _atualizar_metricas(comparacao)
        _logar_langfuse(narrativa, comparacao, "shadow", None)
        if comparacao.divergencias:
            for div in comparacao.divergencias:
                log.append(f"[shadow][{div.severidade}] {div.campo}: {div.descricao}")
        else:
            log.append(f"[shadow] concordância total ({comparacao.score_concordancia:.0%})")
    else:
        _METRICAS.total_concordancias += 1
        log.append("[shadow] novo agente falhou — OCTA retornado")

    return ResultadoShadowRun(
        modo_efetivo="shadow",
        output_retornado=output_octa,
        comparacao=comparacao,
        novo_agente_rodou=resultado_novo is not None,
        log_divergencias=log,
    )


def _rodar_silencioso(narrativa: str, segurado_id: Optional[str]) -> Optional[dict]:
    """Roda o novo agente capturando exceções — fail-open."""
    try:
        from agent import processar_narrativa
        return processar_narrativa(narrativa, segurado_id=segurado_id)
    except Exception:
        return None


def _atualizar_metricas(comparacao: ResultadoComparacao) -> None:
    _METRICAS.total_sinistros += 1
    if comparacao.concordancia:
        _METRICAS.total_concordancias += 1
    criticas = sum(1 for d in comparacao.divergencias if d.severidade == "critica")
    altas    = sum(1 for d in comparacao.divergencias if d.severidade == "alta")
    _METRICAS.divergencias_criticas += criticas
    _METRICAS.divergencias_altas    += altas
    for div in comparacao.divergencias:
        _METRICAS.divergencias_por_campo[div.campo] = (
            _METRICAS.divergencias_por_campo.get(div.campo, 0) + 1
        )


def resetar_metricas() -> None:
    """Reseta contadores in-place — útil para testes."""
    _METRICAS.total_sinistros = 0
    _METRICAS.total_concordancias = 0
    _METRICAS.divergencias_criticas = 0
    _METRICAS.divergencias_altas = 0
    _METRICAS.divergencias_por_campo = {}
    _METRICAS.ultimo_run = None


def relatorio() -> dict:
    """Retorna métricas acumuladas do shadow mode."""
    m = _METRICAS
    return {
        "modo_atual": get_modo(),
        "canary_percent": get_canary_percent() if get_modo() == ShadowModeEnum.CANARY else None,
        "total_sinistros": m.total_sinistros,
        "total_concordancias": m.total_concordancias,
        "divergencias_criticas": m.divergencias_criticas,
        "divergencias_altas": m.divergencias_altas,
        "taxa_concordancia": round(m.taxa_concordancia, 3),
        "taxa_divergencia_critica": round(m.taxa_divergencia_critica, 3),
        "divergencias_por_campo": m.divergencias_por_campo,
        "ultimo_run": m.ultimo_run,
        "pronto_para_cutover": (
            m.total_sinistros >= 100
            and m.taxa_concordancia >= 0.95
            and m.taxa_divergencia_critica <= 0.02
        ),
    }
