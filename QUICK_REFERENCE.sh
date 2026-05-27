#!/bin/bash
# Quick Reference — 88i Sinistro Harness Commands

# ============================================================================
# ENVIRONMENT
# ============================================================================

# Ativar venv
cd ~/Projects/88i-sinistro-harness && source .venv/bin/activate

# Verificar versão
hermes --version

# ============================================================================
# DESENVOLVIMENTO
# ============================================================================

# Criar primeira skill
mkdir -p skills/seguros/sinistro-analyzer
cat > skills/seguros/sinistro-analyzer/SKILL.md << 'EOF'
---
name: sinistro-analyzer
description: "Analyzes insurance claim documents, extracts key fields."
version: 1.0.0
author: 88i
---

# Sinistro Analyzer

Extract fields from insurance claims.

## Usage

/sinistro-analyzer extract ~/documento.pdf

EOF

# Criar custom tool
touch tools/sinistro_tools.py

# Setup config local
mkdir -p ~/.hermes
cat > ~/.hermes/config.yaml << 'EOF'
ai:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
  system_prompt: |
    Você é Octa, agente sênior de sinistros 88i.
    
    Especialista em: AP, DITA, Impedimento ao Trabalho
    Objetivo: análise rápida (4-6h), detecção fraude
    Cliente: CloudWalk/InfinitePay (33k/mês)

tools:
  enabled_toolsets:
    - terminal
    - code_execution
    - browser
    - delegate_task
    - cronjob

EOF

# ============================================================================
# TESTING
# ============================================================================

# Rodar agent interativo (precisa ANTHROPIC_API_KEY)
hermes

# Rodar skill específica
hermes /sinistro-analyzer

# Listar tools
hermes tools list

# Listar skills
hermes skills list

# Ver logs
hermes logs --follow

# Rodar testes
python -m pytest tests/ -v

# ============================================================================
# GIT OPERATIONS
# ============================================================================

# Criar branch de feature
git checkout -b feature/sinistro-analyzer

# Commit
git add .
git commit -m "feat: add sinistro-analyzer skill"

# Push
git push -u origin feature/sinistro-analyzer

# Merge pra main
git checkout main
git merge feature/sinistro-analyzer
git push origin main

# Sincronizar com upstream Hermes
git fetch upstream
git merge upstream/main
git push origin main

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Se pip install falhar
pip install --upgrade pip setuptools wheel
pip install -e .

# Se import error
python -c "import hermes_agent; print('OK')"

# Se tool não aparece na lista
python -m tools.registry  # check auto-discovery

# Limpar cache Python
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# ============================================================================
# ÚTIL
# ============================================================================

# Ver estrutura
tree -L 2 -I '__pycache__|*.pyc|.git' .

# Contar linhas de código
find . -name "*.py" -type f | xargs wc -l | tail -1

# Buscar função no codebase
grep -r "def sinistro_" tools/ | head -5

# Status git
git status
git log --oneline -10

# ============================================================================
# DEPLOYMENT (Phase 5)
# ============================================================================

# Build Docker
docker build -t 88i-sinistro:latest .

# Deploy Render
# (confira PLANO_CUSTOMIZACAO_88I.md seção Deploy)

# ============================================================================
# DOCUMENTAÇÃO
# ============================================================================

# Ler plano de customização
cat PLANO_CUSTOMIZACAO_88I.md

# Ler próximos passos
cat README_88I.md

# Ler sumário do setup
cat SETUP_SUMMARY.md

# Ler tech guide Hermes
cat AGENTS.md | head -200

# ============================================================================
