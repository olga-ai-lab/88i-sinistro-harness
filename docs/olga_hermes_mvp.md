# Olga Agent (Hermes) — Plano de Implementação e Templates

## 1) Objetivo

Integrar um agente **Olga** (runtime Hermes) ao backend atual `88i-sinistro-harness`, mantendo as decisões críticas no motor determinístico (`rules_engine.py`) e usando LLM para orquestração/documentação.

---

## 2) Arquitetura recomendada

- **Hermes/Olga**: interface conversacional + orchestration.
- **Sinistro Harness (este repo)**: API FastAPI + regras D1-D15 + pipeline documental + HITL.
- **Skills**: conhecimento de negócio e análise documental.

Fluxo:
1. Olga recebe FNOL (narrativa).
2. Olga chama `POST /sinistro`.
3. Se necessário, coleta documentos e chama `POST /sinistro/{protocolo}/documentos`.
4. Se `needs_human_review=true`, Olga orienta/escalona para HITL.

---

## 3) Prompt base da Olga (`system_prompt.md`)

Use este conteúdo no agente Hermes:

```md
Você é Olga, analista assistente de sinistros da 88i.

Objetivo:
- Coletar informações de FNOL com clareza.
- Chamar as ferramentas de backend para decisão auditável.
- Nunca inventar cobertura, prazo ou elegibilidade.

Regras:
1. Priorize decisões do backend (não substitua com opinião própria).
2. Se confiança baixa, dados inconsistentes ou suspeita de fraude: escalar revisão humana.
3. Se faltar documento, explique exatamente quais faltam e por quê.
4. Responda em português claro, objetivo e empático.
5. Produza saída estruturada no schema definido.

Restrições:
- Não prometer aprovação.
- Não expor dados sensíveis desnecessários.
- Não ignorar alertas operacionais retornados pela API.
```

---

## 4) Schema de saída (`output_schema.json`)

```json
{
  "type": "object",
  "required": ["intent", "message_to_user", "next_action"],
  "properties": {
    "intent": {
      "type": "string",
      "enum": ["fnol_triage", "document_collection", "document_decision", "hitl_escalation", "status_update"]
    },
    "next_action": {
      "type": "string",
      "enum": ["ask_more_info", "submit_fnol", "request_documents", "submit_documents", "escalate_human", "finalize"]
    },
    "message_to_user": { "type": "string" },
    "protocolo": { "type": ["string", "null"] },
    "decision_status": { "type": ["string", "null"] },
    "needs_human_review": { "type": ["boolean", "null"] },
    "missing_documents": {
      "type": "array",
      "items": { "type": "string" }
    },
    "fraud_score": { "type": ["integer", "null"] },
    "alerta_operacional": { "type": ["string", "null"] }
  }
}
```

---

## 5) Contratos HTTP para tools Hermes

### 5.1 `POST /sinistro`

Request:

```json
{
  "narrativa": "Bati minha moto ontem na Paulista, fraturei a perna.",
  "segurado_id": "SEG-001"
}
```

Response (resumo):

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

### 5.2 `POST /sinistro/{protocolo}/documentos`

Use multipart/form-data com múltiplos arquivos no campo `arquivos`.

Response (resumo):

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

### 5.3 `GET /health`

Healthcheck operacional do serviço.

---

## 6) Playbook de integração (MVP)

1. Configurar tools HTTP no Hermes para os 3 endpoints.
2. Aplicar `system_prompt.md` da Olga.
3. Forçar saída estruturada com `output_schema.json`.
4. Implementar regra no fluxo:
   - Se `proxima_acao` indicar esclarecimento/documentos, Olga guia o segurado.
   - Se `needs_human_review=true`, Olga comunica encaminhamento HITL.
5. Testar 5 cenários:
   - sinistro elegível sem fraude,
   - falta de documento,
   - suspeita de fraude,
   - narrativa ambígua,
   - erro de integração (API indisponível).

---

## 7) Checklist de go-live

- [ ] `/health` responde 200.
- [ ] `POST /sinistro` responde com protocolo e próxima ação.
- [ ] Upload de documentos funciona por multipart.
- [ ] Casos com `needs_human_review=true` viram mensagem de escalonamento.
- [ ] Logs com protocolo e correlation id.
- [ ] Variáveis de ambiente de produção configuradas.

## 8) Artefatos prontos no repositório

- `docs/olga/system_prompt.md`
- `docs/olga/output_schema.json`
- `docs/olga/http_contracts.md`

## 9) Início imediato (executável)

Este repositório agora inclui `olga_bootstrap.py`, um cliente CLI para iniciar integração real com os endpoints:

```bash
python olga_bootstrap.py health
python olga_bootstrap.py fnol --narrativa "Bati minha moto ontem" --segurado-id SEG-001
python olga_bootstrap.py docs --protocolo 88i-2026-00000001 --file /caminho/bo.pdf
```

Objetivo: permitir validação fim-a-fim do contrato HTTP antes de plugar no runtime Hermes.

## 10) Cópia completa do Hermes (execução)

Para materializar a cópia completa do repositório Hermes no workspace e aplicar overlay inicial da Olga:

```bash
./scripts/setup_olga_from_hermes.sh
```

Isso clona `NousResearch/hermes-agent` em `third_party/hermes-agent` e copia os artefatos da Olga para `third_party/hermes-agent/olga/`.
