# Olga ↔ 88i Harness — Contratos HTTP

## Base URL

- Produção: `https://88i-sinistro-harness.railway.app`

## 1) Healthcheck

### Request

`GET /health`

### Response esperada

- `200 OK`
- JSON com `status=ok`.

---

## 2) Triagem FNOL

### Request

`POST /sinistro`

```json
{
  "narrativa": "Bati minha moto ontem na Paulista, fraturei a perna.",
  "segurado_id": "SEG-001"
}
```

### Response (campos principais)

```json
{
  "proxima_acao": "solicitar_esclarecimento",
  "mensagem_ao_segurado": "...",
  "protocolo": "88i-2026-00000001",
  "tipo_sinistro": "DITA",
  "confianca": 0.86,
  "red_flags_count": 1,
  "alerta_operacional": null,
  "timestamp": "2026-05-26T12:00:00"
}
```

---

## 3) Pipeline documental

### Request

`POST /sinistro/{protocolo}/documentos`

- Content-Type: `multipart/form-data`
- Campo de arquivos: `arquivos` (múltiplos)

### Response (campos principais)

```json
{
  "protocolo": "88i-2026-00000001",
  "decision_status": "pending_manual_review",
  "fraud_score": 47,
  "fraud_level": "medium",
  "needs_human_review": true,
  "missing_documents": ["boletim_ocorrencia"],
  "key_findings": ["datas divergentes entre atestado e narrativa"],
  "recommended_next_action": "solicitar_bo",
  "timestamp": "2026-05-26T12:05:00"
}
```

---

## Mapeamento de decisão para UX da Olga

- `proxima_acao=solicitar_esclarecimento` → coletar detalhes faltantes.
- `decision_status=pending_documents` → pedir documentação listada.
- `needs_human_review=true` → informar escalonamento para análise humana.
- `decision_status=fraud_escalation` → escalar imediatamente para HITL/jurídico.
