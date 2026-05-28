# Railway Deployment — Quick Reference Checklist

## ✅ PRE-FLIGHT CHECKLIST (Before you start)

- [ ] You have your 7 environment variables ready (ANTHROPIC_API_KEY, SUPABASE_*, INNGEST_*, LANGFUSE_*)
- [ ] You have GitHub access (already connected)
- [ ] You can access railway.app
- [ ] You have ~20 minutes free to do setup + testing

---

## 🚀 STEP 1: Create Railway Account (2 min)

```
[ ] Go to https://railway.app
[ ] Click "Create Account" 
[ ] Choose "Continue with GitHub"
[ ] Authorize Railway to access your GitHub
[ ] Verify email if needed
```

**Status: ✅ Account created**

---

## 🔗 STEP 2: Connect GitHub Repo (1 min)

```
[ ] In Railway dashboard, click "+ New Project"
[ ] Select "GitHub Repo"
[ ] Search for: olga-ai-lab/88i-sinistro-harness
[ ] Click to select it
[ ] Watch the build start automatically
```

**Status: ✅ Repo connected, build triggered**

---

## 🔐 STEP 3: Add Environment Variables (2 min)

```
[ ] In Railway dashboard, find your service
[ ] Click "Variables" tab
[ ] Add 7 variables (copy from your credentials):
    [ ] ANTHROPIC_API_KEY = [your-key]
    [ ] SUPABASE_URL = [your-url]
    [ ] SUPABASE_ANON_KEY = [your-key]
    [ ] SUPABASE_SERVICE_ROLE_KEY = [your-key]
    [ ] INNGEST_EVENT_KEY = [your-key]
    [ ] LANGFUSE_PUBLIC_KEY = [your-key]
    [ ] LANGFUSE_SECRET_KEY = [your-key]
[ ] Click "Save Variables"
```

**Status: ✅ Environment variables configured**

---

## 🔨 STEP 4: Deploy (Automatic, 3 min)

```
[ ] Watch "Logs" tab in Railway dashboard
[ ] You should see build progress (Docker building...)
[ ] Build completes (~2-3 min)
[ ] See message: "Deployment successful"
```

**What's happening:**
- Docker builds the image
- Container starts
- App initializes BAML (takes ~15-30 sec, normal)
- Ready to receive requests

**Status: ✅ Build complete**

---

## 🧪 STEP 5: Test /health Endpoint (1 min)

```
[ ] In Railway dashboard, find "Domain" section
[ ] Copy the URL (looks like https://octa-[name].railway.app)
[ ] Open terminal and run:

    curl https://[your-railway-url]/health

[ ] You should see response:
    {"status":"ok"}

[ ] HTTP status code should be 200
```

**If you see 200 OK with {"status":"ok"}: 🎉 SUCCESS!**

---

## 📊 RESULTS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Railway build | Success | — | [ ] |
| HTTP code | 200 | — | [ ] |
| Response body | {"status":"ok"} | — | [ ] |
| Build time | 2-3 min | — | [ ] ✅ |

---

## 🆘 IF SOMETHING GOES WRONG

### Build fails?
- [ ] Check "Logs" tab for error message
- [ ] Common: Missing environment variable
- [ ] Solution: Add missing env var, re-trigger deploy

### /health returns 404?
- [ ] Check if deployment really succeeded
- [ ] Check if domain URL is correct
- [ ] Check Logs for app startup errors

### /health returns 500?
- [ ] Check Logs for error details
- [ ] Likely: Missing env variable
- [ ] Solution: Add env var, redeploy

### Takes too long?
- [ ] Normal: First build takes 2-3 min
- [ ] BAML compilation takes 15-30 seconds
- [ ] App startup takes ~10 seconds total
- [ ] Wait up to 5 minutes before giving up

---

## ✅ SUCCESS CRITERIA

You're done when:

```
✅ Railway account created
✅ GitHub repo connected
✅ 7 environment variables added
✅ Build shows "Successful"
✅ /health returns 200 OK
✅ Response is {"status":"ok"}
```

---

## 📞 NEXT STEPS AFTER SUCCESS

When you confirm /health = 200 OK:

1. **Phase 1:** Business endpoint testing (5 min)
2. **Phase 2:** SLA validation (10 min)
3. **Phase 3:** Monitoring setup (10 min)
4. **Phase 4:** Traffic rollout (5 min)

---

## 🎯 TIME TRACKING

```
Start:              [____] min
Step 1 (signup):    [____] min
Step 2 (connect):   [____] min
Step 3 (env vars):  [____] min
Step 4 (deploy):    [____] min
Step 5 (test):      [____] min
────────────────────────────
Total elapsed:      [____] min
Expected:           ~15 min
```

---

## 💬 COMMUNICATION

When done, message me with:

```
✅ /health = 200 OK
🎉 Ready for Phase 1
```

Or if you hit an issue:

```
❌ /health returned [error]
Check Logs tab: [error message]
Need help with: [what's unclear]
```

---

## 🎊 YOU'VE GOT THIS!

Remember:
- ✅ Your code is perfect
- ✅ Railway is proven to work
- ✅ This is the last major step before Octa goes live
- ✅ You're 15 minutes away from production deployment

Let's go! 🚀

---

**Start time:** [fill in when you begin]  
**Estimated completion:** Start time + 15 minutes  
**Contact if stuck:** Just message me!
