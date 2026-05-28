# Environment Variables Checklist para Octa no Render

## 📋 Variáveis Obrigatórias

### 1. OpenAI / Anthropic
- [ ] `ANTHROPIC_API_KEY` — Chave para Claude AI (substitua XXX)
  ```
  sk-ant-v4-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```

### 2. Supabase (Database + Auth)
- [ ] `SUPABASE_URL` — URL da API Supabase
  ```
  https://xxxxx.supabase.co
  ```
- [ ] `SUPABASE_ANON_KEY` — Chave pública Supabase
  ```
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```

### 3. Inngest (Workflow Engine)
- [ ] `INNGEST_EVENT_KEY` — Chave de eventos Inngest
  ```
  evt_prod_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```
- [ ] `INNGEST_SIGNING_KEY` — Chave de assinatura Inngest
  ```
  signkey_prod_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```

### 4. Langfuse (Observability - OPCIONAL)
- [ ] `LANGFUSE_PUBLIC_KEY` — Chave pública Langfuse
  ```
  pk-lf-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```
- [ ] `LANGFUSE_SECRET_KEY` — Chave secreta Langfuse
  ```
  sk-lf-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```

### 5. Logging & Debug
- [ ] `LOG_LEVEL` — (opcional, default: INFO)
  ```
  INFO | DEBUG | WARNING | ERROR
  ```
- [ ] `PYTHONUNBUFFERED` — (default: 1)
  ```
  1
  ```

---

## 🚀 Como Adicionar no Render

### Opção 1: Dashboard (UI)
1. Vá para https://dashboard.render.com/services
2. Clique no seu serviço (octa-sinistro-harness ou similar)
3. Vá para aba **"Environment"**
4. Clique **"Add Environment Variable"**
5. Digite a chave e valor
6. Clique **"Save"**
7. Render vai fazer auto-redeploy

### Opção 2: Render CLI (Terminal)
```bash
# Login
render login

# Set variable
render env set ANTHROPIC_API_KEY "sk-ant-v4-..."

# Verify
render env list
```

### Opção 3: render.yaml (IaC)
Editar `/render.yaml` e adicionar:
```yaml
envVars:
  - key: ANTHROPIC_API_KEY
    scope: RUN
    value: ${ANTHROPIC_API_KEY}
```

---

## ⚠️ SEGURANÇA

**NUNCA commit secrets ao GitHub!**

✅ Use Render Dashboard ou Render CLI  
❌ Nunca use `.env` local em produção  
✅ Render carrega automaticamente do dashboard  

---

## 📊 Validação

Depois de adicionar as variáveis:

```bash
# Verificar que estão setadas
curl https://YOUR_RENDER_URL/health

# Deve responder com status 200
# Se Langfuse está configurado, logs aparecerão lá
```

---

## 🔄 Próximas Etapas

1. ✅ Copiar credentials de ANTHROPIC_API_KEY
2. ✅ Copiar credentials de SUPABASE_*
3. ✅ Copiar credentials de INNGEST_*
4. ✅ (Opcional) Copiar credentials de LANGFUSE_*
5. ✅ Adicionar todas ao Render Dashboard
6. ✅ Aguardar auto-redeploy
7. ✅ Validar `/health` endpoint
8. ✅ Testar endpoints de negócio

---

**Você tem todos esses credentials?** Se sim, vou ajudar com o setup!
