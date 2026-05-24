# sinistro-agent-88i

Agente de ingestão de sinistros da **88i Seguradora Digital**.
Substitui o OCTA v4.0 (bot atual em n8n) no fluxo de First Notice of Loss.
Cliente final: **CloudWalk/InfinitePay** — volume previsto: 33.000 sinistros/mês.

---

## Stack (FECHADA — não debater)

- **BAML 0.221.0** — schema → client Python tipado (saída LLM)
- **LangGraph 1.1.8** — StateGraph com nós de roteamento determinístico
- **Inngest 0.5.18** — orquestração durável de workflow
- **Langfuse 4.3.1** — observabilidade de LLM
- **FastAPI 0.136.0** + **uvicorn** — HTTP server
- **Claude Sonnet 4.5** (via Anthropic API)
- **Python 3.12** (NÃO TypeScript)
- **Railway** (Docker) — deploy
- **Supabase Edge Function** — porta de entrada (webhook Evolution API → raw_inbox → Inngest)

## Rejeitado (não sugerir sem motivo novo)

n8n, Temporal, Kestra, Argo, LangChain puro.

Se alguém tiver argumento substancial pra reabrir uma dessas decisões, consultar
"Decisões arquiteturais" abaixo primeiro — a maioria dos argumentos já foi
considerada e descartada. Reabrir só se houver dado novo (mudança de volume,
compliance, etc).

---

## Decisões arquiteturais (por quê, não só o quê)

### Por que BAML (e não Pydantic + Instructor, ou LangChain structured output)
- BAML embute o schema E o prompt num único artefato versionado (`.baml`),
  e gera client Python tipado a cada build. Mudou o schema → cliente
  tipado quebra compilação, não em runtime com log enigmático.
- Instructor faz retry cego em cima de Pydantic; BAML tem parsing tolerante
  (SAP — Schema-Aligned Parser) que aceita variações do LLM antes de falhar.
- LangChain structured output depende da runtime inteira do LangChain, que
  já foi rejeitada no projeto.

### Por que LangGraph (e não agente ad-hoc com if/else)
- Precisamos de nós explícitos e transições auditáveis pra SUSEP: quem
  decidiu o quê, em qual ordem. LangGraph força isso via StateGraph.
- Evita o anti-padrão "prompt gigante que decide tudo" — a decisão de rota
  vive em código Python puro (`no_decidir_rota`), não no LLM.

### Por que Inngest (e não Temporal, Celery ou SQS)
- Durabilidade com retries idempotentes por step sem operar cluster
  (Temporal exige servidor próprio).
- Observabilidade nativa de eventos e replays — crítico pra reprocessar
  sinistro quando a análise documental (Semana 3-4) falhar.
- Celery/SQS não dão step-level retry nem replay visual.

### Por que FastAPI (e não Flask ou Django)
- Async nativo, tipos fortes, OpenAPI grátis — integra com Supabase Edge
  Function (webhook) sem middleware extra.
- Inngest tem binding oficial (`inngest.fast_api.serve`).

### Por que Claude Sonnet 4.5 (e não GPT-4o ou Gemini)
- Melhor aderência a schemas estruturados em português brasileiro.
- Controle fino de temperatura=0 sem regressão de qualidade.
- Já é o modelo padrão da OlgaAI; sem custo adicional de onboarding.

### Por que Python 3.12 (e não TypeScript)
- Ecosistema de ML/observabilidade em Python é superior (Langfuse,
  BAML client).
- Time interno da 88i já escreve Python; TypeScript geraria custo de
  onboarding sem benefício proporcional.

### Por que Railway (e não AWS, Fly, Render)
- Deploy via Dockerfile em <10 min sem config de IAM/VPC.
- Volume previsto (33k sinistros/mês ≈ 1 req/minuto médio) não justifica
  complexidade de AWS nesta fase.

### Por que Supabase Edge Function na porta de entrada
- Webhook da Evolution API grava em `raw_inbox` ANTES de acordar o agente:
  auditoria SUSEP fica garantida mesmo se o agente estiver fora.
- Edge Function + RLS + migrations versionadas dão o pacote
  audit-grade sem infra extra.

### Por que Langfuse (e não LangSmith ou Datadog APM)
- LangSmith obriga LangChain; Datadog não tem tratamento nativo de
  prompt/completion.

---

## Princípios não-negociáveis

1. **Separação neurosimbólica.** LLM interpreta; código decide.
   O nó `no_decidir_rota` em `agent.py` é ZERO LLM — roteamento por thresholds
   explícitos e auditáveis.
2. **Tipos sempre.** BAML pra saída LLM, Pydantic/TypedDict no resto.
3. **Idempotência por step Inngest.** Cada step deve ser retry-safe.
4. **Auditabilidade SUSEP.** Tudo registrado em Supabase + Langfuse.
5. **Fail-closed.** Se extração falhar ou confiança < 0.6, escalar humano.

---

## Tipos de sinistro 88i

| Código | Descrição |
|---|---|
| MA | Morte Acidental |
| IPA | Invalidez Permanente por Acidente |
| DITA | Diária por Incapacidade Temporária por Acidente |
| DMHO | Despesas Médico-Hospitalares |
| MAC | Morte por Qualquer Causa |
| IAT | Impedimento ao Trabalho |
| AF | Auxílio Funeral |
| BAGAGEM | Bagagens e Encomendas (CloudWalk/delivery) |

---

## Glossário

- **FNOL** — First Notice of Loss (aviso de sinistro)
- **OCTA** — bot atual em n8n, sendo substituído por este agente
- **SUSEP** — regulador brasileiro de seguros
- **Rosi** — analista de sinistros da 88i; destino da fila humana

---

## Escopo por semana

| Semana | Entrega |
|---|---|
| **1** (atual) | Ingestão + roteamento (BAML + LangGraph + testes) |
| 2 | Tools/MCP |
| 3 | Rules engine DMN |
| 4 | HITL (human-in-the-loop) |
| 5 | Paralelismo |
| 6 | Eval dataset |
| 7 | Shadow mode |
| 8 | Cutover CloudWalk |

**Semana 1 NÃO faz:** decidir cobertura, consultar apólice, enviar WhatsApp
de volta. Pendências documentais ficam registradas no state e são consumidas
pela camada de análise documental (Semana 3-4).

---

## Arquitetura atual (Semana 1)

```
narrativa → no_extrair (BAML) → no_decidir_rota → [3 saídas]
                                      │
                                      ├── pronto_para_analise
                                      ├── solicitar_esclarecimento
                                      └── escalar_humano
```

**Regras de `no_decidir_rota` (determinísticas, nesta ordem):**
1. Red flag severidade alta → `escalar_humano`
2. `ha_vitimas_fatais` → `escalar_humano`
3. `confianca < 0.6` OU `requer_esclarecimento=True` → `solicitar_esclarecimento`
4. Fallback → `pronto_para_analise` (bloqueantes viram pendências documentais)

---

## Convenções BAML (prompt de `ExtrairSinistro`)

- `confianca` reflete certeza real do LLM (0.0–1.0)
- `campos_faltantes` classificados por criticidade:
  - **bloqueante** — só o segurado pode fornecer (ex.: atestado médico, BO)
  - **importante** — dado consultável em sistema (apólice, cadastro)
  - **opcional** — nice-to-have
- `requer_esclarecimento` é sobre COMPREENSÃO DO EVENTO, não sobre documentação
- Schema completo em `baml_src/sinistro.baml`

---

## Padrões de depuração (aprendidos na Etapa 1)

### As 3 perguntas antes de mexer em código
Quando o comportamento do agente divergir do esperado, responder estas
3 perguntas antes de qualquer mudança:

1. **A expectativa estava errada?** O caso teste pode ter sido mal
   desenhado — o "esperado" pode não refletir o que deveria acontecer.
2. **A definição estava ambígua?** O prompt pode dizer uma coisa e o
   LLM interpretar outra — solução é refinar definição, não forçar output.
3. **A lógica de fluxo (código) estava errada?** O que o LLM retorna
   está certo, mas a regra em código que consome está misturando
   conceitos diferentes.

Na Etapa 1, o Caso 1 falhou 2 vezes. Primeira rodada: definição de
"bloqueante" estava ambígua (ajuste no prompt BAML). Segunda rodada:
lógica de `no_decidir_rota` misturava "faltam docs" com "não entendi
narrativa" (ajuste em `agent.py`, não no prompt). Se tivéssemos forçado
o LLM a dar o output esperado, teríamos criado bug permanente.

Regra derivada: **LLM julga compreensão semântica; código decide fluxo
operacional.**

### Confiança do LLM não é nota do prompt
Caso 1 do `test_narrativas.py` passou com confiança 0.75 em duas rodadas —
e mesmo assim caiu na rota errada. O sintoma não estava no score do LLM,
estava em como o prompt definia os campos `requer_esclarecimento` e
`campos_faltantes bloqueantes`. **Regra:** quando um caso falha mas a
extração "parece boa", o problema quase sempre é semântico no prompt,
não na capacidade do modelo.

### BAML embute o prompt em `inlinedbaml.py`
O conteúdo do `.baml` é serializado pro Python no momento do
`baml-cli generate`. Editar o `.baml` SEM regenerar o cliente não tem
efeito — o prompt antigo continua rodando. **Sempre regenerar depois de
qualquer edit no `.baml`.**

### Regenerar em ambiente com permissões restritas
Se o diretório do projeto tiver mount read-only parcial (caso do sandbox
Claude), o `baml-cli generate` falha ao criar `baml_client.tmp/`.
Workaround:

```bash
REGEN=/tmp/baml_regen
mkdir -p $REGEN/baml_src
cp baml_src/sinistro.baml $REGEN/baml_src/
cd $REGEN && baml-cli generate
cp $REGEN/baml_client/*.py <projeto>/baml_client/
```

### Python stdout buffering em scripts longos
Rodar `python script.py` com print() e redirecionamento pode engolir
output até a próxima flush. **Use `python -u`** em todos os comandos
de teste pra ver logs em tempo real.

### Testes BAML embutidos vs test_narrativas.py
- `baml-cli test` valida que o schema é preenchível — útil pra smoke test.
- `test_narrativas.py` valida o grafo inteiro (extração + roteamento +
  mensagem). **É este que manda.** 3/3 PASS é o gate de qualquer commit
  que toque em `agent.py` ou `sinistro.baml`.

### Python 3.10 local vs 3.12 em produção
Se o ambiente local não tiver 3.12, rodar com 3.10 é aceitável para
desenvolvimento. Deploy Railway usa 3.12 via Docker.

---

## Workflow de trabalho (Fernanda + Claude)

- Plano em bullets ANTES de criar/editar arquivos; espera OK explícito
- Comandos destrutivos: confirmar antes
- Commits: **Conventional Commits em inglês**
- Comunicação: **português brasileiro, direto, sem bajulação**
- **Commits feitos diretamente pelo Claude** no terminal local, seguindo Conventional Commits em inglês.
- Regressão em `test_narrativas.py` (3/3) → parar e reportar antes de
  qualquer outra coisa

---

## Estrutura do projeto

Status: ✅ pronto · ⏳ em implementação · ⬜ próxima semana

```
sinistro-agent-semana1/
├── .env                      ⏳ gitignored; configurar ANTHROPIC_API_KEY
├── .env.example              ✅ placeholders
├── .gitignore                ✅
├── CLAUDE.md                 ⏳ este arquivo — em criação
├── README.md                 ✅ instruções rápidas
├── agent.py                  ✅ LangGraph: 5 nós + roteamento determinístico
├── observability.py          ⏳ Langfuse wrapper fail-open (Etapa 2)
├── inngest_functions.py      ⏳ workflow durável (Etapa 2)
├── main.py                   ⏳ FastAPI + healthcheck (Etapa 2)
├── requirements.txt          ⏳ atualizar com langfuse/inngest/fastapi (Etapa 2)
├── test_narrativas.py        ✅ 3/3 PASS
├── baml_src/
│   └── sinistro.baml         ✅ schema + prompt ExtrairSinistro
├── baml_client/              ✅ gerado; NÃO editar à mão
│   ├── sync_client.py
│   ├── types.py
│   ├── inlinedbaml.py        (prompt embutido — regenerar após edit no .baml)
│   └── ...
├── Dockerfile                ⬜ Etapa 3 (Railway)
├── railway.json              ⬜ Etapa 3
└── supabase/                 ⬜ Etapa 3
    ├── migrations/
    │   └── 20260419_sinistro_raw_inbox.sql
    └── functions/
        └── sinistro-webhook/
            └── index.ts
```

A cada commit da Etapa 2, atualizar os status: todos os ⏳ viram ✅.

---

## Como rodar localmente

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
baml-cli generate
export ANTHROPIC_API_KEY=...
python test_narrativas.py
```

Esperado: **3/3 PASS**.
