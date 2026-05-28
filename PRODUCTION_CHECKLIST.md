# ✅ Checklist de Deployment — Octa 88i Sinistro

**Data:** May 27, 2026  
**Ambiente:** Render.com (Ohio)  
**Service ID:** srv-d8bo09cp3tds73als7u0

---

## FASE 1: Validação de Saúde ✅ Em Progresso

- [ ] **Passo 1.1** — `/health` endpoint responde 200 OK
  ```bash
  curl https://srv-d8bo09cp3tds73als7u0.onrender.com/health
  # Esperado: {"status": "ok"}
  ```

- [ ] **Passo 1.2** — `/health/live` (liveness probe) responde
  ```bash
  curl https://srv-d8bo09cp3tds73als7u0.onrender.com/health/live
  # Esperado: {"status": "alive"}
  ```

- [ ] **Passo 1.3** — `/health/ready` (readiness probe) responde
  ```bash
  curl https://srv-d8bo09cp3tds73als7u0.onrender.com/health/ready
  # Esperado: 200 ou 503 (dependendo de deps)
  ```

---

## FASE 2: Configuração de Ambiente

### Variáveis Obrigatórias

**IMPORTANTE:** Estas variáveis DEVEM ser adicionadas ao Render Dashboard (não ao `.env` local!)

#### 2.1 Anthropic API

- [ ] `ANTHROPIC_API_KEY`
  ```
  Value: sk-ant-v4-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  Scope: RUN
  ```
  
  Onde obter: https://console.anthropic.com/account/keys

#### 2.2 Supabase (Database)

- [ ] `SUPABASE_URL`
  ```
  Value: https://xxxxx.supabase.co
  Scope: RUN
  ```
  Onde obter: Painel Supabase → Settings → API

- [ ] `SUPABASE_ANON_KEY`
  ```
  Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  Scope: RUN
  ```
  Onde obter: Painel Supabase → Settings → API

#### 2.3 Inngest (Workflow Engine)

- [ ] `INNGEST_EVENT_KEY`
  ```
  Value: evt_prod_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  Scope: RUN
  ```
  Onde obter: https://app.inngest.com/settings/keys

- [ ] `INNGEST_SIGNING_KEY`
  ```
  Value: signkey_prod_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  Scope: RUN
  ```
  Onde obter: https://app.inngest.com/settings/keys

#### 2.4 Langfuse (Observability - OPCIONAL)

- [ ] `LANGFUSE_PUBLIC_KEY` (opcional)
  ```
  Value: pk-lf-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```
  Onde obter: https://cloud.langfuse.com/settings/keys

- [ ] `LANGFUSE_SECRET_KEY` (opcional)
  ```
  Value: sk-lf-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```
  Onde obter: https://cloud.langfuse.com/settings/keys

### Como Adicionar no Render

1. Ir para: https://dashboard.render.com/srv-d8bo09cp3tds73als7u0
2. Aba: **"Environment"**
3. Clicar: **"Add Environment Variable"**
4. Adicionar cada uma das chaves acima
5. Clicar: **"Save"** (Render auto-redeploy)

---

## FASE 3: Testes de Negócio

- [ ] **Passo 3.1** — POST /sinistro (teste simples)
  ```bash
  curl -X POST https://srv-d8bo09cp3tds73als7u0.onrender.com/sinistro \
    -H "Content-Type: application/json" \
    -d '{
      "narrativa": "Acidente de trânsito em São Paulo, SP. Colisão frontal entre dois veículos na Av. Paulista.",
      "cliente_id": "test-client-123"
    }'
  # Esperado: 200 com processamento ou 422 com erro de validação
  ```

- [ ] **Passo 3.2** — POST /sinistro (teste completo)
  ```bash
  curl -X POST https://srv-d8bo09cp3tds73als7u0.onrender.com/sinistro \
    -H "Content-Type: application/json" \
    -d '@test_payloads/sinistro_ap.json'
  # Validar resposta com extracted fields
  ```

- [ ] **Passo 3.3** — GET /api/status (status geral)
  ```bash
  curl https://srv-d8bo09cp3tds73als7u0.onrender.com/api/status
  # Esperado: JSON com status de integração
  ```

---

## FASE 4: Validação de SLAs

Target SLAs (segundo requirements):
- Extract: < 100ms
- Fraud score: < 150ms
- Context inject: < 50ms
- Plugin load: < 200ms
- State save: < 300ms

- [ ] **Passo 4.1** — Rodar script de validação
  ```bash
  cd ~/Projects/88i-deploy
  ./scripts/validate_live.sh https://srv-d8bo09cp3tds73als7u0.onrender.com
  ```

- [ ] **Passo 4.2** — Verificar response times em logs
  ```bash
  # No Render Dashboard → Logs
  # Procurar por: "latency_ms"
  ```

---

## FASE 5: Monitoring Setup

### 5.1 Prometheus (Métricas)

- [ ] Endpoints de métricas configurados
  ```bash
  curl https://srv-d8bo09cp3tds73als7u0.onrender.com/metrics
  # Esperado: Prometheus format (text/plain)
  ```

- [ ] Alertas configurados (rate limiting, error rates)

### 5.2 Langfuse (Tracing)

- [ ] Observabilidade ativa se `LANGFUSE_PUBLIC_KEY` setada
  - [ ] Traces aparecendo em: https://cloud.langfuse.com/dashboard
  - [ ] Latency metrics sendo capturadas

### 5.3 Logs

- [ ] Logs centralizados em Render dashboard
- [ ] Pattern para erro/warning/info visível

---

## FASE 6: Gradual Rollout

### 6.1 Shadow Mode (10%)
- [ ] Activar shadow mode via environment variable
- [ ] Validar predictions comparadas com "ground truth"
- [ ] Monitorar discrepâncias

### 6.2 Canary (50%)
- [ ] Rotear 50% do tráfico para novo Octa
- [ ] Monitorar SLAs, error rates, latencies
- [ ] Comparar resultados com versão anterior

### 6.3 Produção (100%)
- [ ] Todos os checks passaram
- [ ] Rollback plan documentado
- [ ] Go-live 100%

---

## Documentação de Referência

- 📄 **DEPLOY_SUCCESS.md** — Timeline completo do deployment
- 📄 **ENV_VARS_CHECKLIST.md** — Detalhes de cada variável
- 📄 **scripts/validate_live.sh** — Validação automática
- 📄 **scripts/test_octa_health.sh** — Teste de health contínuo

---

## Contatos & Escalação

- **Render Support:** https://render.com/support
- **GitHub Repo:** https://github.com/olga-ai-lab/88i-sinistro-harness
- **Logs ao Vivo:** https://dashboard.render.com/srv-d8bo09cp3tds73als7u0

---

**Status Geral:** 🟡 Em Progresso (fase 1: validação de saúde)
**Último Update:** 2026-05-27 21:32 GMT-3
