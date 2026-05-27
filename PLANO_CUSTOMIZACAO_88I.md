# Plano de Customização: 88i Sinistro Harness

**Status:** Setup inicial concluído ✓
**Data:** 27 de maio de 2026
**Versão Hermes:** 0.14.0

---

## 1. Overview — O que você está customizando

Base: Hermes Agent (agente IA multi-tool open source)
Objetivo: Criar agente especializado em análise de sinistros para 88i Seguradora Digital
Escopo: Last Mile Delivery (AP, DITA, Impedimento ao Trabalho)
Stack: BAML + LangGraph + Inngest + FastAPI
Cliente Principal: CloudWalk/InfinitePay (33k sinistros/mês)

---

## 2. Estrutura do Projeto

```
~/Projects/88i-sinistro-harness/
├── run_agent.py              [Core] AIAgent class — conversas
├── cli.py                    [Core] CLI interativa (685KB!)
├── model_tools.py            [Core] Orchestração de tools
├── toolsets.py               [Config] Definições de toolsets
├── hermes_state.py           [Core] SessionDB (SQLite + FTS5 search)
├── hermes_constants.py       [Config] Paths profile-aware
├── agent/                    [Core] Internals — providers, memory, cache
│   ├── chat_completion_helpers.py  [Key] LLM calls + tool dispatch
│   └── ...
├── tools/                    [Extensível] Tool implementations
│   ├── registry.py           [Key] Auto-discovery de tools
│   ├── terminal_tool.py      [Key] Execução de shell
│   ├── code_execution_tool.py [Key] Python REPL
│   ├── browser_tool.py       [Large] Navegador automatizado
│   ├── delegate_tool.py      [Key] Spawn subagents
│   ├── cronjob_tools.py      [Key] Scheduler de jobs
│   └── <40+ mais tools>
├── skills/                   [Extensível] Built-in skills
│   ├── github/
│   ├── research/
│   ├── devops/
│   └── <mais skills>
├── plugins/                  [Extensível] Plugin system
│   ├── memory/               [Providers] honcho, mem0, supermemory
│   ├── model-providers/      [Providers] anthropic, openrouter, gmi
│   ├── kanban/               [Workers] Multi-agent orchestration
│   └── <mais plugins>
├── gateway/                  [Optional] Messaging gateway
│   ├── platforms/            [Adapters] Telegram, Discord, Slack, etc
│   └── run.py                [Server] HTTP server
├── hermes_cli/               [CLI] Subcommands, setup, skin engine
├── tests/                    [Testing] ~17k tests em ~900 arquivos
└── pyproject.toml            [Config] Deps, extras, scripts
```

---

## 3. 5 Pontos de Customização Principais

### A. SKILLS PERSONALIZADAS (LOW EFFORT, HIGH VALUE)
**Onde:** `skills/seguros/` (novo diretório)
**O que fazer:**
  - Criar skill `sinistro-analyzer` — análise de documentação, extração de campos
  - Criar skill `fraude-detector` — detecção de padrões suspeitos
  - Criar skill `88i-sinistro-process` — workflow específico 88i
  - Cada skill = 1 diretório com SKILL.md + references/ + scripts/ + templates/

**Benefícios:**
  - Fácil de versionarycar no Git
  - Reutilizável via `/skills` command no CLI
  - Sem mexer em código core
  - Podem chamar tools existentes (terminal, browser, code_execution)

**Exemplo structure:**
```
skills/seguros/sinistro-analyzer/
├── SKILL.md                  # Metadata + markdown docs
├── references/
│   ├── 88i-sinistro-flow.md  # Documentação do workflow
│   ├── campo-mappings.json   # Campo → tipo/validação
│   └── regra-negocio.md      # Business rules
├── scripts/
│   ├── extract_fields.py     # CLI: extrai campos de PDF
│   └── validate_claim.py     # Valida sinistro
└── templates/
    └── analise_relatorio.md  # Template de relatório
```

---

### B. CUSTOM TOOLS (MEDIUM EFFORT, MEDIUM VALUE)
**Onde:** `tools/` (adicionar arquivos .py)
**O que fazer:**
  1. `tools/sinistro_tools.py` — wrapper BAML pra análise estruturada
  2. `tools/supabase_tool.py` — acesso ao BD de sinistros (cloudwalk)
  3. `tools/inngest_tool.py` — dispara workflows Inngest
  4. `tools/langraph_tool.py` — integra com LangGraph state machines

**Como registrar:**
```python
# tools/sinistro_tools.py
from tools.registry import register

@register("sinistro_analyzer")
def analyze_sinistro(claim_id: str, document_paths: list) -> dict:
    """Analisa sinistro com BAML."""
    # Seu código aqui
    return {"análise": ..., "campos_extraídos": ...}

@register("fraude_check")
def check_fraud(claim_data: dict) -> dict:
    """Detecta padrões de fraude."""
    # Seu código aqui
    return {"risco": "baixo|médio|alto", "evidências": [...]}
```

**Benefícios:**
  - Auto-discoverable pelo Hermes (registry.py)
  - Vira uma tool que qualquer skill/agente pode chamar
  - Suporta async (via tools/registry.py)

---

### C. PLUGINS PERSONALIZADOS (MEDIUM EFFORT, HIGH VALUE)
**Onde:** `plugins/seguros/` (novo diretório)
**O que fazer:**
  1. **Memory Plugin:** Armazena contexto de sinistros em Supabase
  2. **Context Engine:** Recupera histórico de sinistros similares
  3. **Dashboard:** Metrics de sinistros processados (FastAPI)

**Exemplo structure:**
```
plugins/seguros-context-engine/
├── __init__.py               # Entry point
├── supabase_context.py       # Fetch historical claims
├── embedding_cache.py        # Vector store (Supabase pgvector)
└── dashboard/                # FastAPI web UI
    ├── manifest.json         # Plugin metadata
    └── dist/                 # Built frontend (React)
```

**Como criar:**
- Plugins são importados em `hermes_cli/plugins.py`
- Hook automático na inicialização do agent
- Acesso ao `hermes_state.SessionDB` pra ler/escrever contexto

---

### D. SYSTEM PROMPT CUSTOMIZADO (TRIVIAL EFFORT, HIGH VALUE)
**Onde:** `~/.hermes/config.yaml` (ou via environment)
**O que fazer:**
```yaml
ai:
  system_prompt: |
    Você é um analista sênior de sinistros da 88i Seguradora Digital.
    Especialista em sinistros de Last Mile Delivery:
    - AP (Acidentes Pessoais)
    - DITA (Dano Intencional Total ou Acidental)
    - Impedimento ao Trabalho
    
    Seu objetivo: análise rápida e assertiva, detectar fraudes, extrair campos.
    
    Contexto do cliente: CloudWalk/InfinitePay, 33k sinistros/mês.
    Urgência: 4-6 horas por sinistro.
    
    Use as tools: sinistro_analyzer, fraude_check, supabase_query, inngest_trigger.
```

**Também customizar em código:**
```python
# run_agent.py ou hermes_cli/main.py
SYSTEM_MESSAGE = """
Você é o Octa, agente de sinistros 88i...
"""
```

---

### E. GATEWAY + BOT DE WHATSAPP (MEDIUM EFFORT, HIGH VALUE)
**Onde:** `gateway/platforms/` (adicionar `whatsapp_88i.py`)
**O que fazer:**
  1. Integrar com API WhatsApp (via Twilio/Meta)
  2. Receber sinistro via WhatsApp
  3. Retornar análise em tempo real
  4. Usar as skills + tools customizadas

**Exemplo flow:**
```
Usuario WhatsApp → POST /webhook/whatsapp
    ↓
gateway/platforms/whatsapp_88i.py (parse mensagem)
    ↓
AIAgent.run_conversation() (chama skills + tools)
    ↓
Response → WhatsApp API
    ↓
Usuario recebe análise
```

---

## 4. Roadmap de Implementação

### FASE 1: Setup + Skills (1-2 dias)
- [x] Clonar Hermes + setup .venv ← FEITO
- [ ] Criar diretório `skills/seguros/`
- [ ] Skill #1: `sinistro-analyzer` (análise de docs + extração)
- [ ] Skill #2: `fraude-detector` (padrões suspeitos)
- [ ] Testar skills via CLI: `hermes /sinistro-analyzer`

### FASE 2: Custom Tools (2-3 dias)
- [ ] Tool: `sinistro_tools.py` (BAML wrapper)
- [ ] Tool: `supabase_tool.py` (queries de BD)
- [ ] Tool: `inngest_tool.py` (dispara workflows)
- [ ] Registrar no `tools/registry.py`
- [ ] Testes unitários em `tests/test_sinistro_tools.py`

### FASE 3: Context Engine Plugin (3-5 dias)
- [ ] Plugin: `plugins/seguros-context-engine/`
- [ ] Fetch sinistros similares via embeddings (pgvector)
- [ ] Integrar com SessionDB
- [ ] Dashboard FastAPI básico

### FASE 4: System Prompt + Testing (1 dia)
- [ ] Customizar system prompt no config.yaml
- [ ] E2E test: sinistro completo (upload → análise → relatório)
- [ ] Benchmark: tempo de análise

### FASE 5: Gateway + WhatsApp (3-5 dias)
- [ ] Integração Twilio/Meta WhatsApp
- [ ] Webhook handler
- [ ] Deploy em Railway/Render

---

## 5. Stack Técnico — Como Usar o que Existe

### LLM + Providers
Hermes suporta nativamente:
- **Anthropic** (nativo)
- **OpenRouter** (agregador)
- **OpenAI** (via OpenRouter)
- **Custom via plugins** (model-providers/)

**Recomendação:** Use Claude via Anthropic (melhor pra análise/reasoning)

### Databases
- **Built-in:** SQLite (SessionDB em `hermes_state.py`) para session history
- **Seu bd:** Supabase (JWT) — acesso via `tools/supabase_tool.py`
- **Vector Store:** Supabase pgvector pra embeddings

### Workflows
- **Hermes built-in:**
  - Cron jobs (via `tools/cronjob_tools.py`)
  - Subagents (via `tools/delegate_tool.py`)
- **Seu workflow:** LangGraph (agora com BAML)
- **Seu scheduler:** Inngest (já integrado)

### Logging + Observability
- Hermes built-in: `~/.hermes/logs/` (agent.log, errors.log)
- Adicione: Langfuse (tracing LLM), Supabase (logs estruturados)

---

## 6. Comandos Essenciais After Setup

```bash
# Ativar venv
cd ~/Projects/88i-sinistro-harness
source .venv/bin/activate

# Rodar o agente interativo (CLI)
python run_agent.py

# Ou usar o comando instalado (depois de `pip install -e .`)
hermes

# Listar tools available
hermes tools

# Rodar um skill específico
hermes /sinistro-analyzer

# Ver logs
hermes logs --follow

# Testes
python -m pytest tests/ -v -k "test_sinistro"

# Dev: editar + reload automático
# (Hermes não tem hot-reload, mas py-repl via `execute_code` tool funciona)
```

---

## 7. Arquivos para Mexer EM ORDEM

1. **IMEDIATO:**
   - `skills/seguros/sinistro-analyzer/SKILL.md`
   - `skills/seguros/fraude-detector/SKILL.md`

2. **CURTO PRAZO:**
   - `tools/sinistro_tools.py` (novo)
   - `tools/supabase_tool.py` (novo)

3. **MÉDIO PRAZO:**
   - `plugins/seguros-context-engine/__init__.py` (novo)
   - `~/.hermes/config.yaml` (editar system prompt)

4. **LONGO PRAZO:**
   - `gateway/platforms/whatsapp_88i.py` (novo)
   - `deploy/Dockerfile` (customizar pra seu stack)

5. **NÃO MEXER (core Hermes):**
   - `run_agent.py` — use via CLI ou API
   - `cli.py` — use via `hermes` command
   - `model_tools.py` — estável, não precisa
   - `toolsets.py` — adicione toolsets via plugins, não aqui

---

## 8. Deploy

**Current:** Railway (problemas com FastAPI routing — ver memory)
**Recomendação:** Render.com ou Vercel (melhor FastAPI support)

Setup deploy com seu stack:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENV ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
ENV SUPABASE_URL=$SUPABASE_URL
ENV INNGEST_API_KEY=$INNGEST_API_KEY
CMD ["hermes", "--gateway", "0.0.0.0:3000"]
```

---

## 9. Próximo Passo

Você quer começar por qual?

**A) Skills (rápido, fácil)**
```bash
mkdir -p skills/seguros/sinistro-analyzer
touch skills/seguros/sinistro-analyzer/SKILL.md
```

**B) Custom Tools (mais estruturado)**
```bash
touch tools/sinistro_tools.py
```

**C) Explorar o código (understand first)**
```bash
cd ~/Projects/88i-sinistro-harness
source .venv/bin/activate
python run_agent.py  # teste o agent básico
```

Qual você prefere?

---

## Links Úteis

- **Hermes Docs:** https://hermes-agent.nousresearch.com/docs
- **AGENTS.md (project guide):** ./AGENTS.md
- **Skills authoring:** skill_manage(action='create')
- **Tool registry:** tools/registry.py
- **Plugin system:** hermes_cli/plugins.py
