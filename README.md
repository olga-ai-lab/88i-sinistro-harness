# 88i Sinistro Harness

Agente completo de análise de sinistros **Last Mile Delivery** para a 88i Seguradora Digital.

Substitui o OCTA v4.0 (n8n) no fluxo de **First Notice of Loss (FNOL)**.
Cliente: **CloudWalk/InfinitePay** — volume: 33.000 sinistros/mês.

---

## Stack

| Componente | Tecnologia |
|---|---|
| Extração estruturada | BAML 0.221.0 + Claude Sonnet |
| Orquestração | LangGraph 1.1.8 |
| Workflow durável | Inngest 0.5.18 |
| Observabilidade | Langfuse 4.3.1 |
| HTTP server | FastAPI 0.115 + uvicorn |
| Rules engine | Python puro (DMN-style, auditável SUSEP) |
| Pipeline documental | Skills Hermes (classifier → forensics → adjudicator) |
| Validação forense | Checksums BR + EXIF + ELA + API CFM |
| HITL | Fila priorizada para a Rosi (analista 88i) |
| Shadow mode | SHADOW → CANARY → CUTOVER |
| Eval | Dataset 20 casos + runner + Langfuse |
| Deploy | Railway (Docker) |
| Banco | Supabase (PostgreSQL + Edge Functions) |

---

## Quickstart

```bash
git clone https://github.com/olga-ai-lab/88i-sinistro-harness
cd 88i-sinistro-harness

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
baml-cli generate

cp .env.example .env
# preencher ANTHROPIC_API_KEY

python test_narrativas.py   # 3/3 PASS
python test_semana3.py      # 9/9 PASS
python test_hitl.py         # 10/10 PASS
python test_eval.py         # 10/10 PASS
python test_shadow.py       # 10/10 PASS
python test_validadores.py  # 12/12 PASS
```

---

## Estrutura

```
88i-sinistro-harness/
│
├── agent/                          # núcleo do agente
│   ├── baml_src/sinistro.baml      # schema BAML + prompt ExtrairSinistro
│   ├── baml_client/                # client gerado (NÃO editar)
│   ├── agent.py                    # LangGraph StateGraph (8 nós)
│   ├── tools.py                    # consultar_apolice, historico, registrar
│   ├── rules_engine.py             # motor D1-D15 (ZERO LLM)
│   ├── dmn_tables.py               # tabelas de decisão UBER/PADRAO
│   ├── doc_pipeline.py             # classifier→forensics→adjudicator
│   ├── doc_validators.py           # EXIF, PDF, checksums BR, CRM, ELA
│   ├── hitl_queue.py               # fila HITL para a Rosi
│   ├── shadow_comparator.py        # compara OCTA vs novo agente
│   ├── shadow_mode.py              # SHADOW/CANARY/CUTOVER
│   ├── eval_dataset.json           # 20 casos anotados
│   ├── eval_runner.py              # runner de avaliação
│   ├── eval_langfuse.py            # integração Langfuse
│   ├── observability.py            # Langfuse wrapper fail-open
│   ├── inngest_functions.py        # workflow durável
│   └── main.py                     # FastAPI endpoints
│
├── skills/                         # skills Hermes (copiar para ~/.hermes/skills/insurance/)
│   ├── olga-analista-seguros-88i/  # knowledge base produto 88i
│   ├── sinistro-doc-classifier/    # etapa 1: classifica documento
│   ├── sinistro-doc-forensics/     # etapa 2: extrai campos + forense
│   └── sinistro-claim-adjudicator/ # etapa 3: decisão final + fraude
│
├── supabase/
│   ├── migrations/001_sinistros.sql
│   └── functions/sinistro-webhook/ # Edge Function (webhook → Inngest)
│
├── docs/
│   ├── arquitetura.md
│   ├── runbook.md
│   └── condicoes-gerais/           # PDFs CGs 88i março/2026
│
└── .github/workflows/ci.yml        # CI: testes + eval gate 80%
```

---

## Arquitetura do Agente

```
WhatsApp (Evolution API)
    ↓
Supabase Edge Function
    ↓ grava raw_inbox (auditoria SUSEP)
Inngest event: sinistro/fnol.received
    ↓
FastAPI POST /sinistro
    ↓
LangGraph Pipeline:
  narrativa
    → no_extrair (BAML/Claude) ──────────── extrai tipo, plataforma, red_flags
    → no_consultar_contexto ─────────────── apólice + histórico (Supabase)
    → no_decidir_rota ───────────────────── determinístico (ZERO LLM)
         ├── escalar_humano ──────────────── fila HITL (Rosi)
         ├── solicitar_esclarecimento ────── perguntas ao segurado
         └── pronto_para_analise
               → rules_engine (D1-D15) ──── elegibilidade + cobertura
               → doc_pipeline ──────────────── classifier→forensics→adjudicator
               → registrar_sinistro ─────── protocolo 88i-YYYY-XXXXXXXX
```

---

## Plataformas Suportadas

| Plataforma | Regime | D6 (veiculo) | D7 (coberturas) | Cooldown DITA |
|---|---|---|---|---|
| Uber | CP Uber | só automóvel | só DITA | 30 dias |
| 99 / iFood / Rappi / Loggi / Lalamove | CG Padrão | qualquer | todas (MA, IPA, DMHO, etc.) | 90 dias |
| NAO_MENCIONADA | CG Padrão | qualquer | todas | 90 dias |

---

## Instalando as Skills no Hermes

```bash
mkdir -p ~/.hermes/skills/insurance

cp -r skills/olga-analista-seguros-88i   ~/.hermes/skills/insurance/
cp -r skills/sinistro-doc-classifier     ~/.hermes/skills/insurance/
cp -r skills/sinistro-doc-forensics      ~/.hermes/skills/insurance/
cp -r skills/sinistro-claim-adjudicator  ~/.hermes/skills/insurance/
```

---

## Variáveis de Ambiente

```bash
# Obrigatório
ANTHROPIC_API_KEY=sk-ant-...

# Supabase (produção)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# Inngest
INNGEST_SIGNING_KEY=...

# Langfuse (observabilidade)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Shadow mode
SHADOW_MODE=shadow     # shadow | canary | cutover
CANARY_PERCENT=5       # % de sinistros no novo agente (canary)
```

---

## Endpoints FastAPI

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/sinistro` | Recebe narrativa, roda pipeline completo |
| POST | `/sinistro/{protocolo}/documentos` | Recebe arquivos, roda pipeline documental |
| GET | `/hitl/fila` | Lista fila de revisão para a Rosi |
| GET | `/hitl/tarefa/{id}` | Detalhe de uma tarefa HITL |
| POST | `/hitl/tarefa/{id}/resolver` | Rosi submete decisão |
| GET | `/shadow/relatorio` | Taxa de concordância OCTA vs novo agente |
| GET | `/health` | Healthcheck Railway |

---

## Eval

```bash
# Dry-run (sem LLM) — testa framework
python eval_runner.py --dry-run

# Roda avaliação real (20 casos com Claude)
python eval_runner.py --verbose

# Filtra por categoria
python eval_runner.py --categoria uber_normal

# Envia resultados para Langfuse
python eval_langfuse.py
```

Quality gate: **score_geral >= 80%** → CI passa.

---

## Contatos 88i

- Sinistros: sinistrosapdelivery@88i.io
- SAC: 0800 718 7813
- WhatsApp: +55 11 97803-8881
# Force rebuild trigger (qui 28 mai 2026 10:02:20 -03)
# Clean rebuild with verified imports (qui 28 mai 2026 10:37:40 -03)
