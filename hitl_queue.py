"""
hitl_queue.py — Fila de Revisão Humana (Semana 5 — HITL)

Responsável por:
  - Criar tarefas de revisão quando o agente escala para humano
  - Expor a fila para a Rosi (analista da 88i) via FastAPI
  - Registrar a decisão humana e retornar o resultado ao pipeline

Motivos de escalação (enum TarefaMotivo):
  - RED_FLAG_ALTA        — red flag de alta severidade na narrativa
  - VITIMA_FATAL         — caso com vítima fatal
  - FRAUDE_ESCALATION    — adjudicator detectou fraude (pipeline documental)
  - APOLICE_VENCIDA      — apólice vencida, pode haver regularização
  - ALERTA_FREQUENCIA    — >= 3 sinistros em 12 meses
  - DECISAO_INCONCLUSIVA — confiança baixa, pipeline não chegou a consenso
  - REVISAO_MANUAL       — pending_manual_review do adjudicator

Prioridade: CRITICA > ALTA > MEDIA > BAIXA
  - CRITICA: fraude ou vítima fatal
  - ALTA:    red_flag alta, fraud_score >= 6
  - MEDIA:   apólice vencida, alerta frequência
  - BAIXA:   demais casos

Em produção: persiste em Supabase (tabela `hitl_tarefas`).
Em stub: dict em memória (reinicia com o processo).

Princípios:
  - Fail-closed: se criar_tarefa falhar, o sinistro vai para escalar_humano de qualquer forma
  - Idempotente por protocolo: não cria duplicata se já existe tarefa aberta para o mesmo protocolo
  - Auditável: toda decisão registra analista + timestamp + justificativa
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ============================================================
# Enums e tipos
# ============================================================

class TarefaMotivo:
    RED_FLAG_ALTA        = "red_flag_alta"
    VITIMA_FATAL         = "vitima_fatal"
    FRAUDE_ESCALATION    = "fraude_escalation"
    APOLICE_VENCIDA      = "apolice_vencida"
    ALERTA_FREQUENCIA    = "alerta_frequencia"
    DECISAO_INCONCLUSIVA = "decisao_inconclusiva"
    REVISAO_MANUAL       = "revisao_manual"


class TarefaPrioridade:
    CRITICA = "critica"
    ALTA    = "alta"
    MEDIA   = "media"
    BAIXA   = "baixa"

    _ORDER = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}

    @classmethod
    def ordenar(cls, p: str) -> int:
        return cls._ORDER.get(p, 99)


class TarefaStatus:
    PENDENTE   = "pendente"
    EM_REVISAO = "em_revisao"
    RESOLVIDA  = "resolvida"
    EXPIRADA   = "expirada"


class DecisaoHumana:
    APROVAR          = "aprovar"
    RECUSAR          = "recusar"
    SOLICITAR_DOCS   = "solicitar_docs"
    ESCALAR_JURIDICO = "escalar_juridico"


@dataclass
class TarefaHITL:
    id: str
    protocolo: str
    segurado_id: Optional[str]
    motivo: str
    prioridade: str
    status: str
    criada_em: str
    # Contexto para a Rosi tomar decisão
    narrativa_original: str
    tipo_sinistro: Optional[str]
    plataforma: Optional[str]
    cobertura: Optional[str]
    red_flags: list[dict]
    alerta_operacional: Optional[str]
    fraud_score: int
    fraud_findings: list[str]
    veredicto_cobertura_status: Optional[str]
    veredicto_motivo_recusa: Optional[str]
    # Resolução (preenchido pela Rosi)
    resolvida_em: Optional[str] = None
    analista: Optional[str] = None
    decisao: Optional[str] = None
    justificativa: Optional[str] = None
    docs_solicitados: list[str] = field(default_factory=list)


@dataclass
class ResultadoResolucao:
    sucesso: bool
    tarefa_id: str
    decisao: str
    mensagem_ao_segurado: str
    erro: Optional[str] = None


# ============================================================
# Stub em memória (substitui Supabase em dev)
# ============================================================

_FILA: dict[str, TarefaHITL] = {}   # tarefa_id → TarefaHITL
_PROTOCOLO_IDX: dict[str, str] = {}  # protocolo → tarefa_id (dedup)


def _stub_mode() -> bool:
    return not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))


# ============================================================
# Lógica de prioridade
# ============================================================

def _calcular_prioridade(
    motivo: str,
    fraud_score: int,
    ha_vitimas_fatais: bool,
) -> str:
    if ha_vitimas_fatais or motivo == TarefaMotivo.VITIMA_FATAL:
        return TarefaPrioridade.CRITICA
    if motivo == TarefaMotivo.FRAUDE_ESCALATION or fraud_score >= 6:
        return TarefaPrioridade.ALTA
    if motivo == TarefaMotivo.RED_FLAG_ALTA:
        return TarefaPrioridade.ALTA
    if motivo in (TarefaMotivo.APOLICE_VENCIDA, TarefaMotivo.ALERTA_FREQUENCIA):
        return TarefaPrioridade.MEDIA
    return TarefaPrioridade.BAIXA


def _inferir_motivo(state: dict) -> str:
    """Infere o motivo principal da escalação a partir do state do agente."""
    extracao = state.get("extracao")
    analise_doc = state.get("analise_documental")
    historico = state.get("historico_sinistros")
    apolice = state.get("dados_apolice")
    log = state.get("log_execucao", [])

    # Fraude detectada no pipeline documental
    if analise_doc and analise_doc.veredicto:
        if analise_doc.veredicto.decision_status == "fraud_escalation":
            return TarefaMotivo.FRAUDE_ESCALATION
        if analise_doc.veredicto.human_review_required:
            return TarefaMotivo.REVISAO_MANUAL

    # Vítima fatal
    if extracao and getattr(extracao, "ha_vitimas_fatais", False):
        return TarefaMotivo.VITIMA_FATAL

    # Red flag alta na narrativa
    if extracao:
        red_flags = getattr(extracao, "red_flags", [])
        if any(getattr(rf, "severidade", "") == "alta" for rf in red_flags):
            return TarefaMotivo.RED_FLAG_ALTA

    # Histórico de frequência
    if historico and getattr(historico, "alerta_frequencia", False):
        return TarefaMotivo.ALERTA_FREQUENCIA

    # Apólice vencida
    if apolice and getattr(apolice, "encontrada", False) and not getattr(apolice, "vigente_hoje", True):
        return TarefaMotivo.APOLICE_VENCIDA

    # Confiança baixa / esclarecimento
    if extracao and getattr(extracao, "confianca", 1.0) < 0.6:
        return TarefaMotivo.DECISAO_INCONCLUSIVA

    return TarefaMotivo.REVISAO_MANUAL


# ============================================================
# API pública
# ============================================================

def criar_tarefa(state: dict) -> Optional[TarefaHITL]:
    """
    Cria uma tarefa de revisão humana a partir do state do agente.

    Idempotente: se já existe tarefa pendente para o protocolo, retorna ela.
    Fail-open: retorna None se falhar (não bloqueia o pipeline).
    """
    protocolo = state.get("protocolo") or f"sem-protocolo-{uuid.uuid4().hex[:8]}"

    # Dedup por protocolo
    if protocolo in _PROTOCOLO_IDX:
        existing_id = _PROTOCOLO_IDX[protocolo]
        if existing_id in _FILA:
            existing = _FILA[existing_id]
            if existing.status == TarefaStatus.PENDENTE:
                return existing

    try:
        extracao = state.get("extracao")
        analise_doc = state.get("analise_documental")
        veredicto_cob = state.get("veredicto_cobertura")

        # Infere campos do state
        motivo = _inferir_motivo(state)

        fraud_score = 0
        fraud_findings: list[str] = []
        if analise_doc and analise_doc.veredicto:
            fraud_score = analise_doc.veredicto.fraud_score or 0
            fraud_findings = analise_doc.veredicto.key_findings or []

        ha_fatais = bool(extracao and getattr(extracao, "ha_vitimas_fatais", False))
        prioridade = _calcular_prioridade(motivo, fraud_score, ha_fatais)

        # Red flags serializadas
        red_flags_raw = []
        if extracao:
            for rf in getattr(extracao, "red_flags", []):
                red_flags_raw.append({
                    "tipo": getattr(rf, "tipo", "outro"),
                    "descricao": getattr(rf, "descricao", ""),
                    "severidade": getattr(rf, "severidade", "baixa"),
                })

        tipo_label = None
        plataforma_label = None
        if extracao:
            ts = getattr(extracao, "tipo_sinistro", None)
            tipo_label = ts.value if ts and hasattr(ts, "value") else str(ts) if ts else None
            pl = getattr(extracao, "plataforma_mencionada", None)
            plataforma_label = pl.value if pl and hasattr(pl, "value") else str(pl) if pl else None

        tarefa = TarefaHITL(
            id=str(uuid.uuid4()),
            protocolo=protocolo,
            segurado_id=state.get("segurado_id"),
            motivo=motivo,
            prioridade=prioridade,
            status=TarefaStatus.PENDENTE,
            criada_em=datetime.now().isoformat(),
            narrativa_original=state.get("narrativa_original", "")[:500],
            tipo_sinistro=tipo_label,
            plataforma=plataforma_label,
            cobertura=veredicto_cob.cobertura if veredicto_cob else None,
            red_flags=red_flags_raw,
            alerta_operacional=state.get("alerta_operacional"),
            fraud_score=fraud_score,
            fraud_findings=fraud_findings[:5],
            veredicto_cobertura_status=veredicto_cob.status if veredicto_cob else None,
            veredicto_motivo_recusa=veredicto_cob.motivo_recusa if veredicto_cob else None,
        )

        if not _stub_mode():
            _persistir_supabase(tarefa)

        _FILA[tarefa.id] = tarefa
        _PROTOCOLO_IDX[protocolo] = tarefa.id
        return tarefa

    except Exception as e:
        # Fail-open: não bloqueia o pipeline
        return None


def listar_tarefas(
    status: str = TarefaStatus.PENDENTE,
    limit: int = 50,
) -> list[TarefaHITL]:
    """
    Lista tarefas da fila, ordenadas por prioridade e data de criação.
    Em stub: retorna do dict em memória.
    Em produção: busca no Supabase.
    """
    if not _stub_mode():
        return _listar_supabase(status, limit)

    tarefas = [t for t in _FILA.values() if t.status == status]
    tarefas.sort(key=lambda t: (
        TarefaPrioridade.ordenar(t.prioridade),
        t.criada_em,
    ))
    return tarefas[:limit]


def obter_tarefa(tarefa_id: str) -> Optional[TarefaHITL]:
    """Retorna uma tarefa pelo ID."""
    if not _stub_mode():
        return _obter_supabase(tarefa_id)
    return _FILA.get(tarefa_id)


def resolver_tarefa(
    tarefa_id: str,
    decisao: str,
    analista: str,
    justificativa: str = "",
    docs_solicitados: Optional[list[str]] = None,
) -> ResultadoResolucao:
    """
    Registra a decisão humana de uma tarefa.

    decisao: DecisaoHumana.APROVAR | RECUSAR | SOLICITAR_DOCS | ESCALAR_JURIDICO
    analista: nome/ID da analista (ex: "Rosi")
    """
    tarefa = obter_tarefa(tarefa_id)
    if not tarefa:
        return ResultadoResolucao(
            sucesso=False,
            tarefa_id=tarefa_id,
            decisao=decisao,
            mensagem_ao_segurado="",
            erro=f"Tarefa {tarefa_id} não encontrada",
        )

    if tarefa.status == TarefaStatus.RESOLVIDA:
        return ResultadoResolucao(
            sucesso=False,
            tarefa_id=tarefa_id,
            decisao=decisao,
            mensagem_ao_segurado="",
            erro=f"Tarefa {tarefa_id} já foi resolvida por {tarefa.analista}",
        )

    # Atualiza tarefa
    tarefa.status = TarefaStatus.RESOLVIDA
    tarefa.resolvida_em = datetime.now().isoformat()
    tarefa.analista = analista
    tarefa.decisao = decisao
    tarefa.justificativa = justificativa
    tarefa.docs_solicitados = docs_solicitados or []

    # Gera mensagem ao segurado baseada na decisão
    mensagem = _gerar_mensagem(tarefa)

    if not _stub_mode():
        _atualizar_supabase(tarefa)

    return ResultadoResolucao(
        sucesso=True,
        tarefa_id=tarefa_id,
        decisao=decisao,
        mensagem_ao_segurado=mensagem,
    )


def resumo_fila() -> dict:
    """Retorna contagens por status e prioridade — para o dashboard."""
    tarefas = list(_FILA.values())
    return {
        "total": len(tarefas),
        "pendentes": len([t for t in tarefas if t.status == TarefaStatus.PENDENTE]),
        "em_revisao": len([t for t in tarefas if t.status == TarefaStatus.EM_REVISAO]),
        "resolvidas": len([t for t in tarefas if t.status == TarefaStatus.RESOLVIDA]),
        "por_prioridade": {
            "critica": len([t for t in tarefas if t.prioridade == TarefaPrioridade.CRITICA and t.status == TarefaStatus.PENDENTE]),
            "alta":    len([t for t in tarefas if t.prioridade == TarefaPrioridade.ALTA    and t.status == TarefaStatus.PENDENTE]),
            "media":   len([t for t in tarefas if t.prioridade == TarefaPrioridade.MEDIA   and t.status == TarefaStatus.PENDENTE]),
            "baixa":   len([t for t in tarefas if t.prioridade == TarefaPrioridade.BAIXA   and t.status == TarefaStatus.PENDENTE]),
        },
    }


# ============================================================
# Helpers internos
# ============================================================

def _gerar_mensagem(tarefa: TarefaHITL) -> str:
    protocolo_txt = f"\nProtocolo: {tarefa.protocolo}" if tarefa.protocolo else ""

    if tarefa.decisao == DecisaoHumana.APROVAR:
        return (
            f"Seu sinistro foi analisado e aprovado por nossa equipe.{protocolo_txt}\n"
            f"Vamos prosseguir com a análise de cobertura e retornamos em breve."
        )
    elif tarefa.decisao == DecisaoHumana.RECUSAR:
        motivo = tarefa.justificativa or "não atende aos critérios de cobertura"
        return (
            f"Após análise detalhada, seu sinistro não pode ser aprovado.{protocolo_txt}\n"
            f"Motivo: {motivo}\n"
            f"Para mais informações, entre em contato: 0800 718 7813"
        )
    elif tarefa.decisao == DecisaoHumana.SOLICITAR_DOCS:
        docs_txt = ""
        if tarefa.docs_solicitados:
            docs_txt = "\n\nDocumentos necessários:\n" + "\n".join(
                f"  • {d}" for d in tarefa.docs_solicitados
            )
        return (
            f"Analisamos seu sinistro e precisamos de documentação adicional.{protocolo_txt}"
            f"{docs_txt}\n"
            f"Por favor, envie os documentos pelo mesmo canal."
        )
    elif tarefa.decisao == DecisaoHumana.ESCALAR_JURIDICO:
        return (
            f"Seu caso foi encaminhado para análise especializada.{protocolo_txt}\n"
            f"Nossa equipe jurídica entrará em contato em até 5 dias úteis."
        )
    return f"Seu sinistro está em análise.{protocolo_txt}"


# ============================================================
# Stubs de produção (Supabase) — implementar ao conectar
# ============================================================

def _persistir_supabase(tarefa: TarefaHITL) -> None:
    """Em produção: INSERT em hitl_tarefas."""
    raise NotImplementedError("Supabase não configurado")


def _listar_supabase(status: str, limit: int) -> list[TarefaHITL]:
    """Em produção: SELECT FROM hitl_tarefas WHERE status = %s ORDER BY prioridade, criada_em."""
    raise NotImplementedError("Supabase não configurado")


def _obter_supabase(tarefa_id: str) -> Optional[TarefaHITL]:
    """Em produção: SELECT FROM hitl_tarefas WHERE id = %s."""
    raise NotImplementedError("Supabase não configurado")


def _atualizar_supabase(tarefa: TarefaHITL) -> None:
    """Em produção: UPDATE hitl_tarefas SET ... WHERE id = %s."""
    raise NotImplementedError("Supabase não configurado")
