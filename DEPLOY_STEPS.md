# 🚀 DEPLOY OCTA — PASSO-A-PASSO COMPLETO

**Status:** 🟢 PRONTO PARA DEPLOY  
**Data:** 27 maio 2026  
**Tempo estimado:** 30-45 minutos (setup + validation)

---

## ⏱️ TIMELINE

```
T+0min  ← Você está aqui
T+5min  — Render.com configurado + build iniciado
T+15min — Build completo + deploy em produção
T+20min — Health check OK
T+30min — Todos endpoints validados
T+45min — Pronto para go-live gradual
```

---

## 📋 CHECKLIST PRÉ-DEPLOY

Antes de começar, verifique:

- [ ] Você tem acesso ao Render.com (https://dashboard.render.com)
- [ ] Você tem acesso ao GitHub (olga-ai-lab/88i-sinistro-harness)
- [ ] Você tem valores para variáveis de ambiente (Anthropic, Inngest, etc.)
- [ ] Você tem acesso ao Supabase ou outro DB PostgreSQL
- [ ] Você tem Slack aberto para comunicações (#octa-launch)

---

## 🎯 OS 5 PASSOS DO DEPLOY

### PASSO 1: Conectar Render.com (5 minutos)

**URL:** https://dashboard.render.com

**Instruções:**

1. Login no Render.com (ou crie conta)
2. Clique **New +** → **Web Service**
3. Clique **Deploy an existing repo from GitHub**
4. Pesquise: `olga-ai-lab/88i-sinistro-harness`
5. Clique **Connect**

**Configuração:**

```
Name:              octa-sinistro-harness
Runtime:           Docker
Region:            Ohio
Plan:              Standard ($12/mês, 2 vCPU, 4GB)
Dockerfile:        ./Dockerfile
Auto-deploy:       ON
```

**Clique:** Create Web Service

⏳ Render começará o build (aguarde 5-10 minutos)

---

### PASSO 2: Configurar Variáveis de Ambiente (10 minutos)

Enquanto o build roda, prepare as variáveis de ambiente:

1. **Vá para:** Settings → Environment Variables
2. **Clique:** Add Environment Variable

Adicione (copie exatamente seus valores reais):

```
ANTHROPIC_API_KEY          = sk-ant-[seu-valor]
INNGEST_API_KEY            = evt-[seu-valor]
INNGEST_SIGNING_KEY        = signkey-[seu-valor]
LANGFUSE_PUBLIC_KEY        = pk-[seu-valor]
LANGFUSE_SECRET_KEY        = sk-[seu-valor]
SUPABASE_URL               = https://[seu-project].supabase.co
SUPABASE_ANON_KEY          = eyJ[seu-valor]
DATABASE_URL               = postgresql://[sua-string]
PORT                       = 3000
NODE_ENV                   = production
LOG_LEVEL                  = info
PYTHONUNBUFFERED           = 1
```

⚠️ **IMPORTANTE:** Esses valores NÃO devem estar no repositório Git!

---

### PASSO 3: Aguardar Deploy (10 minutos)

**No Render Dashboard:**

1. Vá para **Logs** e aguarde ver:

```
✅ Build starting...
✅ pip install -r requirements.txt
✅ Building Docker image...
✅ Pushing image to registry...
✅ Deploying new service...
✅ ==> Your service is live!
```

2. Copie a **URL do seu serviço:**
```
https://octa-sinistro-harness.onrender.com
```

Se vir erro, verifique:
- ❌ requirements.txt tem todos os pacotes
- ❌ Dockerfile está correto
- ❌ main.py tem @app.get("/health")

---

### PASSO 4: Validar Health Check (5 minutos)

Depois que deploy está "Live":

```bash
# Terminal local
RENDER_URL="https://octa-sinistro-harness.onrender.com"

# Test 1: Health
curl $RENDER_URL/health

# Esperado:
# {"status": "healthy", "version": "1.0.0"}

# Test 2: Extract
curl -X POST $RENDER_URL/extract \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "TEST-001", "type": "AP"}'

# Test 3: Fraud
curl -X POST $RENDER_URL/fraud \
  -H "Content-Type: application/json" \
  -d '{"claim_amount": 5000}'
```

Se tudo retornar 200 OK → ✅ Go!

Se retornar 404 → ❌ FastAPI não iniciou
- Verifique: `python main.py` localmente
- Verifique imports e dependências

---

### PASSO 5: Executar Script de Validação (10 minutos)

Após health checks OK:

```bash
# Clone/pull o repositório
cd ~/Projects/88i-sinistro-harness

# Execute validation script
./scripts/validate_render_deployment.sh https://octa-sinistro-harness.onrender.com

# Output esperado:
# ✅ Health endpoint
# ✅ Extract endpoint
# ✅ Fraud detection
# ✅ Routing endpoint
# ✅ Performance checks
```

---

## 📊 O QUE ESPERAR VER

### Render Dashboard

**Status:** "Live" (verde) ✅

**Logs mostram:**
```
INFO:     Uvicorn running on http://0.0.0.0:3000
INFO:     Application startup complete
```

**Metrics:**
- CPU: < 50% nominal
- Memory: < 500MB nominal
- Requests: começando a aumentar

### Langfuse (opcional, mas recomendado)

Se tiver Langfuse configurado:
- Vá para: https://langfuse.com/projects/octa
- Deve mostrar: primeiros traces/calls

### Prometheus (opcional)

Se tiver Prometheus:
- Deve mostrar: métricas começando a coletar

---

## 🚨 PROBLEMAS COMUNS

### "Build Failed"

**Causa:** requirements.txt ou Dockerfile inválido

```
Solução:
1. Clique "Retry" no Render
2. Ou faça git push de novo (com correção)
3. Render auto-redeploya
```

### "Service unhealthy"

**Causa:** Variáveis de ambiente faltando ou erro em main.py

```
Solução:
1. Verifique variáveis de ambiente estão setadas
2. Verifique logs em Render Dashboard
3. Teste: python main.py (local)
4. Clique "Restart Service" no Render
```

### "Port not accessible"

**Causa:** PORT não configurada como env var

```
Solução:
1. Verifique main.py: port = int(os.getenv('PORT', 3000))
2. Adicione PORT = 3000 nas env vars do Render
3. Redeploy
```

---

## ✅ CHECKLIST DE CONCLUSÃO

- [ ] Render.com conta criada e repo conectado
- [ ] Build completo (status "Live")
- [ ] Variáveis de ambiente setadas
- [ ] Health check OK (curl /health → 200)
- [ ] Extract endpoint OK
- [ ] Fraud endpoint OK
- [ ] Validation script executado com sucesso
- [ ] Langfuse coletando traces (opcional)
- [ ] Prometheus coletando métricas (opcional)
- [ ] URL do Render anotada: ________________

---

## 📞 PRÓXIMOS PASSOS

✅ Deploy completo? Parabéns! Você alcançou **PASSO 3 de 5**

Próximo:
- **PASSO 4:** Testes com sinistro sample real
- **PASSO 5:** Go-live gradual (10% → 50% → 100%)

Ver documentação:
- `DEPLOY_RUNBOOK.md` — Procedimento completo
- `GO_NOGO_CHECKLIST.md` — Go/no-go decision
- `RENDER_DEPLOYMENT_GUIDE.md` — Guia detalhado Render

---

**Precisa de ajuda?**
- Render docs: https://render.com/docs
- Slack: #octa-launch
- Escalation: @cto

**Tempo decorrido:** ⏱️ Conte quanto levou!

---

**Status Final:** 🟢 DEPLOY COMPLETO

Você está pronto para o **PASSO 4: Testes Pós-Deploy**
