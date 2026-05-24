"""
tools.py — Tools do agente 88i (Semana 2)

Cada tool é uma função Python pura com interface real e stub de dados.
Em produção: trocar os stubs por chamadas ao Supabase/PostgreSQL.

Princípio: tools retornam dicts tipados — nunca strings cruas.
O nó `no_consultar_contexto` em agent.py chama as tools e injeta
os resultados no SinistroState antes do roteamento.

NÃO usar LLM dentro de nenhuma tool — esse código é determinístico.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field


# ============================================================
# Tipos de retorno (Pydantic-free — usamos dataclasses simples)
# ============================================================

@dataclass
class DadosApolice:
    encontrada: bool
    segurado_id: str
    produto: Optional[str] = None          # ex: "DITA", "BAGAGEM", "IPA"
    coberturas: list[str] = field(default_factory=list)
    vigencia_inicio: Optional[date] = None
    vigencia_fim: Optional[date] = None
    vigente_hoje: bool = False
    carencia_ativa: bool = False           # se ainda em carência
    observacao: Optional[str] = None


@dataclass
class HistoricoSinistros:
    encontrado: bool
    segurado_id: str
    total_sinistros: int = 0
    sinistros_12_meses: int = 0
    ultimo_sinistro_data: Optional[date] = None
    sinistros_mesmo_tipo: int = 0          # mesmo tipo_sinistro que o atual
    alerta_frequencia: bool = False        # True se >= 3 em 12 meses
    observacao: Optional[str] = None


@dataclass
class RegistroSinistro:
    sucesso: bool
    protocolo: Optional[str] = None       # ex: "88i-2026-000123"
    sinistro_id: Optional[str] = None     # UUID
    timestamp_registro: Optional[str] = None
    erro: Optional[str] = None


# ============================================================
# Helpers de conexão (substituir por Supabase em produção)
# ============================================================

def _get_supabase_client():
    """
    Em produção: retorna supabase.create_client(url, key).
    Por enquanto retorna None — as tools operam em stub mode.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if url and key:
        try:
            from supabase import create_client  # type: ignore
            return create_client(url, key)
        except ImportError:
            pass
    return None


def _stub_mode() -> bool:
    """True se Supabase não está configurado — usa dados sintéticos."""
    return not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))


# ============================================================
# STUB DATA — dados sintéticos para desenvolvimento local
# Estrutura espelha o schema real do Supabase (supabase_schema.sql)
# ============================================================

_APOLICES_STUB: dict[str, dict] = {
    "SEG-001": {
        "produto": "DITA",
        "coberturas": ["DITA", "DMHO"],
        "vigencia_inicio": date(2025, 1, 1),
        "vigencia_fim": date(2026, 12, 31),
        "carencia_ativa": False,
    },
    "SEG-002": {
        "produto": "BAGAGEM",
        "coberturas": ["BAGAGEM"],
        "vigencia_inicio": date(2026, 3, 1),
        "vigencia_fim": date(2027, 2, 28),
        "carencia_ativa": True,
    },
    "SEG-003": {
        "produto": "IPA",
        "coberturas": ["IPA", "MA", "AF"],
        "vigencia_inicio": date(2024, 6, 1),
        "vigencia_fim": date(2025, 5, 31),  # vencida
        "carencia_ativa": False,
    },
}

_HISTORICO_STUB: dict[str, dict] = {
    "SEG-001": {
        "total": 2,
        "em_12_meses": 1,
        "ultimo": date(2025, 11, 10),
        "mesmo_tipo": 1,
    },
    "SEG-002": {
        "total": 5,
        "em_12_meses": 3,  # dispara alerta_frequencia
        "ultimo": date(2026, 4, 1),
        "mesmo_tipo": 2,
    },
    "SEG-003": {
        "total": 0,
        "em_12_meses": 0,
        "ultimo": None,
        "mesmo_tipo": 0,
    },
}


# ============================================================
# Tool 1: consultar_apolice
# ============================================================

def consultar_apolice(segurado_id: str) -> DadosApolice:
    """
    Busca dados da apólice ativa do segurado.

    Em produção: SELECT * FROM apolices WHERE segurado_id = %s AND status = 'ativa'
    Retorna DadosApolice com vigencia e coberturas.

    Fail-safe: se Supabase cair ou segurado não encontrado, retorna
    DadosApolice(encontrada=False) — o agente continua sem travar.
    """
    if not segurado_id:
        return DadosApolice(encontrada=False, segurado_id="", observacao="segurado_id vazio")

    # --- Produção ---
    if not _stub_mode():
        try:
            sb = _get_supabase_client()
            resp = (
                sb.table("apolices")
                .select("produto, coberturas, vigencia_inicio, vigencia_fim, carencia_ativa")
                .eq("segurado_id", segurado_id)
                .eq("status", "ativa")
                .single()
                .execute()
            )
            if not resp.data:
                return DadosApolice(encontrada=False, segurado_id=segurado_id,
                                    observacao="apólice não encontrada")
            d = resp.data
            vi = date.fromisoformat(d["vigencia_inicio"]) if d.get("vigencia_inicio") else None
            vf = date.fromisoformat(d["vigencia_fim"]) if d.get("vigencia_fim") else None
            hoje = date.today()
            vigente = bool(vi and vf and vi <= hoje <= vf)
            return DadosApolice(
                encontrada=True,
                segurado_id=segurado_id,
                produto=d.get("produto"),
                coberturas=d.get("coberturas") or [],
                vigencia_inicio=vi,
                vigencia_fim=vf,
                vigente_hoje=vigente,
                carencia_ativa=bool(d.get("carencia_ativa", False)),
            )
        except Exception as e:
            return DadosApolice(encontrada=False, segurado_id=segurado_id,
                                observacao=f"erro Supabase: {e}")

    # --- Stub ---
    dados = _APOLICES_STUB.get(segurado_id)
    if not dados:
        return DadosApolice(encontrada=False, segurado_id=segurado_id,
                            observacao="segurado não encontrado no stub")
    hoje = date.today()
    vi = dados["vigencia_inicio"]
    vf = dados["vigencia_fim"]
    return DadosApolice(
        encontrada=True,
        segurado_id=segurado_id,
        produto=dados["produto"],
        coberturas=dados["coberturas"],
        vigencia_inicio=vi,
        vigencia_fim=vf,
        vigente_hoje=(vi <= hoje <= vf),
        carencia_ativa=dados["carencia_ativa"],
        observacao="[STUB]",
    )


# ============================================================
# Tool 2: buscar_historico_sinistros
# ============================================================

def buscar_historico_sinistros(
    segurado_id: str,
    tipo_sinistro: Optional[str] = None,
) -> HistoricoSinistros:
    """
    Busca histórico de sinistros do segurado.

    Em produção: SELECT + COUNT agrupando por período e tipo.
    `tipo_sinistro` é opcional — se passado, conta os do mesmo tipo.

    Alerta de frequência: >= 3 sinistros nos últimos 12 meses.
    (Regra 88i — sinal de fraude de frequência.)
    """
    if not segurado_id:
        return HistoricoSinistros(encontrado=False, segurado_id="",
                                  observacao="segurado_id vazio")

    # --- Produção ---
    if not _stub_mode():
        try:
            sb = _get_supabase_client()
            # total geral
            resp_total = (
                sb.table("sinistros")
                .select("id, tipo_sinistro, data_ocorrencia", count="exact")
                .eq("segurado_id", segurado_id)
                .execute()
            )
            total = resp_total.count or 0

            # últimos 12 meses
            doze_meses_atras = datetime.now().replace(
                year=datetime.now().year - 1
            ).isoformat()
            resp_12 = (
                sb.table("sinistros")
                .select("id", count="exact")
                .eq("segurado_id", segurado_id)
                .gte("created_at", doze_meses_atras)
                .execute()
            )
            em_12 = resp_12.count or 0

            # mesmo tipo
            mesmo_tipo = 0
            if tipo_sinistro:
                resp_tipo = (
                    sb.table("sinistros")
                    .select("id", count="exact")
                    .eq("segurado_id", segurado_id)
                    .eq("tipo_sinistro", tipo_sinistro)
                    .execute()
                )
                mesmo_tipo = resp_tipo.count or 0

            # último sinistro
            resp_ultimo = (
                sb.table("sinistros")
                .select("data_ocorrencia")
                .eq("segurado_id", segurado_id)
                .order("data_ocorrencia", desc=True)
                .limit(1)
                .execute()
            )
            ultimo = None
            if resp_ultimo.data:
                ultimo = date.fromisoformat(resp_ultimo.data[0]["data_ocorrencia"])

            return HistoricoSinistros(
                encontrado=True,
                segurado_id=segurado_id,
                total_sinistros=total,
                sinistros_12_meses=em_12,
                ultimo_sinistro_data=ultimo,
                sinistros_mesmo_tipo=mesmo_tipo,
                alerta_frequencia=(em_12 >= 3),
            )
        except Exception as e:
            return HistoricoSinistros(encontrado=False, segurado_id=segurado_id,
                                      observacao=f"erro Supabase: {e}")

    # --- Stub ---
    dados = _HISTORICO_STUB.get(segurado_id)
    if not dados:
        return HistoricoSinistros(encontrado=False, segurado_id=segurado_id,
                                  observacao="segurado não encontrado no stub")
    return HistoricoSinistros(
        encontrado=True,
        segurado_id=segurado_id,
        total_sinistros=dados["total"],
        sinistros_12_meses=dados["em_12_meses"],
        ultimo_sinistro_data=dados["ultimo"],
        sinistros_mesmo_tipo=dados["mesmo_tipo"],
        alerta_frequencia=(dados["em_12_meses"] >= 3),
        observacao="[STUB]",
    )


# ============================================================
# Tool 3: registrar_sinistro
# ============================================================

def registrar_sinistro(
    segurado_id: Optional[str],
    narrativa_original: str,
    tipo_sinistro: str,
    proxima_acao: str,
    extracao_json: str,
    timestamp_recebimento: str,
) -> RegistroSinistro:
    """
    Grava o sinistro em `sinistros` (Supabase) e retorna protocolo.

    Em produção: INSERT INTO sinistros (...) RETURNING id, protocolo
    Em stub: gera protocolo sintético localmente.

    Idempotência: em produção usar upsert por (segurado_id, timestamp_recebimento)
    para garantir retry-safe (princípio Inngest).
    """
    sinistro_id = str(uuid.uuid4())
    ano = datetime.now().year
    # Protocolo humano: 88i-YYYY-XXXXXXXX
    protocolo = f"88i-{ano}-{sinistro_id[:8].upper()}"

    if not _stub_mode():
        try:
            sb = _get_supabase_client()
            resp = (
                sb.table("sinistros")
                .insert({
                    "id": sinistro_id,
                    "protocolo": protocolo,
                    "segurado_id": segurado_id,
                    "narrativa_original": narrativa_original,
                    "tipo_sinistro": tipo_sinistro,
                    "proxima_acao": proxima_acao,
                    "extracao_json": extracao_json,
                    "timestamp_recebimento": timestamp_recebimento,
                    "status": "aberto",
                })
                .execute()
            )
            if resp.data:
                return RegistroSinistro(
                    sucesso=True,
                    protocolo=protocolo,
                    sinistro_id=sinistro_id,
                    timestamp_registro=datetime.now().isoformat(),
                )
            return RegistroSinistro(sucesso=False, erro="insert sem retorno de dados")
        except Exception as e:
            return RegistroSinistro(sucesso=False, erro=f"erro Supabase: {e}")

    # --- Stub: simula registro local ---
    return RegistroSinistro(
        sucesso=True,
        protocolo=protocolo,
        sinistro_id=sinistro_id,
        timestamp_registro=datetime.now().isoformat(),
    )
