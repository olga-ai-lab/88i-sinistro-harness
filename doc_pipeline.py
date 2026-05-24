"""
doc_pipeline.py — Pipeline documental 3 etapas (Semana 4)

Orquestra as 3 skills instaladas em ~/.hermes/skills/insurance/:
  Etapa 1 — sinistro-doc-classifier   → classifica tipo do documento
  Etapa 2 — sinistro-doc-forensics    → extrai campos + perícia forense
  Etapa 3 — sinistro-claim-adjudicator → decisão final + fraud scoring

Cada etapa chama Claude com a skill como system prompt e parseia JSON.
Input:  lista de DocumentoInput (bytes ou texto + metadados do sinistro)
Output: AnaliseDocumental com classificação, extração, veredicto consolidado

Princípios:
  - Fail-closed: erro em qualquer etapa → needs_human_review=True
  - Cada etapa recebe output da anterior como contexto
  - Documentos processados em sequência; cross-validation na etapa 3
  - ZERO decisão de negócio aqui — isso é do rules_engine.py
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

import anthropic


# ============================================================
# Tipos de dados
# ============================================================

@dataclass
class DocumentoInput:
    """Um documento recebido do segurado."""
    nome: str                          # nome do arquivo (ex: "bo_campinas.pdf")
    conteudo: str                      # texto extraído OU descrição para mock
    mime_type: str = "text/plain"      # em produção: image/jpeg, application/pdf, etc.
    ordem: int = 0


@dataclass
class ResultadoClassificacao:
    document_type: str
    document_subtype: Optional[str] = None
    is_relevant: bool = True
    image_quality: str = "good"
    requires_human_review: bool = False
    target_fields: list[str] = field(default_factory=list)
    classification_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    notes: Optional[str] = None
    raw: Optional[dict] = None


@dataclass
class ResultadoForensics:
    document_type: str
    fields: dict = field(default_factory=dict)
    missing_required_fields: list[str] = field(default_factory=list)
    inconsistencies: list[str] = field(default_factory=list)
    authenticity_status: str = "indeterminate"   # plausible | suspicious | indeterminate
    plausibility_signals: list[str] = field(default_factory=list)
    tampering_signals: list[str] = field(default_factory=list)
    cross_document_issues: list[dict] = field(default_factory=list)
    needs_human_review: bool = False
    overall_confidence: float = 0.0
    extraction_notes: Optional[str] = None
    raw: Optional[dict] = None


@dataclass
class ResultadoAdjudicator:
    decision_status: str               # approved_for_next_step | pending_documents |
                                       # pending_manual_review | fraud_escalation | rejected_documentally
    product: Optional[str] = None
    coverage: Optional[str] = None
    fraud_score: int = 0
    fraud_level: str = "low"           # low | medium | high
    missing_documents: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    recommended_next_action: Optional[str] = None
    human_review_required: bool = False
    decision_confidence: float = 0.0
    raw: Optional[dict] = None


@dataclass
class AnaliseDocumento:
    """Resultado completo de um único documento."""
    documento: DocumentoInput
    classificacao: Optional[ResultadoClassificacao] = None
    forensics: Optional[ResultadoForensics] = None
    erro: Optional[str] = None


@dataclass
class AnaliseDocumental:
    """Resultado consolidado de todos os documentos + veredicto final."""
    documentos: list[AnaliseDocumento] = field(default_factory=list)
    veredicto: Optional[ResultadoAdjudicator] = None
    needs_human_review: bool = False
    resumo_fraude: Optional[str] = None
    erro: Optional[str] = None


# ============================================================
# Carregamento das skills
# ============================================================

SKILLS_DIR = Path.home() / ".hermes" / "skills" / "insurance"

def _load_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# Skill {name}\nConteúdo não encontrado em {path}"


def _load_reference(skill_name: str, ref_file: str) -> str:
    path = SKILLS_DIR / skill_name / "references" / ref_file
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


# Carrega skills uma vez em módulo-load (não por chamada)
_SKILL_CLASSIFIER  = _load_skill("sinistro-doc-classifier")
_SKILL_FORENSICS   = _load_skill("sinistro-doc-forensics")
_SKILL_ADJUDICATOR = _load_skill("sinistro-claim-adjudicator")

# References do forensics
_REF_EXTRACTION    = _load_reference("sinistro-doc-forensics", "extraction_fields.md")
_REF_FORENSIC_SIG  = _load_reference("sinistro-doc-forensics", "forensic_signals.md")
_REF_CROSS_VAL     = _load_reference("sinistro-doc-forensics", "cross_validation_rules.md")
_REF_FRAUD_MATRIX  = _load_reference("sinistro-doc-forensics", "fraud_scoring_matrix.md")


# ============================================================
# Cliente Anthropic
# ============================================================

def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _call_claude(system: str, user: str, max_tokens: int = 2048) -> str:
    """Chama Claude e retorna o texto da resposta."""
    client = _get_client()
    resp = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text


def _parse_json(text: str) -> Optional[dict]:
    """Extrai JSON da resposta — tolerante a markdown code blocks."""
    # tenta extrair bloco ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    # tenta o texto todo
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # fallback: encontra o primeiro { ... } balanceado
        depth = 0
        start = text.find("{")
        if start == -1:
            return None
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        return None
        return None


# ============================================================
# Etapa 1 — Classificador
# ============================================================

def _classificar(doc: DocumentoInput) -> ResultadoClassificacao:
    system = _SKILL_CLASSIFIER
    user = (
        f"Classifique o seguinte documento recebido num sinistro 88i.\n\n"
        f"Nome do arquivo: {doc.nome}\n"
        f"Tipo MIME: {doc.mime_type}\n\n"
        f"Conteúdo / descrição:\n---\n{doc.conteudo}\n---\n\n"
        f"Responda APENAS em JSON válido conforme o formato da skill."
    )
    raw_text = _call_claude(system, user, max_tokens=1024)
    data = _parse_json(raw_text)
    if not data:
        return ResultadoClassificacao(
            document_type="image_unreadable",
            requires_human_review=True,
            notes=f"Falha ao parsear resposta: {raw_text[:200]}",
        )
    return ResultadoClassificacao(
        document_type=data.get("document_type", "image_unreadable"),
        document_subtype=data.get("document_subtype"),
        is_relevant=data.get("is_relevant", True),
        image_quality=data.get("image_quality", "acceptable"),
        requires_human_review=data.get("requires_human_review", False),
        target_fields=data.get("target_fields", []),
        classification_evidence=data.get("classification_evidence", []),
        confidence=data.get("confidence", 0.0),
        notes=data.get("notes"),
        raw=data,
    )


# ============================================================
# Etapa 2 — Forensics
# ============================================================

def _analisar_forensics(
    doc: DocumentoInput,
    classificacao: ResultadoClassificacao,
    outros_docs_context: str = "",
) -> ResultadoForensics:
    system = "\n\n---\n\n".join([
        _SKILL_FORENSICS,
        f"## Campos de Extração de Referência\n{_REF_EXTRACTION}",
        f"## Sinais Forenses\n{_REF_FORENSIC_SIG}",
        f"## Regras de Cross-Validation\n{_REF_CROSS_VAL}",
    ])
    user_parts = [
        f"Analise o documento abaixo. Tipo já classificado: **{classificacao.document_type}**",
        f"Nome do arquivo: {doc.nome}",
        f"Campos-alvo: {', '.join(classificacao.target_fields) or 'conforme taxonomia'}",
        f"\nConteúdo / descrição:\n---\n{doc.conteudo}\n---",
    ]
    if outros_docs_context:
        user_parts.append(f"\nContexto de outros documentos já analisados:\n{outros_docs_context}")
    user_parts.append("\nResponda APENAS em JSON válido conforme o formato da skill.")

    raw_text = _call_claude(system, "\n".join(user_parts), max_tokens=2048)
    data = _parse_json(raw_text)
    if not data:
        return ResultadoForensics(
            document_type=classificacao.document_type,
            authenticity_status="indeterminate",
            needs_human_review=True,
            extraction_notes=f"Falha ao parsear resposta: {raw_text[:200]}",
        )

    # Normaliza fields: aceita list[{field, value, confidence}] ou dict
    fields_raw = data.get("fields", {})
    if isinstance(fields_raw, list):
        fields_dict = {item.get("field", f"field_{i}"): item for i, item in enumerate(fields_raw)}
    else:
        fields_dict = fields_raw

    return ResultadoForensics(
        document_type=data.get("document_type", classificacao.document_type),
        fields=fields_dict,
        missing_required_fields=data.get("missing_required_fields", []),
        inconsistencies=data.get("inconsistencies", []),
        authenticity_status=data.get("authenticity_status", "indeterminate"),
        plausibility_signals=data.get("plausibility_signals", []),
        tampering_signals=data.get("tampering_signals", []),
        cross_document_issues=data.get("cross_document_issues", []),
        needs_human_review=data.get("needs_human_review", False),
        overall_confidence=data.get("overall_confidence", 0.0),
        extraction_notes=data.get("extraction_notes"),
        raw=data,
    )


# ============================================================
# Etapa 3 — Adjudicator
# ============================================================

def _adjudicar(
    analises: list[AnaliseDocumento],
    contexto_sinistro: str,
) -> ResultadoAdjudicator:
    system = "\n\n---\n\n".join([
        _SKILL_ADJUDICATOR,
        f"## Matriz de Fraude\n{_REF_FRAUD_MATRIX}",
    ])

    # Monta resumo de cada documento para o adjudicator
    docs_summary = []
    for a in analises:
        if a.erro:
            docs_summary.append(f"- {a.documento.nome}: ERRO — {a.erro}")
            continue
        clf = a.classificacao
        fns = a.forensics
        summary = f"- {a.documento.nome} [{clf.document_type if clf else '?'}]"
        if fns:
            summary += (
                f"\n  autenticidade={fns.authenticity_status}"
                f" | confiança={fns.overall_confidence:.2f}"
                f" | campos_faltantes={fns.missing_required_fields}"
                f" | sinais_adulteração={fns.tampering_signals}"
            )
            if fns.cross_document_issues:
                summary += f"\n  divergências_cross_doc={fns.cross_document_issues}"
        docs_summary.append(summary)

    user = (
        f"## Contexto do Sinistro\n{contexto_sinistro}\n\n"
        f"## Documentos Analisados\n" + "\n".join(docs_summary) + "\n\n"
        f"Execute as 7 fases do procedimento obrigatório e retorne a decisão final "
        f"em JSON válido conforme o formato da skill."
    )

    raw_text = _call_claude(system, user, max_tokens=4096)
    data = _parse_json(raw_text)
    if not data:
        return ResultadoAdjudicator(
            decision_status="pending_manual_review",
            human_review_required=True,
            key_findings=[f"Falha ao parsear resposta do adjudicator: {raw_text[:200]}"],
        )

    fraud = data.get("fraud_scoring", {})
    fraud_total = fraud.get("total_score", 0) if isinstance(fraud, dict) else 0
    fraud_level = "low"
    if fraud_total >= 10:
        fraud_level = "critical"
    elif fraud_total >= 6:
        fraud_level = "high"
    elif fraud_total >= 1:
        fraud_level = "medium"

    return ResultadoAdjudicator(
        decision_status=data.get("decision_status", "pending_manual_review"),
        product=data.get("product"),
        coverage=data.get("coverage"),
        fraud_score=fraud_total,
        fraud_level=fraud_level,
        missing_documents=data.get("missing_documents", []),
        key_findings=data.get("key_findings", []),
        recommended_next_action=data.get("recommended_next_action"),
        human_review_required=data.get("human_review_required", False),
        decision_confidence=data.get("decision_confidence", 0.0),
        raw=data,
    )


# ============================================================
# Pipeline público
# ============================================================

def analisar_documentos(
    documentos: list[DocumentoInput],
    contexto_sinistro: str = "",
) -> AnaliseDocumental:
    """
    Executa o pipeline completo nos documentos recebidos.

    Args:
        documentos: lista de DocumentoInput com conteúdo dos arquivos
        contexto_sinistro: string com tipo_sinistro, cobertura, narrativa — contexto
                          para o adjudicator tomar a decisão correta

    Returns:
        AnaliseDocumental com resultado por documento + veredicto final
    """
    if not documentos:
        return AnaliseDocumental(
            needs_human_review=True,
            erro="Nenhum documento recebido",
        )

    analises: list[AnaliseDocumento] = []
    contexto_acumulado_parts: list[str] = []

    # Etapas 1 e 2 — por documento
    for doc in documentos:
        analise = AnaliseDocumento(documento=doc)
        try:
            # Etapa 1: classificação
            clf = _classificar(doc)
            analise.classificacao = clf

            # Documentos irrelevantes ou ilegíveis não passam pela forensics
            if clf.document_type in ("image_unreadable", "irrelevant_document"):
                analises.append(analise)
                continue

            # Etapa 2: forensics com contexto acumulado
            ctx = "\n".join(contexto_acumulado_parts) if contexto_acumulado_parts else ""
            fns = _analisar_forensics(doc, clf, outros_docs_context=ctx)
            analise.forensics = fns

            # Adiciona ao contexto acumulado para próximos documentos
            contexto_acumulado_parts.append(
                f"Documento: {doc.nome} | Tipo: {clf.document_type} | "
                f"Autenticidade: {fns.authenticity_status} | "
                f"Campos extraídos: {list(fns.fields.keys())}"
            )

        except Exception as e:
            analise.erro = str(e)

        analises.append(analise)

    # Etapa 3: adjudicator com todos os resultados
    needs_review = any(
        (a.classificacao and a.classificacao.requires_human_review)
        or (a.forensics and a.forensics.needs_human_review)
        or a.erro
        for a in analises
    )

    try:
        veredicto = _adjudicar(analises, contexto_sinistro)
    except Exception as e:
        veredicto = ResultadoAdjudicator(
            decision_status="pending_manual_review",
            human_review_required=True,
            key_findings=[f"Erro no adjudicator: {e}"],
        )
        needs_review = True

    # Resumo de fraude
    resumo = None
    if veredicto.fraud_score > 0:
        resumo = (
            f"Fraud score: {veredicto.fraud_score} ({veredicto.fraud_level}) | "
            f"Achados: {'; '.join(veredicto.key_findings[:3])}"
        )

    return AnaliseDocumental(
        documentos=analises,
        veredicto=veredicto,
        needs_human_review=needs_review or veredicto.human_review_required,
        resumo_fraude=resumo,
    )
