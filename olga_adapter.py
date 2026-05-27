"""
olga_adapter.py — adapta respostas do harness para o schema da Olga.

Uso:
  python olga_adapter.py --from-file response_sinistro.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_INTENTS = {
    "fnol_triage",
    "document_collection",
    "document_decision",
    "hitl_escalation",
    "status_update",
}

ALLOWED_NEXT_ACTIONS = {
    "ask_more_info",
    "submit_fnol",
    "request_documents",
    "submit_documents",
    "escalate_human",
    "finalize",
}


def map_harness_to_olga(payload: dict[str, Any]) -> dict[str, Any]:
    # sinistro response
    if "proxima_acao" in payload and "mensagem_ao_segurado" in payload:
        proxima = payload.get("proxima_acao") or "solicitar_esclarecimento"
        next_action = "ask_more_info" if proxima == "solicitar_esclarecimento" else "finalize"
        intent = "fnol_triage"
        if proxima == "escalar_humano":
            intent = "hitl_escalation"
            next_action = "escalate_human"

        return {
            "intent": intent,
            "next_action": next_action,
            "message_to_user": payload.get("mensagem_ao_segurado", ""),
            "protocolo": payload.get("protocolo"),
            "decision_status": None,
            "needs_human_review": proxima == "escalar_humano",
            "missing_documents": [],
            "fraud_score": None,
            "alerta_operacional": payload.get("alerta_operacional"),
        }

    # documentos response
    if "decision_status" in payload and "needs_human_review" in payload:
        ds = payload.get("decision_status")
        if payload.get("needs_human_review"):
            intent = "hitl_escalation"
            next_action = "escalate_human"
        elif ds == "pending_documents":
            intent = "document_collection"
            next_action = "request_documents"
        else:
            intent = "document_decision"
            next_action = "finalize"

        return {
            "intent": intent,
            "next_action": next_action,
            "message_to_user": payload.get("recommended_next_action") or "Análise documental concluída.",
            "protocolo": payload.get("protocolo"),
            "decision_status": ds,
            "needs_human_review": payload.get("needs_human_review"),
            "missing_documents": payload.get("missing_documents", []),
            "fraud_score": payload.get("fraud_score"),
            "alerta_operacional": None,
        }

    raise ValueError("Payload não reconhecido para adaptação Olga")


def validate_olga_output(output: dict[str, Any]) -> None:
    required = ["intent", "next_action", "message_to_user"]
    for key in required:
        if key not in output:
            raise ValueError(f"Campo obrigatório ausente: {key}")

    if output["intent"] not in ALLOWED_INTENTS:
        raise ValueError(f"intent inválido: {output['intent']}")

    if output["next_action"] not in ALLOWED_NEXT_ACTIONS:
        raise ValueError(f"next_action inválido: {output['next_action']}")

    if not isinstance(output["message_to_user"], str) or not output["message_to_user"].strip():
        raise ValueError("message_to_user deve ser string não vazia")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Adapter de resposta para Olga schema")
    parser.add_argument("--from-file", required=True, help="Arquivo JSON de resposta do harness")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = json.loads(Path(args.from_file).read_text(encoding="utf-8"))
    out = map_harness_to_olga(payload)
    validate_olga_output(out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
