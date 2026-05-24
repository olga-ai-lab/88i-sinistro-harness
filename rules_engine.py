"""
rules_engine.py — Motor de regras 88i (Semana 3)

Avalia as tabelas DMN (dmn_tables.py) contra o state do agente
e retorna um VeredictoCobertura com decisão, docs obrigatórios e pendências.

Princípios:
  - ZERO LLM — tudo determinístico
  - Fail-closed: dúvida → pending_documents (nunca aprovar na dúvida)
  - Auditável: cada decisão carrega o código da regra que a disparou
  - Idempotente: mesma entrada → mesma saída sempre

Integração com agent.py:
  O nó `no_analisar_cobertura` chama `avaliar_cobertura(state)` e
  escreve o resultado em state["veredicto_cobertura"].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

from dmn_tables import (
    TIPO_SINISTRO_COBERTURA,
    KIT_BASICO,
    DOCS_POR_COBERTURA,
    PARAMETROS_COBERTURA,
    resolver_regime,
)


# ============================================================
# Tipo de retorno
# ============================================================

@dataclass
class VeredictoCobertura:
    # Decisão principal
    elegivel: bool
    status: str  # "approved" | "pending_documents" | "rejected"

    # Cobertura identificada
    cobertura: Optional[str] = None       # ex: "B_DITA"
    produto: Optional[str] = None         # ex: "B"
    descricao_cobertura: Optional[str] = None

    # Motivo (se recusado)
    motivo_recusa: Optional[str] = None
    regra_violada: Optional[str] = None   # ex: "D6"

    # Documentos
    docs_obrigatorios: list[str] = field(default_factory=list)
    docs_pendentes: list[str] = field(default_factory=list)   # dos obrigatórios, quais faltam

    # Parâmetros financeiros
    parametros: Optional[dict] = None

    # Trilha de auditoria
    regras_verificadas: list[str] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)


# ============================================================
# Helpers
# ============================================================

def _tipo_sinistro_str(extracao) -> Optional[str]:
    if extracao is None:
        return None
    ts = extracao.tipo_sinistro
    return ts.value if hasattr(ts, "value") else str(ts)


def _veiculo_tipo(extracao) -> Optional[str]:
    """Retorna tipo do veículo ('MOTO', 'CARRO', etc.) ou None."""
    if extracao is None or extracao.veiculo is None:
        return None
    t = extracao.veiculo.tipo
    return t.value if hasattr(t, "value") else str(t)


def _docs_mencionados(extracao) -> set[str]:
    """Retorna set com nomes de documentos citados na narrativa (lowercase)."""
    if extracao is None:
        return set()
    return {d.lower() for d in (extracao.documentos_mencionados or [])}


def _dias_desde(data: Optional[date]) -> Optional[int]:
    if data is None:
        return None
    return (date.today() - data).days


# ============================================================
# Motor principal
# ============================================================

def avaliar_cobertura(
    tipo_sinistro: Optional[str],
    dados_apolice,
    historico_sinistros,
    extracao,
    plataforma: str = "NAO_MENCIONADA",
) -> VeredictoCobertura:
    """
    Avalia elegibilidade e cobertura de um sinistro.

    Args:
        tipo_sinistro     — string do enum BAML (ex: "DITA", "BAGAGEM")
        dados_apolice     — resultado de tools.consultar_apolice()
        historico_sinistros — resultado de tools.buscar_historico_sinistros()
        extracao          — ExtracaoSinistro do BAML
        plataforma        — valor do enum Plataforma do BAML
                           (ex: "UBER", "NOVENTA_E_NOVE", "NAO_MENCIONADA")
                           Default: "NAO_MENCIONADA" → aplica regime PADRAO

    Retorna VeredictoCobertura com decisão final e docs obrigatórios.
    """
    regime = resolver_regime(plataforma)
    regras_ok: list[str] = []
    obs: list[str] = []
    obs.append(f"plataforma={plataforma} → regime={regime}")

    # ----------------------------------------------------------
    # D1: Apólice vigente
    # ----------------------------------------------------------
    regras_ok.append("D1")
    if dados_apolice is None or not dados_apolice.encontrada:
        obs.append("D1: apólice não encontrada — não é possível verificar vigência")
        return VeredictoCobertura(
            elegivel=False,
            status="rejected",
            motivo_recusa="D1: apólice não encontrada ou não cadastrada no sistema",
            regra_violada="D1",
            regras_verificadas=regras_ok,
            observacoes=obs,
        )

    if not dados_apolice.vigente_hoje:
        obs.append(f"D1: apólice vencida em {dados_apolice.vigencia_fim}")
        return VeredictoCobertura(
            elegivel=False,
            status="rejected",
            motivo_recusa=f"D1: apólice vencida em {dados_apolice.vigencia_fim}",
            regra_violada="D1",
            regras_verificadas=regras_ok,
            observacoes=obs,
        )
    obs.append("D1: apólice vigente ✓")

    # ----------------------------------------------------------
    # D2: Carência
    # ----------------------------------------------------------
    regras_ok.append("D2")
    if dados_apolice.carencia_ativa:
        obs.append("D2: sinistro durante período de carência")
        return VeredictoCobertura(
            elegivel=False,
            status="rejected",
            motivo_recusa="D2: evento ocorreu durante o período de carência da apólice",
            regra_violada="D2",
            regras_verificadas=regras_ok,
            observacoes=obs,
        )
    obs.append("D2: fora de carência ✓")

    # ----------------------------------------------------------
    # D8: Tipo de sinistro tem cobertura mapeada?
    # ----------------------------------------------------------
    regras_ok.append("D8")
    if tipo_sinistro is None or tipo_sinistro == "INDEFINIDO":
        return VeredictoCobertura(
            elegivel=False,
            status="pending_documents",
            motivo_recusa="D8: tipo de sinistro INDEFINIDO — não é possível mapear cobertura",
            regra_violada="D8",
            regras_verificadas=regras_ok,
            observacoes=obs,
        )

    # Busca cobertura na tabela pelo regime
    cobertura_match = None
    for row in TIPO_SINISTRO_COBERTURA:
        if row["tipo_sinistro"] == tipo_sinistro:
            row_regime = row.get("regime")
            if row_regime is None or row_regime == regime:
                # Linha de recusa explícita
                if row.get("elegivel") is False:
                    obs.append(f"D7/D8: {row['motivo_recusa']}")
                    return VeredictoCobertura(
                        elegivel=False,
                        status="rejected",
                        motivo_recusa=row["motivo_recusa"],
                        regra_violada="D7",
                        regras_verificadas=regras_ok,
                        observacoes=obs,
                    )
                cobertura_match = row
                break  # usa a primeira linha válida

    if cobertura_match is None:
        obs.append(f"D8: tipo '{tipo_sinistro}' não tem cobertura mapeada para plataforma {plataforma}")
        return VeredictoCobertura(
            elegivel=False,
            status="rejected",
            motivo_recusa=f"D8: sinistro tipo '{tipo_sinistro}' não tem cobertura disponível no produto 88i",
            regra_violada="D8",
            regras_verificadas=regras_ok,
            observacoes=obs,
        )

    cobertura = cobertura_match["cobertura"]
    produto = cobertura_match["produto"]
    obs.append(f"D8: cobertura {cobertura} mapeada ✓")

    # D6: Tipo de veículo (somente automóvel para Produto A/Uber)
    # ATENÇÃO: D6 NÃO se aplica no regime PADRAO (CG geral não restringe tipo de veículo)
    if produto == "A" and regime == "UBER":
        regras_ok.append("D6")
        veiculo_tipo = _veiculo_tipo(extracao)
        if veiculo_tipo and veiculo_tipo not in ("CARRO", "NAO_MENCIONADO"):
            obs.append(f"D6: veículo tipo {veiculo_tipo} — Produto A/Uber cobre somente automóveis")
            return VeredictoCobertura(
                elegivel=False,
                status="rejected",
                cobertura=cobertura,
                produto=produto,
                motivo_recusa=f"D6: Produto A (Impedimento ao Trabalho Uber) cobre somente automóveis. "
                              f"Veículo informado: {veiculo_tipo}",
                regra_violada="D6",
                regras_verificadas=regras_ok,
                observacoes=obs,
            )
        obs.append(f"D6: tipo de veículo ok ({veiculo_tipo}) ✓")
    elif produto == "A" and regime == "PADRAO":
        obs.append("D6: não aplicável no regime PADRAO (CG geral aceita qualquer veículo)")

    # ----------------------------------------------------------
    # D15: CNH ativa mencionada nos documentos
    # ----------------------------------------------------------
    if produto in ("A", "B"):
        regras_ok.append("D15")
        docs = _docs_mencionados(extracao)
        cnh_ok = any("cnh" in d or "habilitação" in d or "habilitacao" in d for d in docs)
        if not cnh_ok:
            obs.append("D15: CNH não mencionada — marcar como pendência documental")
            # Não recusa — vira pendência (pode estar com o segurado)

    # D4: Cooldown
    if produto in ("A", "B") and historico_sinistros and historico_sinistros.encontrado:
        regras_ok.append("D4")
        params = PARAMETROS_COBERTURA.get(cobertura, {})
        # DITA Uber: 30 dias | DITA padrão: 90 dias | demais: usar cooldown_dias
        if cobertura == "B_DITA" and regime == "UBER":
            cooldown = params.get("cooldown_dias", 30)
        elif cobertura == "B_DITA":
            cooldown = params.get("cooldown_dias_padrao", 90)
        else:
            cooldown = params.get("cooldown_dias")
        if cooldown:
            dias = _dias_desde(historico_sinistros.ultimo_sinistro_data)
            if dias is not None and dias < cooldown:
                obs.append(f"D4: último sinistro há {dias} dias — cooldown exige {cooldown} dias")
                return VeredictoCobertura(
                    elegivel=False,
                    status="rejected",
                    cobertura=cobertura,
                    produto=produto,
                    motivo_recusa=f"D4: cooldown não respeitado — último sinistro há {dias} dias "
                                  f"(mínimo {cooldown} dias entre sinistros da mesma cobertura)",
                    regra_violada="D4",
                    regras_verificadas=regras_ok,
                    observacoes=obs,
                )
            obs.append(f"D4: cooldown ok ({dias} dias desde último sinistro) ✓")

    # ----------------------------------------------------------
    # D11: NF de parente (Produto C)
    # ----------------------------------------------------------
    if produto == "C":
        regras_ok.append("D11")
        red_flags = extracao.red_flags if extracao else []
        for rf in red_flags:
            desc = rf.descricao.lower() if hasattr(rf, "descricao") else ""
            if "parente" in desc or "nf" in desc and "parente" in desc:
                obs.append("D11: sinal de NF de parente detectado nas red_flags")
                return VeredictoCobertura(
                    elegivel=False,
                    status="rejected",
                    cobertura=cobertura,
                    produto=produto,
                    motivo_recusa="D11: NF de parente do segurado não é aceita (Produto C)",
                    regra_violada="D11",
                    regras_verificadas=regras_ok,
                    observacoes=obs,
                )
        obs.append("D11: sem sinal de NF de parente ✓")

    # ----------------------------------------------------------
    # D12: Declaração prévia (Produto C)
    # ----------------------------------------------------------
    if produto == "C":
        regras_ok.append("D12")
        docs = _docs_mencionados(extracao)
        decl_ok = any("declaração" in d or "declaracao" in d or "declaração prévia" in d for d in docs)
        if not decl_ok:
            obs.append("D12: declaração prévia não mencionada — marcar como pendência")
            # Vira pendência documental, não recusa imediata

    # ----------------------------------------------------------
    # Monta lista de documentos obrigatórios + pendências
    # ----------------------------------------------------------
    docs_obrigatorios = KIT_BASICO + DOCS_POR_COBERTURA.get(cobertura, [])

    # Docs pendentes: os obrigatórios específicos da cobertura que não foram mencionados
    docs_citados = _docs_mencionados(extracao)
    docs_pendentes = []

    # Palavras-chave curtas que identificam cada tipo de documento
    _ALIASES: dict[str, list[str]] = {
        "bo": ["bo", "boletim", "brat"],
        "laudo": ["laudo"],
        "atestado": ["atestado"],
        "receituário": ["receituário", "receituario", "receita"],
        "relatório": ["relatório", "relatorio"],
        "comprovante": ["comprovante"],
        "nota fiscal": ["nota fiscal", "nf-e", "nfe", "nf "],
        "declaração prévia": ["declaração", "declaracao"],
        "cnh": ["cnh", "habilitação", "habilitacao"],
        "fotos": ["fotos", "foto"],
        "orçamento": ["orçamento", "orcamento"],
        "crlv": ["crlv"],
        "cpf": ["cpf", "rg"],
    }

    def _mencionado(doc_obrigatorio: str) -> bool:
        doc_lower = doc_obrigatorio.lower()
        # Verifica aliases
        for chave, aliases in _ALIASES.items():
            if chave in doc_lower:
                if any(any(a in citado for a in aliases) for citado in docs_citados):
                    return True
        # Fallback: palavras com mais de 4 chars
        palavras_chave = [p for p in doc_lower.split() if len(p) > 4]
        return any(
            any(pk in citado for pk in palavras_chave)
            for citado in docs_citados
        )

    for doc in DOCS_POR_COBERTURA.get(cobertura, []):
        if not _mencionado(doc):
            docs_pendentes.append(doc)

    obs.append(f"docs obrigatórios: {len(docs_obrigatorios)} | pendentes: {len(docs_pendentes)}")

    # ----------------------------------------------------------
    # Decisão final
    # ----------------------------------------------------------
    status = "approved" if not docs_pendentes else "pending_documents"
    obs.append(f"veredicto: {status}")

    return VeredictoCobertura(
        elegivel=True,
        status=status,
        cobertura=cobertura,
        produto=produto,
        descricao_cobertura=cobertura_match.get("descricao"),
        docs_obrigatorios=docs_obrigatorios,
        docs_pendentes=docs_pendentes,
        parametros=PARAMETROS_COBERTURA.get(cobertura),
        regras_verificadas=regras_ok,
        observacoes=obs,
    )
