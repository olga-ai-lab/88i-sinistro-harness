# 🚀 VERCEL DEPLOYMENT — 2 MINUTE SETUP

## ✅ What's Ready

- ✅ Code in GitHub (88i-sinistro-harness)
- ✅ vercel.json configuration added
- ✅ api/main.py ready for Vercel
- ✅ Environment variables configured

---

## 🎯 2-Minute Setup

### Step 1: Go to Vercel (1 minute)

Open: https://vercel.com/new

---

### Step 2: Import Project From GitHub (30 seconds)

1. Click **"Import Project"**
2. Select **GitHub**
3. Search for: `88i-sinistro-harness`
4. Click **"Import"**

---

### Step 3: Configure Project (30 seconds)

1. **Project Name:** Keep default or change to `octa-production`
2. **Framework:** Select **"Other"** (it will auto-detect Python)
3. **Root Directory:** Leave empty
4. Click **"Deploy"**

---

### Step 4: Set Environment Variables (30 seconds)

Go back to Vercel Settings:
- Click **"Settings"** tab
- Go to **"Environment Variables"**
- Add these variables:

```
ANTHROPIC_API_KEY = [your key]
SUPABASE_URL = [your URL]
SUPABASE_KEY = [your key]
INNGEST_EVENT_KEY = [your key]
INNGEST_SIGNING_KEY = [your key]
LANGFUSE_PUBLIC_KEY = [your key]
LANGFUSE_SECRET_KEY = [your key]
```

---

### Step 5: Redeploy (30 seconds)

1. Go to **"Deployments"** tab
2. Click **"Redeploy"** button on latest deployment
3. Wait for green checkmark ✅

---

## 🎉 Done!

Your Octa will be live at:
```
https://octa-production.vercel.app/health
```

---

## ⏱️ Timeline

- Step 1-2: 1.5 min
- Step 3: 2 min (Vercel builds)
- Step 4: 1 min
- Step 5: 2 min (redeploy with env vars)
- **Total: ~6 minutes**

---

## 🔍 After Deploy

Test it:

```bash
curl https://octa-production.vercel.app/health
# Should return: {"status":"ok"}

curl -X POST https://octa-production.vercel.app/sinistro \
  -H "Content-Type: application/json" \
  -d '{"sinistro_id":"TEST","narrativa":"Test","tipo":"AP"}'
# Should return full workflow response
```

---

**Ready? Go to https://vercel.com/new and start! 🚀**
