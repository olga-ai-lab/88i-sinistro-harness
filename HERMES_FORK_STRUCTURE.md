# 🎯 Hermes Fork Structure - 88i Sinistro Harness

## O que você tem

Este repositório é um **FORK COMPLETO** do Hermes Agent, com:
- ✅ Código-fonte integral do Hermes (NousResearch/hermes-agent)
- ✅ Configuração pronta para customizar
- ✅ Integração com 7 semanas de código Octa
- ✅ 2 remotes Git (origin + upstream) para sincronização

---

## Estrutura de Diretórios

```
88i-sinistro-harness/
│
├── 🔧 HERMES CORE (fork completo)
│   ├── agent/                      # Código principal do Hermes
│   │   ├── lsp/                    # Language Server Protocol
│   │   ├── transports/             # Transporte (HTTP, WebSocket, subprocess)
│   │   └── secret_sources/         # Gerenciamento de secrets
│   │
│   ├── hermes_cli/                 # CLI principal (hermes command)
│   │   ├── dashboard_auth/         # Auth para dashboard
│   │   └── proxy/                  # Proxy HTTP
│   │
│   ├── hermes_*.py                 # Core modules
│   │   ├── hermes_agent.py         # Main agent
│   │   ├── hermes_logging.py       # Logging
│   │   ├── hermes_state.py         # State management
│   │   ├── hermes_time.py          # Timing utils
│   │   └── hermes_constants.py     # Constants
│   │
│   ├── acp_adapter/                # ACP (Anthropic CLI Protocol)
│   ├── acp_registry/               # ACP registry
│   │
│   ├── gateway/                    # Gateway HTTP para múltiplos transports
│   │   ├── platforms/              # Integração com Discord, Telegram, etc
│   │   └── builtin_hooks/          # Webhooks
│   │
│   ├── cron/                       # Agendamento de jobs (cronjob)
│   ├── docker/                     # Docker configurations
│   ├── nix/                        # NixOS setup
│   ├── locales/                    # I18n (internacionalização)
│   │
│   ├── pyproject.toml              # Dependências Python
│   ├── setup.py                    # Setup script
│   ├── LICENSE                     # MIT License
│   └── hermes_bootstrap.py         # Bootstrap do Hermes
│
│
├── 🧠 88i OCTA INTEGRATION (7 semanas mergeadas)
│   ├── agent.py                    # Agente customizado para sinistros
│   ├── main.py                     # FastAPI entrypoint
│   ├── tools.py                    # Custom tools
│   │
│   ├── rules_engine.py             # DMN rules (semana 3)
│   ├── dmn_tables.py               # Tabelas de decisão
│   │
│   ├── doc_pipeline.py             # Pipeline de documentos (semana 4)
│   ├── doc_validators.py           # Validadores de documentos
│   │
│   ├── hitl_queue.py               # Human-in-the-loop (semana 5)
│   ├── shadow_mode.py              # Shadow/Canary mode (semana 7)
│   ├── shadow_comparator.py        # Comparador de resultados
│   │
│   ├── olga_adapter.py             # Adaptador HTTP para Olga
│   ├── olga_bootstrap.py           # Bootstrap Olga client
│   ├── olga_run_flow.py            # Executor FNOL-to-Olga
│   │
│   ├── eval_langfuse.py            # Observability + Langfuse
│   ├── eval_runner.py              # Dataset runner
│   ├── observability.py            # Logging e tracing
│   │
│   ├── baml_src/
│   │   └── sinistro.baml           # Especificações BAML
│   │
│   ├── baml_client/                # BAML client gerado
│   │   ├── async_client.py
│   │   ├── sync_client.py
│   │   ├── types.py
│   │   └── ...
│   │
│   ├── requirements.txt            # Dependencies adicionais
│   ├── Dockerfile                  # Railway-otimizado
│   ├── railway.json                # Configuração Railway
│   │
│   ├── skills/                     # Skills customizadas
│   │   ├── olga-analista-seguros-88i/        # Analista de sinistros
│   │   ├── sinistro-claim-adjudicator/       # Adjudicador
│   │   ├── sinistro-doc-classifier/          # Classificador docs
│   │   └── sinistro-doc-forensics/           # Forensics perito
│   │
│   └── test_*.py                   # Test suite
│
│
├── 📚 DOCUMENTAÇÃO
│   ├── PLANO_CUSTOMIZACAO_88I.md           # Roadmap Fases 1-5
│   ├── MERGE_INTEGRATION_SUMMARY.md        # Summary do merge
│   ├── HERMES_FORK_STRUCTURE.md            # Este arquivo
│   ├── README.md                           # Main README
│   ├── README_88I.md                       # Quick start 88i
│   │
│   ├── docs/
│   │   ├── arquitetura.md                  # Arquitetura do sistema
│   │   ├── runbook.md                      # Runbook operacional
│   │   │
│   │   ├── olga/
│   │   │   ├── http_contracts.md           # Contratos HTTP
│   │   │   ├── output_schema.json          # Schema output
│   │   │   └── system_prompt.md            # System prompt
│   │   │
│   │   ├── olga_hermes_mvp.md              # MVP integration
│   │   │
│   │   ├── condicoes-gerais/               # Condições de seguro
│   │   │   ├── acidentes_pessoais.txt
│   │   │   ├── acidentes_pessoais_uber_2026.pdf
│   │   │   ├── ap_2024.pdf
│   │   │   ├── bagagem_2024.pdf
│   │   │   ├── impedimento_trabalho.txt
│   │   │   └── impedimento_trabalho_uber_2026.pdf
│   │   │
│   │   └── plans/                          # Implementação plans
│   │
│   └── ...
│
│
├── 🛠️ BUILD & DEPLOY
│   ├── setup-hermes.sh             # Setup script Hermes
│   ├── scripts/
│   │   ├── setup_olga_from_hermes.sh
│   │   └── smoke_olga_adapter.py
│   │
│   ├── docker/                     # Docker configs
│   └── nix/                        # NixOS configs
│
│
├── 🧩 EXTENSÕES (Optional)
│   ├── optional-skills/            # Skills opcionais
│   │   ├── autonomous-ai-agents/
│   │   ├── creative/
│   │   ├── devops/
│   │   └── ...
│   │
│   └── optional-mcps/              # MCP servers opcionais
│       ├── linear/
│       └── n8n/
│
│
└── 📦 METADATA
    ├── .git/                       # Git history (full Hermes + your changes)
    ├── .gitignore                  # Git ignore
    ├── .env.example                # Environment template
    ├── .github/
    │   └── workflows/              # CI/CD pipelines
    ├── hermes_agent.egg-info/      # Package metadata
    ├── pyproject.toml              # Python project config
    └── setup.py                    # Setup configuration

```

---

## Qual é a diferença entre seus arquivos e do Hermes?

### ✅ SEU CÓDIGO (88i customizado)
Estes arquivos **NÃO existem** no Hermes base — são seus:

```
agent.py
main.py
tools.py
rules_engine.py
dmn_tables.py
doc_pipeline.py
doc_validators.py
hitl_queue.py
shadow_mode.py
shadow_comparator.py
olga_adapter.py
olga_bootstrap.py
olga_run_flow.py
eval_langfuse.py
eval_runner.py
observability.py
baml_src/sinistro.baml
baml_client/          (gerado a partir de sinistro.baml)
requirements.txt
Dockerfile            (modificado para Railway)
railway.json          (novo)
skills/olga-analista-seguros-88i/
skills/sinistro-claim-adjudicator/
skills/sinistro-doc-classifier/
skills/sinistro-doc-forensics/
test_*.py             (seus testes)
docs/olga/            (seus contracts)
docs/condicoes-gerais/ (seus PDFs seguros)
PLANO_CUSTOMIZACAO_88I.md
MERGE_INTEGRATION_SUMMARY.md
README_88I.md
SETUP_SUMMARY.md
GIT_AUDIT_REPORT.md
HERMES_FORK_STRUCTURE.md
```

### 📦 HERMES CÓDIGO (NousResearch)
Estes diretórios/arquivos vêm do Hermes **fork original**:

```
agent/                     # Core Hermes agent
hermes_cli/                # Hermes CLI
gateway/                   # Multi-platform gateway
acp_adapter/               # ACP support
cron/                      # Cron job scheduler
docker/                    # Docker setup
nix/                       # NixOS support
optional-skills/           # Optional skills
optional-mcps/             # Optional MCPs
hermes_*.py                # Core Hermes modules
pyproject.toml             # Hermes deps
setup.py                   # Hermes setup
LICENSE                    # MIT License
```

---

## Git Remotes

```bash
# Ver remotes
git remote -v

# Output:
# origin     https://github.com/olga-ai-lab/88i-sinistro-harness (seu repo)
# upstream   https://github.com/NousResearch/hermes-agent (Hermes original)
```

### Como usar:

**Pull novas features do Hermes:**
```bash
git fetch upstream
git merge upstream/main     # Ou rebase
```

**Push suas mudanças para GitHub:**
```bash
git push origin main
```

---

## Como Usar Este Fork

### 1️⃣ Setup Local
```bash
cd ~/Projects/88i-sinistro-harness
source .venv/bin/activate
pip install -r requirements.txt
python -m pip install -e .          # Instala Hermes + customizações
```

### 2️⃣ Rodar o Agent
```bash
hermes --version                    # Verifica instalação
python main.py --help               # Seu FastAPI
```

### 3️⃣ Deploy
```bash
git push origin main                # Railway redeploy automático
```

### 4️⃣ Sincronizar com Hermes Original
```bash
git fetch upstream
git log upstream/main..main          # Ver seu commits
git merge upstream/main              # Trazer updates do Hermes
```

---

## Estatísticas

| Métrica | Valor |
|---------|-------|
| **Repo size** | 366 MB |
| **Arquivos Python** | 5.097 |
| **Commits próprios** | 36+ (últimas 2 semanas) |
| **Commits Hermes** | ~5.000+ (histórico completo) |
| **Branches remotos** | 3 (todos mergeados em main) |
| **Skills customizadas** | 4 |
| **PDFs (condicoes-gerais)** | 6 |

---

## Próximos Passos

1. ✅ Fork completo baixado e mergeado
2. ⏭️ Customizar skills (Phase 1)
3. ⏭️ Adicionar custom tools (Phase 2)
4. ⏭️ Fine-tune BAML models (Phase 3)
5. ⏭️ Testing + CI/CD (Phase 4)
6. ⏭️ Deploy + monitoring (Phase 5)

Veja: **PLANO_CUSTOMIZACAO_88I.md**

---

## Troubleshooting

**P: Onde estão os arquivos do Hermes original?**
R: Em `agent/`, `hermes_cli/`, `gateway/`, `acp_adapter/`, `cron/`. Todos vêm do fork original.

**P: Posso deletar arquivos do Hermes?**
R: ⚠️ Não recomendado — quebra as funcionalidades principais. Se precisar, use branches.

**P: Como voltarei para o Hermes vanilla?**
R: `git checkout upstream/main` cria um branch temporário com versão original.

**P: Hermes vai receber updates?**
R: Sim! Use `git fetch upstream && git merge upstream/main` regularmente.
