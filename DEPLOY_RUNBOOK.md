# 🚀 RUNBOOK DE DEPLOY — OCTA (88i Sinistro Harness)

## PRÉ-DEPLOY (T-60min)

### 1. Validar Testes
```bash
cd ~/Projects/88i-sinistro-harness
pytest tests/pre_launch/ -v --tb=short
pytest tests/ -q --co | wc -l  # Deve ter 1317+ testes
```

**Critério de GO:** ✅ Todos passando (90%+ coverage)

### 2. Validar Segurança
```bash
./scripts/pre_launch_security.sh
```

**Checklist:**
- [ ] Trivy container scan (0 críticas)
- [ ] Safety dependencies (0 vulneráveis)
- [ ] Git secrets não encontrados
- [ ] API keys validadas
- [ ] Encryption verificada (AES-256)
- [ ] HSTS/CSP headers OK
- [ ] Rate limit rules OK (1000 req/min)
- [ ] Backup validado
- [ ] PITR status OK

### 3. Validar Performance
```bash
./scripts/pre_launch_performance.sh
```

**SLAs:**
- [ ] Extract latency P95 < 100ms
- [ ] Fraud score latency P95 < 150ms
- [ ] Context injection latency P95 < 50ms
- [ ] Plugin load latency P95 < 200ms
- [ ] State save latency P95 < 300ms

### 4. Sign-Off (6 papéis)
```bash
# Edite docs/SIGN_OFF_FORM.md
# Cada papel tem 10 checklist items
# Todos devem assinar ✅
```

**Papéis:**
- [ ] Dev Lead (fidelidade código)
- [ ] DevOps Lead (infraestrutura)
- [ ] Security Lead (OWASP Top 10)
- [ ] Product Manager (requisitos negócio)
- [ ] Ops Manager (runbooks)
- [ ] CTO (aprovação final)

---

## DEPLOY (T-0 até T+30min)

### PASSO 1: Preparar Render.com

1. Acesse https://dashboard.render.com
2. Clique em **New Service** → **Web Service**
3. Conecte GitHub: `olga-ai-lab/88i-sinistro-harness`
4. Configuração:
   ```
   Name: octa-sinistro-harness
   Runtime: Python 3.13
   Build: pip install -r requirements.txt
   Start: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
   Plan: Standard (2 CPU, 4GB)
   Region: us-east-1
   ```

### PASSO 2: Configurar Variáveis de Ambiente

No Render Dashboard → **Environment Variables**, adicione:

```
ANTHROPIC_API_KEY=sk-ant-[SEUS_VALORES]
INNGEST_API_KEY=evt-[SEUS_VALORES]
INNGEST_SIGNING_KEY=signkey-[SEUS_VALORES]
LANGFUSE_PUBLIC_KEY=pk-[SEUS_VALORES]
LANGFUSE_SECRET_KEY=sk-[SEUS_VALORES]
SUPABASE_URL=https://[seu-project].supabase.co
SUPABASE_ANON_KEY=eyJ[SEUS_VALORES]
DATABASE_URL=postgresql://[DADOS_SUPABASE]
PORT=3000
NODE_ENV=production
LOG_LEVEL=info
```

⚠️ **IMPORTANTE:** NÃO use `.env` local! Render não vê arquivos.

### PASSO 3: Deploy Inicial

```bash
# No Render Dashboard:
# 1. Clique "Deploy"
# 2. Aguarde logs de build
# 3. Deve ver: "INFO:     Uvicorn running on http://0.0.0.0:3000"
```

### PASSO 4: Health Check Imediato

```bash
# Substitua pela URL do seu Render
RENDER_URL="https://octa-sinistro-harness.onrender.com"

# Health check
curl -v $RENDER_URL/health

# Deve retornar:
# HTTP/1.1 200 OK
# {"status": "healthy", "version": "1.0.0"}
```

**Critério de GO:** Status 200 OK ✅

### PASSO 5: Validar Endpoints

```bash
# Extract endpoint
curl -X POST $RENDER_URL/extract \
  -H "Content-Type: application/json" \
  -d '{"claim_id": "TEST001", "data": {...}}'

# Fraud detection
curl -X POST $RENDER_URL/fraud \
  -H "Content-Type: application/json" \
  -d '{"claim_amount": 5000, "customer_age": 35}'

# Routing
curl -X POST $RENDER_URL/route \
  -H "Content-Type: application/json" \
  -d '{"claim_type": "AP", "region": "SP"}'
```

**Critério de GO:** Todos retornam 200 ✅

---

## VALIDAÇÃO (T+30min até T+1hr)

### TESTE COM SINISTRO SAMPLE

```bash
# Use um sinistro de teste real (ID sensível mascarado)
CLAIM_ID="TEST-2026-05-27-001"

curl -X POST $RENDER_URL/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer [API_KEY]" \
  -d '{
    "claim_id": "'$CLAIM_ID'",
    "type": "AP",
    "amount": 5000,
    "customer_id": "TEST-CUST-001",
    "days_insured": 1095,
    "region": "SP"
  }' | jq .

# Valide na resposta:
# - extraction_status: "success"
# - fraud_score: entre 0-1
# - fraud_risk: "low" ou "high"
# - recommended_route: "AP" ou "DITA" ou "Impedimento"
```

### MONITORAMENTO EM TEMPO REAL

```bash
# Langfuse Dashboard
# Acesse: https://langfuse.com/projects/octa
# Deve mostrar:
# - Traços de API calls
# - Token usage
# - Latências

# Prometheus
# Acesse: http://localhost:9090/graph
# ou via Render logs
# Deve mostrar:
# - octa_claims_processed_total
# - octa_extract_latency_ms
# - octa_fraud_score_latency_ms
```

**Critério de GO:** Métricas coletadas ✅

---

## PRODUÇÃO GRADUAL (T+1hr até T+24hr)

### FASE 1: 10% Tráfego (T+1hr)

```bash
# Configure load balancer (se aplicável)
# ou manualmente:
# - 10% de sinistros reais para OCTA
# - 90% ainda para sistema legado

# Monitorar:
# - Error rate (deve ser < 1%)
# - Latência P95 (deve ser < SLA)
# - Fraude scores (comparar com baseline)
```

### FASE 2: 50% Tráfego (T+6hr)

```bash
# Se tudo OK em Fase 1:
# - Aumentar para 50%
# - Verificar scaling automático (1-2 instâncias)
# - Alertas disparando? Responder rápido
```

### FASE 3: 100% Tráfego (T+12hr)

```bash
# Se tudo OK em Fase 2:
# - Full rollout para 100%
# - Desativar sistema legado (se desejado)
# - Monitoramento 24/7 ativo
```

---

## ROLLBACK (Se necessário)

```bash
# Render Dashboard → Deploy History
# Clique no deployment anterior
# Clique "Re-deploy"
# Aguarde até ter status "live"

# Ou via CLI:
# git revert [hash-do-commit-ruim]
# git push origin main
# Render auto-deploya
```

**Critério de ROLLBACK:**
- ❌ Error rate > 5% por 5 minutos
- ❌ Latência P95 > 3x SLA
- ❌ Database connection loss
- ❌ Fraude scores zerados (bug)

---

## CHECKLIST FINAL

- [ ] Todos testes passando
- [ ] Security scan OK (0 críticas)
- [ ] Performance SLAs validados
- [ ] 6 stakeholders assinados
- [ ] Render.com configurado
- [ ] Variáveis de ambiente setadas
- [ ] Health check OK
- [ ] Endpoints respondendo
- [ ] Sinistro sample processado
- [ ] Langfuse coletando
- [ ] Prometheus coletando
- [ ] On-call team confirmado
- [ ] Runbooks testados
- [ ] Rollback plan validado

---

## CONTATOS DE EMERGÊNCIA

| Papel | Nome | Slack | Telefone |
|-------|------|-------|----------|
| CTO | [CTO] | @cto | +55-11-XXXX-XXXX |
| DevOps Lead | [DEVOPS] | @devops | +55-11-XXXX-XXXX |
| On-Call (noite) | [ON-CALL] | @on-call | +55-11-XXXX-XXXX |

---

**Versão:** 1.0.0
**Data:** 27 mai 2026
**Status:** 🟢 Production-Ready
