# 88i Sinistro Harness — Setup Concluído ✓

**Data:** 27 de maio de 2026  
**Status:** Pronto para customização  
**Versão Hermes:** 0.14.0

---

## ✅ Concluído

- [x] Fork completo de https://github.com/NousResearch/hermes-agent
- [x] Push para https://github.com/olga-ai-lab/88i-sinistro-harness
- [x] Clone local em `~/Projects/88i-sinistro-harness`
- [x] Setup venv + pip install -e .
- [x] Verificado: `hermes --version` OK
- [x] Tools verificadas: 20+ toolsets disponíveis
- [x] Criado PLANO_CUSTOMIZACAO_88I.md (guia detalhado)
- [x] Criado README_88I.md (próximos passos)

---

## 📂 Estrutura

```
~/Projects/88i-sinistro-harness/
├── run_agent.py              # Core agent
├── cli.py                    # CLI interactive
├── model_tools.py            # Tool orchestration
├── toolsets.py               # Toolset definitions
├── tools/                    # 40+ built-in tools
├── skills/                   # Built-in skills (extensível)
├── plugins/                  # Plugin system (extensível)
├── gateway/                  # Messaging gateway
├── tests/                    # ~17k pytest tests
├── .venv/                    # Virtual environment (Python 3.13.2)
├── PLANO_CUSTOMIZACAO_88I.md # ← Leia isto
├── README_88I.md             # ← Próximos passos
└── SETUP_SUMMARY.md          # Este arquivo
```

---

## 🚀 Próximos Passos (Em Ordem)

### 1. Leia o Plano (5 min)
```bash
cd ~/Projects/88i-sinistro-harness
cat PLANO_CUSTOMIZACAO_88I.md
```

### 2. Crie Primeira Skill (sinistro-analyzer) [30 min]
```bash
source .venv/bin/activate
mkdir -p skills/seguros/sinistro-analyzer
# Edite skills/seguros/sinistro-analyzer/SKILL.md
```

### 3. Crie Custom Tool (sinistro_tools.py) [1-2h]
```bash
touch tools/sinistro_tools.py
# Integre com BAML, Supabase, Inngest
```

### 4. Setup Config Local [10 min]
```bash
cat README_88I.md # veja seção "Setup Config Local"
```

### 5. Teste E2E [30 min]
```bash
hermes /sinistro-analyzer
# ou
hermes  # CLI interativa (precisa ANTHROPIC_API_KEY)
```

---

## 🔧 Remotes Git

```
origin   → https://github.com/olga-ai-lab/88i-sinistro-harness.git (seu repo)
upstream → https://github.com/NousResearch/hermes-agent.git (sync)
```

Manter em sync:
```bash
git fetch upstream
git merge upstream/main
git push origin main
```

---

## 📊 Recursos Disponíveis

**Tools que já estão prontos:**
- terminal (shell scripts)
- code_execution (Python REPL)
- browser (automação web)
- delegate_task (spawn subagents)
- cronjob (scheduler)
- file operations
- web search
- image generation
- text-to-speech
- e 10+ mais

**Skills que já estão prontos:**
- github workflows
- research (arxiv, blogs)
- devops (kanban, CI/CD)
- email, calendar, drives
- e 50+ mais (veja `hermes skills list`)

**Plugins já prontos:**
- Memory (honcho, mem0)
- Model providers (anthropic, openrouter)
- Context engines
- Observability (W&B, Langfuse)

---

## 🎯 5 Pontos de Customização

1. **Skills personalizadas** (skills/seguros/) — FÁCIL
2. **Custom tools** (tools/sinistro_tools.py) — MÉDIO
3. **Plugins** (plugins/seguros-context-engine/) — MÉDIO
4. **System prompt** (~/.hermes/config.yaml) — TRIVIAL
5. **Gateway + WhatsApp** (gateway/platforms/) — DIFÍCIL

Comece pelos #1 e #2.

---

## 🐛 Troubleshooting

**Problema:** `command not found: hermes`
```bash
source .venv/bin/activate  # Ativar venv
```

**Problema:** `ANTHROPIC_API_KEY not set`
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Ou adicione em ~/.hermes/.env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> ~/.hermes/.env
```

**Problema:** Import error ao editar code
```bash
# Reinstale em modo editable
pip install -e .
```

---

## 📞 Suporte

- **Docs:** https://hermes-agent.nousresearch.com/docs
- **GitHub:** https://github.com/NousResearch/hermes-agent
- **AGENTS.md:** Tech guide detalhado (./AGENTS.md)

---

**Setup realizado por Hermes Agent**  
**Próxima sessão: Skills + Custom Tools**
