# 🔑 Guia Rápido — Obter Credenciais para Octa

## Passo a Passo

### 1. ANTHROPIC_API_KEY
1. Acesse: https://console.anthropic.com/
2. Login com sua conta Anthropic
3. Vá para "API Keys"
4. Clique "Create Key"
5. Copie a chave (começa com `sk-ant-`)

**Valor para copiar:** `sk-ant-v4-xxxxxxxxxxxxxxxxxxxxx`

---

### 2. SUPABASE_URL + SUPABASE_ANON_KEY
1. Acesse: https://app.supabase.com/
2. Login com sua conta Supabase
3. Selecione seu projeto
4. Clique em "Project Settings" (engrenagem, canto inferior esquerdo)
5. Vá para aba "API" ou "Configuration"
6. Você verá:
   - **Project URL** → Copie para `SUPABASE_URL`
   - **anon public** → Copie para `SUPABASE_ANON_KEY`

**Valores para copiar:**
```
SUPABASE_URL = https://xxxxxxx.supabase.co
SUPABASE_ANON_KEY = eyJhbG... (começa com eyJ)
```

---

### 3. INNGEST_EVENT_KEY + INNGEST_SIGNING_KEY
1. Acesse: https://app.inngest.com/
2. Login com sua conta Inngest
3. Vá para "Settings" (engrenagem)
4. Procure por "Signing Keys" ou "API Keys"
5. Você verá:
   - **Event Key** → Copie para `INNGEST_EVENT_KEY`
   - **Signing Key** → Copie para `INNGEST_SIGNING_KEY`

**Valores para copiar:**
```
INNGEST_EVENT_KEY = evt_prod_xxxxxxxxxxxxx
INNGEST_SIGNING_KEY = signkey_prod_xxxxxxxxxxxxx
```

---

### 4. LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY (Opcional)
1. Acesse: https://cloud.langfuse.com/
2. Login com sua conta Langfuse
3. Clique no seu projeto
4. Vá para "Settings"
5. Procure por "API Keys"
6. Você verá:
   - **Public Key** → Copie para `LANGFUSE_PUBLIC_KEY`
   - **Secret Key** → Copie para `LANGFUSE_SECRET_KEY`

**Valores para copiar:**
```
LANGFUSE_PUBLIC_KEY = pk-lf-xxxxxxxxxxxxx
LANGFUSE_SECRET_KEY = sk-lf-xxxxxxxxxxxxx
```

---

## ⚠️ Dica Importante

**NÃO compartilhe essas credenciais!**
- Nunca commite ao GitHub
- Nunca mande por email
- Apenas use no Render Dashboard

---

## Próximo Passo

Depois de copiar as 7 credenciais (ou 5 se pular Langfuse), eu ajudo você a:
1. Aguardar /health ficar 200 OK
2. Adicionar cada credencial no Render Dashboard
3. Testar os endpoints
4. Configurar monitoring
5. Go-live!
