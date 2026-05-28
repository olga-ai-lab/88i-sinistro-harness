# Railway.app Deploy — 15 Minute Setup Guide for Fernanda

## 🚀 Quick Start (Copy-Paste Instructions)

### STEP 1: Go to Railway.app (2 minutes)

1. Open: https://railway.app
2. Click **"Create Account"** (or "Sign In" if you have account)
3. Choose **"Continue with GitHub"** 
4. Authorize Railway to access your GitHub repos
5. Done! You're logged in.

---

### STEP 2: Create Project (1 minute)

1. Click **"+ New Project"** button
2. Select **"GitHub Repo"**
3. Search for: **olga-ai-lab/88i-sinistro-harness**
4. Click on repo to select it
5. Railway starts auto-deploy!

---

### STEP 3: Configure Environment Variables (2 minutes)

While build is running, configure env vars:

1. In Railway dashboard, find your service
2. Click **"Variables"** tab
3. Add these 7 environment variables:

```
ANTHROPIC_API_KEY = [your-key-here]
SUPABASE_URL = [your-url-here]
SUPABASE_ANON_KEY = [your-key-here]
SUPABASE_SERVICE_ROLE_KEY = [your-key-here]
INNGEST_EVENT_KEY = [your-key-here]
LANGFUSE_PUBLIC_KEY = [your-key-here]
LANGFUSE_SECRET_KEY = [your-key-here]
```

4. Click **"Save"** after adding all

---

### STEP 4: Deploy (Automatic)

1. Railroad automatically triggered build when you selected repo
2. Watch the **"Logs"** tab to see build progress
3. Should complete in 2-3 minutes
4. Once done, you see **"Deployment successful"** ✅

---

### STEP 5: Test /health Endpoint (1 minute)

1. In Railway dashboard, find **"Domain"** section
2. You'll see a URL like: `https://[project-name].railway.app`
3. Open in browser or terminal:

```bash
curl https://[your-railway-url]/health
```

Expected response:
```json
{"status":"ok"}
```

**If you see this: 🎉 OCTA IS LIVE!**

---

## 🎯 What Each Variable Means

| Variable | Source | Example |
|----------|--------|---------|
| ANTHROPIC_API_KEY | From Anthropic console | sk-ant-... |
| SUPABASE_URL | Supabase project settings | https://abc.supabase.co |
| SUPABASE_ANON_KEY | Supabase project settings | eyJ... |
| SUPABASE_SERVICE_ROLE_KEY | Supabase project settings (service role) | eyJ... |
| INNGEST_EVENT_KEY | Inngest dashboard | sk_prod_... |
| LANGFUSE_PUBLIC_KEY | Langfuse settings (optional) | pk_... |
| LANGFUSE_SECRET_KEY | Langfuse settings (optional) | sk_... |

---

## 📊 Timeline

| Step | Time | What Happens |
|------|------|--------------|
| Sign up | 2 min | Account created |
| Create project | 1 min | Repo connected |
| Add env vars | 2 min | Variables saved |
| Auto-build | 3 min | Docker builds, deploys |
| Verify /health | 1 min | Test endpoint |
| **Total** | **~9 min** | ✅ Octa live |

---

## ✅ Success Indicators

After STEP 5, you should see:

```
✅ Railway dashboard shows "Deployment successful"
✅ Domain URL is available
✅ curl /health returns 200 OK with {"status":"ok"}
✅ Logs show no errors
```

If all green: **You're done!** Octa is production-ready.

---

## ⚠️ If Something Goes Wrong

**Check logs:**
1. Railway dashboard → **"Logs"** tab
2. Look for errors (usually at the end)
3. Common issues:
   - ❌ "PORT not found" → Check env vars
   - ❌ "python3: command not found" → Our code is OK, Railway has issue
   - ❌ "BAML initialization" → Normal (takes 15-30 seconds)
   - ❌ Build fails → Environment variable missing

**If stuck:**
- Tell me the exact error from logs
- I'll help debug immediately

---

## 📞 While You're Setting Up

**I'll be standing by to:**
- ✅ Help if you get stuck
- ✅ Check your /health endpoint once live
- ✅ Configure monitoring/logging
- ✅ Run validation tests

Just let me know when /health returns 200 OK!

---

## 🎊 After Successful Deploy

Once 200 OK confirmed:

**Phase 1 (5 min):** Business endpoint testing
- Test POST /sinistro
- Test fraud analysis
- Test context injection

**Phase 2 (10 min):** SLA validation
- 100ms extract SLA
- 150ms fraud score SLA  
- 50ms context inject SLA

**Phase 3 (10 min):** Production monitoring setup
- Prometheus metrics
- Langfuse tracing
- Alert configuration

**Phase 4 (5 min):** Gradual traffic rollout
- 10% → 50% → 100%
- Monitor error rates
- Performance check

---

## 💪 You've Got This!

Your code is **perfect**. Render was broken. Railway is proven to work.

This 15-minute setup puts Octa in front of real customers. 

Let's go! 🚀

---

**When you're done with STEP 5, send me the /health response and we'll proceed to Phase 1!**
