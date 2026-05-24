"""
main.py — FastAPI HTTP server (Semana 2)

Endpoints:
  POST /sinistro   — recebe narrativa e dispara o agente LangGraph
  GET  /health     — healthcheck para Railway / uptime monitors

Em produção: o Supabase Edge Function (webhook Evolution API) chama
este endpoint via Inngest event, não diretamente. O binding Inngest
fica em inngest_functions.py.

Rodar local:
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import processar_narrativa
from tools import _stub_mode


# ============================================================
# App
# ============================================================

app = FastAPI(
    title="88i Sinistro Agent",
    description="Agente de ingestão de sinistros FNOL — 88i Seguradora Digital",
    version="0.2.0",  # Semana 2
)


# ============================================================
# Schemas de request/response
# ============================================================

class SinistroRequest(BaseModel):
    narrativa: str = Field(
        ...,
        min_length=5,
        max_length=10_000,
        description="Narrativa livre do segurado descrevendo o sinistro",
        examples=["Bati minha moto ontem na Paulista, perna quebrada, tenho BO e atestado."],
    )
    segurado_id: Optional[str] = Field(
        None,
        description="ID do segurado no sistema 88i (opcional — enriquece o contexto)",
        examples=["SEG-001"],
    )


class SinistroResponse(BaseModel):
    proxima_acao: str
    mensagem_ao_segurado: str
    protocolo: Optional[str] = None
    tipo_sinistro: Optional[str] = None
    confianca: Optional[float] = None
    red_flags_count: int = 0
    alerta_operacional: Optional[str] = None
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    version: str
    stub_mode: bool
    timestamp: str


# ============================================================
# Endpoints
# ============================================================

@app.get("/health", response_model=HealthResponse, tags=["infra"])
async def health():
    """
    Healthcheck para Railway, Render, ou qualquer uptime monitor.
    Retorna 200 se o servidor está rodando.
    `stub_mode: true` indica que Supabase não está configurado.
    """
    return HealthResponse(
        status="ok",
        version="0.2.0",
        stub_mode=_stub_mode(),
        timestamp=datetime.now().isoformat(),
    )


@app.post("/sinistro", response_model=SinistroResponse, tags=["sinistro"])
async def receber_sinistro(req: SinistroRequest):
    """
    Recebe narrativa livre de um segurado e executa o pipeline completo:
    1. Extrai dados estruturados via BAML/Claude
    2. Consulta apólice e histórico (tools)
    3. Decide rota deterministicamente
    4. Registra sinistro (stub Supabase) e retorna protocolo

    Em produção: chamado pelo Inngest event `sinistro/fnol.received`.
    """
    try:
        resultado = processar_narrativa(
            narrativa=req.narrativa.strip(),
            segurado_id=req.segurado_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline: {e}")

    extracao = resultado.get("extracao")

    return SinistroResponse(
        proxima_acao=resultado.get("proxima_acao", "escalar_humano"),
        mensagem_ao_segurado=resultado.get("mensagem_ao_segurado", ""),
        protocolo=resultado.get("protocolo"),
        tipo_sinistro=extracao.tipo_sinistro.value if extracao and hasattr(extracao.tipo_sinistro, "value") else None,
        confianca=extracao.confianca if extracao else None,
        red_flags_count=len(extracao.red_flags) if extracao else 0,
        alerta_operacional=resultado.get("alerta_operacional"),
        timestamp=datetime.now().isoformat(),
    )


# ============================================================
# Handler de erros não tratados
# ============================================================

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Erro interno: {exc}", "path": str(request.url)},
    )


# ============================================================
# Entrypoint local
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
