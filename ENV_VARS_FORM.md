# 📋 ENVIRONMENT VARIABLES — Formulário para Preenchimento

Cole aqui as 7 variáveis que você tem:

---

## 1️⃣ ANTHROPIC_API_KEY
**O que é:** Claude/OpenAI API key para BAML LLM calls
**Onde encontrar:** 
- https://console.anthropic.com (se for Anthropic/Claude)
- https://platform.openai.com (se for OpenAI)

```
ANTHROPIC_API_KEY = 
```

---

## 2️⃣ SUPABASE_URL
**O que é:** URL do seu projeto Supabase (database)
**Onde encontrar:** https://supabase.com → Project Settings → API

```
SUPABASE_URL = 
```

---

## 3️⃣ SUPABASE_KEY
**O que é:** API Key do Supabase (service role ou anon key)
**Onde encontrar:** https://supabase.com → Project Settings → API → Service Role Key

```
SUPABASE_KEY = 
```

---

## 4️⃣ INNGEST_EVENT_KEY
**O que é:** Inngest API key para event triggers
**Onde encontrar:** https://app.inngest.com → Settings → API Keys

```
INNGEST_EVENT_KEY = 
```

---

## 5️⃣ INNGEST_SIGNING_KEY
**O que é:** Inngest signing key para webhooks
**Onde encontrar:** https://app.inngest.com → Settings → Signing Keys

```
INNGEST_SIGNING_KEY = 
```

---

## 6️⃣ LANGFUSE_PUBLIC_KEY
**O que é:** Langfuse public key para observabilidade
**Onde encontrar:** https://cloud.langfuse.com → Settings → API Keys

```
LANGFUSE_PUBLIC_KEY = 
```

---

## 7️⃣ LANGFUSE_SECRET_KEY
**O que é:** Langfuse secret key para observabilidade
**Onde encontrar:** https://cloud.langfuse.com → Settings → API Keys

```
LANGFUSE_SECRET_KEY = 
```

---

## 📝 Como Fornecer

**Opção 1 (Mais seguro):** Cole diretamente na próxima mensagem
```
ANTHROPIC_API_KEY = sk-ant-...
SUPABASE_URL = https://...
etc
```

**Opção 2 (Menos seguro):** Paste em um arquivo .env local

---

## ⏰ Timeline Após Fornecer

1. Você envia 7 variáveis
2. Eu configuro em uma plataforma (Vercel)
3. Deploy automático
4. /health = 200 OK ✅
5. Octa LIVE! 🎉

---

**Pronto pra colar as 7 variáveis aqui?** 🚀
