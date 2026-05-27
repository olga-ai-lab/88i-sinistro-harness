# 88i Sinistro Harness — Agente de Análise de Sinistros

**Fork Hermes customizado para 88i Seguradora Digital**

- 📦 Repositório: https://github.com/olga-ai-lab/88i-sinistro-harness
- 🔗 Upstream: https://github.com/NousResearch/hermes-agent (sync disponível)
- 🎯 Escopo: Last Mile Delivery (AP, DITA, Impedimento ao Trabalho)
- ⚡ Stack: BAML + LangGraph + Inngest + FastAPI
- 📊 Volume: 33k sinistros/mês

---

## Setup Local (Já Pronto ✓)

```bash
cd ~/Projects/88i-sinistro-harness
source .venv/bin/activate

# Verificar versão
hermes --version
# Output: Hermes Agent v0.14.0 (2026.5.16)
```

**Dependências instaladas:** 35+ packages (openai, pydantic, rich, httpx, fire, etc.)

---

## Próximos Passos

### 1️⃣ Leia o Plano de Customização
```bash
cat PLANO_CUSTOMIZACAO_88I.md
```

Ele detalha:
- Estrutura do projeto
- 5 pontos de customização principais
- Roadmap em 5 fases
- Comandos essenciais

### 2️⃣ Teste o Hermes Básico
```bash
# Ativar venv (se não estiver)
source .venv/bin/activate

# Rodar agent interativo (CLI)
hermes --help

# Ou iniciar uma conversa (precisa ANTHROPIC_API_KEY)
hermes
```

### 3️⃣ Comece com Skills (Recomendado)

Skills são módulos reutilizáveis. Criar um é trivial:

```bash
# Criar skill de análise de sinistros
mkdir -p skills/seguros/sinistro-analyzer

# Criar arquivo SKILL.md
cat > skills/seguros/sinistro-analyzer/SKILL.md << 'EOF'
---
name: sinistro-analyzer
description: "Analisa documentação de sinistro, extrai campos-chave, detecta inconsistências."
version: 1.0.0
author: Olga AI
---

# Sinistro Analyzer

Extrai informações de sinistros de Last Mile Delivery.

## Uso

```
/sinistro-analyzer extrair ~/documento-sinistro.pdf
/sinistro-analyzer validar {"id_sinistro": "...", "tipo": "AP"}
```

## Features

- Extração automática de campos (data, valor, tipo)
- Validação contra business rules 88i
- Detecção de inconsistências

## Pitfalls

- PDF scaneado: considere OCR
- Tipos aceitos: AP, DITA, Impedimento
EOF
```

Depois adicione scripts:
```bash
mkdir -p skills/seguros/sinistro-analyzer/scripts

cat > skills/seguros/sinistro-analyzer/scripts/extract_fields.py << 'EOF'
#!/usr/bin/env python3
"""Extract sinistro fields from document."""

import json
import sys

def extract(doc_path: str) -> dict:
    """Extract sinistro metadata."""
    # TODO: BAML integration
    return {
        "id_sinistro": "...",
        "tipo": "AP|DITA|Impedimento",
        "data_sinistro": "YYYY-MM-DD",
        "valor": 0.0,
        "status": "validado|inconsistência|fraude"
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: extract_fields.py <doc_path>")
        sys.exit(1)
    result = extract(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
EOF

chmod +x skills/seguros/sinistro-analyzer/scripts/extract_fields.py
```

### 4️⃣ Integre com BAML

Hermes suporta:
- **Terminal tool** pra rodar scripts
- **Code execution** pra rodar Python
- **Delegate tool** pra chamar subagents

Para integrar BAML:

```python
# tools/sinistro_tools.py
from tools.registry import register
import subprocess
import json

@register("sinistro_analyzer")
def analyze_sinistro(claim_id: str, document_path: str) -> dict:
    """Analyze sinistro using BAML."""
    # Rodar BAML CLI ou Python SDK
    result = subprocess.run([
        "bun", "run", "src/index.ts",
        "--claim-id", claim_id,
        "--doc", document_path
    ], capture_output=True, text=True)
    
    return json.loads(result.stdout)
```

### 5️⃣ Setup Config Local

```bash
# Criar ~/.hermes/config.yaml customizado
mkdir -p ~/.hermes

cat > ~/.hermes/config.yaml << 'EOF'
ai:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
  system_prompt: |
    Você é o Octa, agente sênior de sinistros da 88i Seguradora Digital.
    
    Especialista em sinistros de Last Mile Delivery:
    - AP (Acidentes Pessoais)
    - DITA (Dano Intencional Total ou Acidental)
    - Impedimento ao Trabalho
    
    Objetivo: análise rápida (4-6h), detecção de fraude, extração de campos.
    Cliente: CloudWalk/InfinitePay (33k sinistros/mês).

tools:
  enabled_toolsets:
    - terminal
    - code_execution
    - browser
    - delegate_task
    - cronjob
  
logging:
  level: "INFO"

display:
  skin: "minimal"  # ou "default", "neon", etc.

gateway:
  enabled: false  # Ativar quando ready pra WhatsApp

EOF
```

---

## Git Workflow

```bash
# Criar branch de feature
git checkout -b feature/sinistro-analyzer

# Editar, commit
git add skills/seguros/sinistro-analyzer/
git commit -m "feat: add sinistro-analyzer skill"

# Push pro seu repo
git push -u origin feature/sinistro-analyzer

# Depois, criar PR ou merge direto pra main
git checkout main
git merge feature/sinistro-analyzer
git push origin main

# Manter em sync com Hermes original
git fetch upstream
git merge upstream/main
git push origin main
```

---

## Estrutura de Diretórios Customizados

Depois de Phase 1-2, você terá:

```
~/Projects/88i-sinistro-harness/
├── skills/seguros/                     [NOVO — Phase 1]
│   ├── sinistro-analyzer/              [NOVO]
│   ├── fraude-detector/                [NOVO]
│   └── 88i-sinistro-process/           [NOVO]
│
├── tools/                              [ESTENDIDO — Phase 2]
│   ├── sinistro_tools.py               [NOVO]
│   ├── supabase_tool.py                [NOVO]
│   ├── inngest_tool.py                 [NOVO]
│   └── <tools originais Hermes>
│
├── plugins/seguros-context-engine/     [NOVO — Phase 3]
│   ├── __init__.py
│   ├── supabase_context.py
│   └── dashboard/
│
├── ~/.hermes/config.yaml               [CUSTOMIZADO]
│
├── PLANO_CUSTOMIZACAO_88I.md           [ESTE ARQUIVO ↑]
└── <código Hermes original>
```

---

## Comandos Úteis

```bash
# Ativar venv
source .venv/bin/activate

# Rodar agent (CLI interativa)
hermes

# Ver skills disponíveis
hermes skills list

# Usar uma skill (após criar)
hermes /sinistro-analyzer

# Ver logs
hermes logs --follow

# Rodar testes
python -m pytest tests/ -v

# Checar estrutura
hermes tools

# Atualizar Hermes (do upstream)
git fetch upstream
git merge upstream/main
```

---

## Suporte + Referências

- **Hermes Docs:** https://hermes-agent.nousresearch.com/docs
- **GitHub:** https://github.com/NousResearch/hermes-agent
- **AGENTS.md (tech guide):** ./AGENTS.md na raiz do projeto
- **API Docs:** ./website/ (Docusaurus)

---

## Next Session Checklist

- [ ] Ler `PLANO_CUSTOMIZACAO_88I.md`
- [ ] Criar primeira skill (`sinistro-analyzer`)
- [ ] Testar skill via CLI: `hermes /sinistro-analyzer`
- [ ] Criar `tools/sinistro_tools.py`
- [ ] Integrar BAML (seu workflow)
- [ ] Setup `.hermes/config.yaml` com system prompt customizado

---

**Status:** Pronto para customização ✓
**Data setup:** 27 de maio de 2026
**Próximo:** Skills + Custom Tools (Phase 1-2)
