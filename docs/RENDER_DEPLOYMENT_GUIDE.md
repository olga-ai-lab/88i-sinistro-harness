# 🚀 GUIA DE DEPLOY — RENDER.COM

**Projeto:** 88i Sinistro Harness (Octa)  
**Data:** 27 maio 2026  
**Região:** Ohio (us-east-1 equivalent)  
**Instâncias:** 1 (auto-scaling 1-3)

---

## PASSO 1: Conectar GitHub ao Render.com

1. Acesse https://dashboard.render.com
2. Clique em **New +** → **Web Service**
3. Selecione **Deploy an existing repo from GitHub**
4. Procure por: `olga-ai-lab/88i-sinistro-harness`
5. Clique em **Connect**

---

## PASSO 2: Configurar Serviço

Na tela de configuração do novo serviço:

### Nome e Configuração

```
Name: octa-sinistro-harness
Region: Ohio
Runtime: Docker
Plan: Standard ($12/mês, 2 vCPU, 4GB RAM)
```

### Build Settings

```
Root Directory: .
Dockerfile Path: ./Dockerfile
Build Command: (deixar vazio - Docker cuida)
Start Command: python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables

Clique em **Advanced** → **Environment**

Adicione (vai adicionar durante o deploy):

```
PORT = 3000
NODE_ENV = production
LOG_LEVEL = info
PYTHONUNBUFFERED = 1
```

---

## PASSO 3: Adicionar Variáveis de Ambiente Sensíveis

Depois do deploy inicial, vá para **Settings** → **Environment Variables** e adicione:

```
ANTHROPIC_API_KEY = sk-ant-[seu-valor]
INNGEST_API_KEY = evt-[seu-valor]
INNGEST_SIGNING_KEY = signkey-[seu-valor]
LANGFUSE_PUBLIC_KEY = pk-[seu-valor]
LANGFUSE_SECRET_KEY = sk-[seu-valor]
SUPABASE_URL = https://[seu-project].supabase.co
SUPABASE_ANON_KEY = eyJ[seu-valor]
DATABASE_URL = postgresql://[seu-valor]
```

⚠️ **NUNCA** comite .env com valores reais!

---

## PASSO 4: Deploy Inicial

1. Clique em **Create Web Service**
2. Render começará a fazer build (aguarde 5-10 minutos)
3. Você verá logs em tempo real

### Sinais de Sucesso

```
✅ Build successful
✅ Deploying...
✅ ==> Your service is live!
✅ URL: https://octa-sinistro-harness.onrender.com
```

### Sinais de Erro

```
❌ Build failed
   → Verifique requirements.txt
   → Verifique Dockerfile
   → Verifique logs

❌ Service not starting
   → Erro em main.py
   → Porta não configurada corretamente
   → Variáveis de ambiente faltando
```

---

## PASSO 5: Health Check Imediato

Após deploy bem-sucedido:

```bash
# Substitua pela URL do seu Render
RENDER_URL="https://octa-sinistro-harness.onrender.com"

# Health check
curl -v $RENDER_URL/health

# Esperado:
# HTTP/1.1 200 OK
# {"status": "healthy", "version": "1.0.0"}
```

Se retornar **404**, significa que FastAPI não iniciou corretamente. Verifique:
- `main.py` está correto
- `requirements.txt` tem todas as dependências
- `PORT` está setado como 3000

---

## PASSO 6: Validar Endpoints

```bash
# Extract endpoint
curl -X POST $RENDER_URL/extract \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "TEST001", "type": "AP"}'

# Fraud detection
curl -X POST $RENDER_URL/fraud \
  -H "Content-Type: application/json" \
  -d '{"claim_amount": 5000}'

# Routing
curl -X POST $RENDER_URL/route \
  -H "Content-Type: application/json" \
  -d '{"claim_type": "AP"}'
```

**Critério de GO:** Todos retornam 200 com JSON válido

---

## PASSO 7: Monitorar Deploy

### Dashboard Render

- **Logs:** Clique em **Logs** para ver output em tempo real
- **Metrics:** CPU, Memory, Requests, etc.
- **Deployments:** Ver histórico de deploys

### Health Status

Render verifica `/health` a cada 30 segundos. Se falhar 3x consecutivas, serviço é marcado como "unhealthy".

---

## ROLLBACK (Se necessário)

1. Acesse **Deployments** no Render
2. Clique no deployment anterior (seta verde ✅)
3. Clique em **Re-deploy**
4. Aguarde até status "Live"

Ou via Git:
```bash
git revert [hash-do-commit-ruim]
git push origin main
# Render auto-deploya em segundos
```

---

## TROUBLESHOOTING

### "Build failed"

```
Error: pip install failed
→ Verifique requirements.txt para typos
→ Teste localmente: pip install -r requirements.txt

Error: Docker image too large
→ Optimize Dockerfile
→ Use .dockerignore para excluir arquivos grandes
```

### "Service not starting"

```
Error: Port not available
→ Render seta PORT via env var, não hardcode em main.py
→ Use: port = int(os.getenv('PORT', 3000))

Error: Module not found
→ Faltam dependências em requirements.txt
→ Teste: pip install -r requirements.txt
```

### "/health returns 404"

```
Possível causa: FastAPI não iniciou
→ Verifique main.py tem @app.get("/health")
→ Verifique imports estão corretos
→ Check Dockerfile CMD

Solução: Adicionar logs
→ Render mostra stdout/stderr
→ Adicione print() em main.py para debug
```

---

## PRÓXIMO PASSO

Após deploy bem-sucedido:

1. ✅ Health check OK
2. ✅ Endpoints respondendo
3. ⏭️ Ir para **PASSO 4: TESTES PÓS-DEPLOY**

Ver: `DEPLOY_RUNBOOK.md` seção "VALIDAÇÃO (T+30min até T+1hr)"

---

**Versão:** 1.0.0  
**Status:** Production-Ready  
**Tempo esperado:** 15-20 minutos
