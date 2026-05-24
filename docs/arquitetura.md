# Arquitetura — 88i Sinistro Harness

## Visão Geral

O agente substitui o OCTA v4.0 (bot n8n) no fluxo de First Notice of Loss (FNOL) da 88i Seguradora Digital para o cliente CloudWalk/InfinitePay.

Volume previsto: **33.000 sinistros/mês** (≈ 1 req/min média).

---

## Princípios Não-Negociáveis

1. **Separação neurosimbólica** — LLM interpreta narrativa; código Python decide o fluxo. O nó `no_decidir_rota` é ZERO LLM.
2. **Tipos sempre** — BAML para saída LLM, Pydantic/TypedDict no resto.
3. **Auditabilidade SUSEP** — tudo registrado em Supabase + Langfuse.
4. **Fail-closed** — confiança < 0.6 → escalar humano. Nunca aprovar na dúvida.
5. **Idempotência** — cada step Inngest deve ser retry-safe.

---

## Fluxo Completo

```
Segurado (WhatsApp)
    │
    ▼ webhook Evolution API
Supabase Edge Function (sinistro-webhook)
    │ grava raw_inbox (auditoria SUSEP antes de qualquer processamento)
    ▼ Inngest event: sinistro/fnol.received
FastAPI + Inngest
    │
    ▼
LangGraph StateGraph
    │
    ├─ no_extrair (BAML + Claude Sonnet)
    │   └─ ExtracaoSinistro: tipo, plataforma, urgencia, red_flags, confianca
    │
    ├─ no_consultar_contexto (tools.py — ZERO LLM)
    │   ├─ consultar_apolice(segurado_id) → vigencia, coberturas, carencia
    │   └─ buscar_historico_sinistros()  → frequencia, alerta >= 3/12m
    │
    ├─ no_decidir_rota (determinístico — ZERO LLM)
    │   ├─ red_flag alta OU >= 3 red_flags media → escalar_humano
    │   ├─ vitima fatal → escalar_humano
    │   ├─ alerta_frequencia → escalar_humano
    │   ├─ apolice vencida → escalar_humano
    │   ├─ confianca < 0.6 OU requer_esclarecimento → solicitar_esclarecimento
    │   └─ fallback → pronto_para_analise
    │
    ├─ no_pronto_para_analise
    │   ├─ rules_engine.avaliar_cobertura() — D1-D15 (ZERO LLM)
    │   │   ├─ Regime UBER: D6 (só automóvel), D7 (só DITA), cooldown 30d
    │   │   └─ Regime PADRAO: todas coberturas, qualquer veículo, cooldown 90d
    │   └─ registrar_sinistro() → protocolo 88i-YYYY-XXXXXXXX
    │
    ├─ no_analisar_documentos (doc_pipeline.py)
    │   ├─ Etapa 0: doc_validators (ZERO LLM — EXIF, checksums BR, CRM, ELA)
    │   ├─ Etapa 1: sinistro-doc-classifier (Claude + skill)
    │   ├─ Etapa 2: sinistro-doc-forensics (Claude + skill + cross-validation)
    │   └─ Etapa 3: sinistro-claim-adjudicator (Claude + skill + fraud scoring)
    │
    └─ no_escalar_humano
        └─ hitl_queue.criar_tarefa() → fila priorizada para a Rosi
```

---

## Regimes de Plataforma

A partir da Semana 4.5, o agente suporta múltiplas plataformas. O regime é determinado pelo campo `plataforma_mencionada` extraído pelo BAML:

| Plataforma extraída | Regime | Restrições |
|---|---|---|
| UBER | UBER | D6 (só automóvel no Prod.A), D7 (só DITA no Prod.B), cooldown 30d |
| NOVENTA_E_NOVE, IFOOD, RAPPI, LOGGI, LALAMOVE | PADRAO | Sem D6/D7, todas coberturas Prod.B disponíveis, cooldown 90d |
| OUTRA_PLATAFORMA, NAO_MENCIONADA | PADRAO | Sem D6/D7, fail-safe (não assume restrições) |

---

## Shadow Mode

Antes do cutover para produção com 33k sinistros/mês, o agente passa por 3 fases:

```
SHADOW  → novo agente roda invisível, OCTA retorna resultado
          divergências logadas no Langfuse
    ↓ quando concordância >= 95% em >= 100 sinistros
CANARY  → X% dos sinistros usam o novo agente (começa em 5%)
          hash determinístico por narrativa (retry-safe)
    ↓ quando concordância >= 95% em >= 500 sinistros
CUTOVER → 100% novo agente, OCTA desativado
```

Controle via env: `SHADOW_MODE=shadow|canary|cutover` + `CANARY_PERCENT=5`

---

## Regras D (DMN)

| Código | Regra | Regime |
|---|---|---|
| D1 | Apólice vigente na data do fato | Todos |
| D2 | Fora do período de carência | Todos |
| D4 | Cooldown respeitado (30d Uber / 90d padrão) | A, B |
| D6 | Somente automóvel (Produto A / Uber) | A + UBER |
| D7 | Coberturas restritas Uber (só DITA) | B + UBER |
| D8 | Tipo de sinistro tem cobertura mapeada | Todos |
| D11 | NF não é de parente do segurado | C |
| D12 | Encomenda em declaração prévia | C |
| D14 | Tratamento médico iniciado em até 30 dias | B |
| D15 | CNH ativa no momento do sinistro | A, B |

---

## Tabela de Decisão: tipo_sinistro → cobertura

| Tipo | Regime | Cobertura | Produto |
|---|---|---|---|
| DITA | UBER | B_DITA | B |
| DITA | PADRAO | B_DITA | B |
| IPA | UBER | ❌ D7 | B |
| IPA | PADRAO | B_IPA | B |
| MA | UBER | ❌ D7 | B |
| MA | PADRAO | B_MA | B |
| DMHO | UBER | ❌ D7 | B |
| DMHO | PADRAO | B_DMHO | B |
| IAT | UBER | A_COB_I / A_COB_II (só automóvel — D6) | A |
| IAT | PADRAO | A_COB_I / A_COB_II (qualquer veículo) | A |
| BAGAGEM | UBER | C_COB_A / C_COB_B | C |
| BAGAGEM | PADRAO | C_COB_A / C_COB_B | C |

---

## Decisões Arquiteturais

Ver `CLAUDE.md` para justificativas completas de: BAML vs Instructor, LangGraph vs if/else, Inngest vs Temporal, FastAPI vs Flask, Railway vs AWS, Supabase vs RDS, Langfuse vs LangSmith.
