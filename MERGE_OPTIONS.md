# Git Merge Decision — 88i Sinistro Harness

**Encontradas 3 branches com seu trabalho anterior**

---

## Opção A: MERGE (Recomendado)

Integra o trabalho das 7 semanas + Railway + FNOL runner.

```bash
# 1. Criar branch de integração
git checkout -b feature/integrate-previous-work

# 2. Merge em ordem
git merge origin/railway/fix-deploy-d5a293 -m "merge: integrate railway deploy work"

git merge origin/codex/investigate-railway-agent-access-issue \
  -m "merge: integrate olga mvp integration"

git merge origin/codex/investigate-railway-agent-access-issue-h6q8vq \
  -m "merge: integrate fnol-to-olga flow runner"

# 3. Resolver conflitos (se houver)
# git status para ver arquivos em conflito
# Editar, depois: git add <arquivo> && git commit

# 4. Push
git push -u origin feature/integrate-previous-work

# 5. Merge pra main (após revisar)
git checkout main
git merge feature/integrate-previous-work
git push origin main
```

**Benefícios:**
- ✓ Reutiliza Docker + Railway config
- ✓ Herda 7 semanas de features (semana1-7)
- ✓ FNOL runner já implementado
- ✓ Langfuse integration + eval dataset
- ✓ Shadow mode + multi-plataforma

**Riscos:**
- Pode ter conflitos (improvável, branches antigos)
- Arquivo de docs pode duplicar

---

## Opção B: DELETE (Começar Fresh)

Remove branches antigos e descarta tudo.

```bash
# Deletar branches remotas
git push origin --delete railway/fix-deploy-d5a293
git push origin --delete codex/investigate-railway-agent-access-issue
git push origin --delete codex/investigate-railway-agent-access-issue-h6q8vq

# Deletar localmente (se estivessem clonadas)
git branch -D railway/fix-deploy-d5a293
git branch -D codex/investigate-railway-agent-access-issue
git branch -D codex/investigate-railway-agent-access-issue-h6q8vq
```

**Benefícios:**
- ✓ Começa 100% fresh
- ✓ Menos confusão na história git
- ✓ Foco no novo Hermes fork

**Riscos:**
- Perder Dockerfile + railway.json (precisa refazer)
- Perder 7 semanas de features
- Perder FNOL runner (refazer tudo)

---

## Opção C: REVISAR ANTES

Ver em detalhe o que cada branch contém antes de decidir.

```bash
# Ver Dockerfile do branch
git show origin/railway/fix-deploy-d5a293:Dockerfile | head -50

# Ver railway.json
git show origin/railway/fix-deploy-d5a293:railway.json

# Listar arquivos novos/modificados
git diff --name-status origin/main..origin/railway/fix-deploy-d5a293

# Ver commits em detalhe
git log origin/main..origin/railway/fix-deploy-d5a293 --format='%h %s' --patch

# Diff específico (ex: arquivos Python)
git diff origin/main..origin/railway/fix-deploy-d5a293 -- '*.py' | head -100
```

---

## Recomendação

🟢 **MERGE (Opção A)**

Por quê:
1. Você investiu 7 semanas nisso (semana1-7 Octa)
2. Dockerfile + railway.json são valiosos (avoid rewrite)
3. FNOL runner já está pronto pra usar
4. Langfuse integration já feita
5. Shadow mode (SHADOW/CANARY/CUTOVER) já implementado
6. Conflicts improvável (branches de meses atrás)

Depois de merge, você pode:
- Criar Phase 1-5 em cima do trabalho anterior
- Reutilizar Dockerfile pra deploy
- Adaptar FNOL runner pra Hermes fork
- Estender skills/tools com novo Hermes architecture

---

## Qual opção você prefere?

Responda com:
- **A** — Fazer merge (integrar trabalho anterior)
- **B** — Delete (começar fresh)
- **C** — Revisar primeiro (ver em detalhe)

Aguardando sua decisão! 🚀
