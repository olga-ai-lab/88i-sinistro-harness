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

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import processar_narrativa
from tools import _stub_mode
from doc_pipeline import analisar_documentos, DocumentoInput, AnaliseDocumental
from hitl_queue import (
    listar_tarefas, obter_tarefa, resolver_tarefa, resumo_fila,
    TarefaStatus, DecisaoHumana, TarefaHITL, ResultadoResolucao,
)


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


class DocumentoAnaliseResponse(BaseModel):
    protocolo: str
    total_documentos: int
    decision_status: str
    fraud_score: int
    fraud_level: str
    needs_human_review: bool
    missing_documents: list[str]
    key_findings: list[str]
    recommended_next_action: Optional[str] = None
    resumo_fraude: Optional[str] = None
    documentos_processados: list[dict]
    timestamp: str


class HITLTarefaResponse(BaseModel):
    id: str
    protocolo: str
    segurado_id: Optional[str]
    motivo: str
    prioridade: str
    status: str
    criada_em: str
    tipo_sinistro: Optional[str]
    plataforma: Optional[str]
    cobertura: Optional[str]
    red_flags: list[dict]
    alerta_operacional: Optional[str]
    fraud_score: int
    fraud_findings: list[str]
    veredicto_cobertura_status: Optional[str]
    veredicto_motivo_recusa: Optional[str]
    narrativa_original: str
    resolvida_em: Optional[str] = None
    analista: Optional[str] = None
    decisao: Optional[str] = None
    justificativa: Optional[str] = None
    docs_solicitados: list[str] = []


class HITLResolverRequest(BaseModel):
    decisao: str = Field(
        ...,
        description="aprovar | recusar | solicitar_docs | escalar_juridico",
    )
    analista: str = Field(..., description="Nome ou ID da analista (ex: 'Rosi')")
    justificativa: str = Field(default="", description="Justificativa da decisão")
    docs_solicitados: list[str] = Field(
        default=[],
        description="Lista de documentos a solicitar (quando decisao=solicitar_docs)",
    )


class HITLFilaResponse(BaseModel):
    total: int
    pendentes: int
    em_revisao: int
    resolvidas: int
    por_prioridade: dict
    tarefas: list[HITLTarefaResponse]


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


@app.post("/sinistro/{protocolo}/documentos",
          response_model=DocumentoAnaliseResponse,
          tags=["sinistro"])
async def receber_documentos(
    protocolo: str,
    tipo_sinistro: str = "DITA",
    cobertura: str = "B_DITA",
    narrativa_resumo: str = "",
    arquivos: list[UploadFile] = File(...),
):
    """
    Recebe documentos de um sinistro já registrado e executa o pipeline documental:
    1. Classifier  — identifica tipo de cada documento
    2. Forensics   — extrai campos + pericia forense (sinais de adulteração)
    3. Adjudicator — decisão final + fraud scoring (5 categorias)

    Aceita múltiplos arquivos via multipart/form-data.
    Em produção: buscar contexto do sinistro no Supabase via protocolo.
    """
    if not arquivos:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

    # Lê conteúdo dos arquivos
    docs: list[DocumentoInput] = []
    for i, arq in enumerate(arquivos):
        try:
            conteudo_bytes = await arq.read()
            # Tenta decodificar como texto; senão usa representação base64 resumida
            try:
                conteudo = conteudo_bytes.decode("utf-8")
            except UnicodeDecodeError:
                conteudo = f"[Arquivo binário: {len(conteudo_bytes)} bytes — {arq.content_type}]"
            docs.append(DocumentoInput(
                nome=arq.filename or f"doc_{i+1}",
                conteudo=conteudo,
                mime_type=arq.content_type or "application/octet-stream",
                ordem=i,
            ))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo {arq.filename}: {e}")

    contexto = (
        f"Protocolo: {protocolo}\n"
        f"Tipo de sinistro: {tipo_sinistro}\n"
        f"Cobertura solicitada: {cobertura}\n"
        f"Narrativa resumida: {narrativa_resumo or 'não informada'}\n"
        f"Plataforma: UBER\n"
    )

    try:
        analise: AnaliseDocumental = analisar_documentos(docs, contexto_sinistro=contexto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline documental: {e}")

    veredicto = analise.veredicto
    docs_processados = []
    for a in analise.documentos:
        item = {
            "nome": a.documento.nome,
            "tipo": a.classificacao.document_type if a.classificacao else "erro",
            "confianca_classificacao": a.classificacao.confidence if a.classificacao else 0.0,
            "autenticidade": a.forensics.authenticity_status if a.forensics else "indeterminate",
            "sinais_adulteracao": a.forensics.tampering_signals if a.forensics else [],
            "campos_faltantes": a.forensics.missing_required_fields if a.forensics else [],
        }
        if a.erro:
            item["erro"] = a.erro
        docs_processados.append(item)

    return DocumentoAnaliseResponse(
        protocolo=protocolo,
        total_documentos=len(docs),
        decision_status=veredicto.decision_status if veredicto else "pending_manual_review",
        fraud_score=veredicto.fraud_score if veredicto else 0,
        fraud_level=veredicto.fraud_level if veredicto else "unknown",
        needs_human_review=analise.needs_human_review,
        missing_documents=veredicto.missing_documents if veredicto else [],
        key_findings=veredicto.key_findings if veredicto else [],
        recommended_next_action=veredicto.recommended_next_action if veredicto else None,
        resumo_fraude=analise.resumo_fraude,
        documentos_processados=docs_processados,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/hitl/fila", response_model=HITLFilaResponse, tags=["hitl"])
async def hitl_fila(
    status: str = TarefaStatus.PENDENTE,
    limit: int = 50,
):
    """
    Lista a fila de revisão humana para a Rosi.
    Ordenada por prioridade (critica → alta → media → baixa) e data.

    status: pendente | em_revisao | resolvida (default: pendente)
    """
    resumo = resumo_fila()
    tarefas = listar_tarefas(status=status, limit=limit)

    def _tarefa_to_resp(t: TarefaHITL) -> HITLTarefaResponse:
        return HITLTarefaResponse(
            id=t.id,
            protocolo=t.protocolo,
            segurado_id=t.segurado_id,
            motivo=t.motivo,
            prioridade=t.prioridade,
            status=t.status,
            criada_em=t.criada_em,
            tipo_sinistro=t.tipo_sinistro,
            plataforma=t.plataforma,
            cobertura=t.cobertura,
            red_flags=t.red_flags,
            alerta_operacional=t.alerta_operacional,
            fraud_score=t.fraud_score,
            fraud_findings=t.fraud_findings,
            veredicto_cobertura_status=t.veredicto_cobertura_status,
            veredicto_motivo_recusa=t.veredicto_motivo_recusa,
            narrativa_original=t.narrativa_original,
            resolvida_em=t.resolvida_em,
            analista=t.analista,
            decisao=t.decisao,
            justificativa=t.justificativa,
            docs_solicitados=t.docs_solicitados,
        )

    return HITLFilaResponse(
        total=resumo["total"],
        pendentes=resumo["pendentes"],
        em_revisao=resumo["em_revisao"],
        resolvidas=resumo["resolvidas"],
        por_prioridade=resumo["por_prioridade"],
        tarefas=[_tarefa_to_resp(t) for t in tarefas],
    )


@app.get("/hitl/tarefa/{tarefa_id}", response_model=HITLTarefaResponse, tags=["hitl"])
async def hitl_tarefa_detalhe(tarefa_id: str):
    """
    Retorna o detalhe completo de uma tarefa — narrativa, red flags,
    fraud findings, veredicto de cobertura — tudo que a Rosi precisa
    para tomar a decisão.
    """
    tarefa = obter_tarefa(tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail=f"Tarefa {tarefa_id} não encontrada")
    return HITLTarefaResponse(
        id=tarefa.id,
        protocolo=tarefa.protocolo,
        segurado_id=tarefa.segurado_id,
        motivo=tarefa.motivo,
        prioridade=tarefa.prioridade,
        status=tarefa.status,
        criada_em=tarefa.criada_em,
        tipo_sinistro=tarefa.tipo_sinistro,
        plataforma=tarefa.plataforma,
        cobertura=tarefa.cobertura,
        red_flags=tarefa.red_flags,
        alerta_operacional=tarefa.alerta_operacional,
        fraud_score=tarefa.fraud_score,
        fraud_findings=tarefa.fraud_findings,
        veredicto_cobertura_status=tarefa.veredicto_cobertura_status,
        veredicto_motivo_recusa=tarefa.veredicto_motivo_recusa,
        narrativa_original=tarefa.narrativa_original,
        resolvida_em=tarefa.resolvida_em,
        analista=tarefa.analista,
        decisao=tarefa.decisao,
        justificativa=tarefa.justificativa,
        docs_solicitados=tarefa.docs_solicitados,
    )


@app.post("/hitl/tarefa/{tarefa_id}/resolver", tags=["hitl"])
async def hitl_resolver(tarefa_id: str, req: HITLResolverRequest):
    """
    Rosi submete sua decisão sobre uma tarefa.

    decisao:
      - aprovar          → sinistro aprovado, mensagem positiva ao segurado
      - recusar          → sinistro recusado com justificativa
      - solicitar_docs   → solicita documentos adicionais (informar docs_solicitados)
      - escalar_juridico → encaminha para equipe jurídica

    Registra: analista, decisao, justificativa, timestamp.
    Retorna mensagem pronta para enviar ao segurado via WhatsApp.
    """
    decisoes_validas = {
        DecisaoHumana.APROVAR,
        DecisaoHumana.RECUSAR,
        DecisaoHumana.SOLICITAR_DOCS,
        DecisaoHumana.ESCALAR_JURIDICO,
    }
    if req.decisao not in decisoes_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Decisão inválida: {req.decisao}. Valores aceitos: {decisoes_validas}",
        )

    resultado = resolver_tarefa(
        tarefa_id=tarefa_id,
        decisao=req.decisao,
        analista=req.analista,
        justificativa=req.justificativa,
        docs_solicitados=req.docs_solicitados,
    )

    if not resultado.sucesso:
        raise HTTPException(status_code=400, detail=resultado.erro)

    return {
        "sucesso": True,
        "tarefa_id": tarefa_id,
        "decisao": resultado.decisao,
        "analista": req.analista,
        "mensagem_ao_segurado": resultado.mensagem_ao_segurado,
        "timestamp": datetime.now().isoformat(),
    }


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
