# 🚀 Deployment Guide: Render.com + Vercel (Demo)

**Cost:** $0/month  
**Time:** 15 minutes  
**Architecture:** Backend on Render.com (free), Frontends on Vercel (free)

---

## 📋 Prerequisites

- [x] GitHub account
- [x] Render.com account (sign up at https://render.com)
- [x] Vercel account (optional, can use CLI)
- [x] Vercel auth token: `bNfJYaewDukflqPgj3mrYGDV`
- [x] MSIL Pre-Prod APIM credentials

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    DEMO DEPLOYMENT                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Vercel (FREE)                        Render.com (FREE)      │
│  ┌────────────────┐                   ┌─────────────────┐   │
│  │  Admin UI      │──────┐            │  FastAPI        │   │
│  │  .vercel.app   │      │            │  - SQLite DB    │   │
│  └────────────────┘      ├──HTTPS────►│  - In-memory    │   │
│                          │            │  - 512MB RAM    │   │
│  ┌────────────────┐      │            │  - Auto-sleep   │   │
│  │  Chat UI       │──────┘            │    @ 15min idle │   │
│  │  .vercel.app   │                   └─────────────────┘   │
│  └────────────────┘                           │             │
│                                               │             │
│                                               ▼             │
│                                       ┌─────────────────┐   │
│                                       │ MSIL Pre-Prod   │   │
│                                       │     APIM        │   │
│                                       └─────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Push Code to GitHub (2 mins)

```powershell
# Navigate to project root
cd c:\Users\deepakgupta13\Downloads\nagarro_development\msil_mcp

# Add all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add Render.com + Vercel deployment configuration"

# Push to GitHub
git push origin main
```

**Verify:** Check GitHub repo at https://github.com/Tannu-Git/msil_mcp.git

---

## Step 2: Deploy Backend to Render.com (5 mins)

### 2.1 Create Render Account
1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended for auto-deploy)

### 2.2 Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect to GitHub repository: `Tannu-Git/msil_mcp`
3. Render will auto-detect `render.yaml` configuration ✅
4. Click **"Apply"** to use render.yaml settings

### 2.3 Add Environment Variables (Secrets)
⚠️ **Important:** These are NOT in `render.yaml` for security

Go to **Environment** tab and add:

| Key | Value | Notes |
|-----|-------|-------|
| `MSIL_APIM_BASE_URL` | `https://apim-preprod.marutisuzuki.com` | MSIL pre-prod endpoint |
| `MSIL_APIM_SUBSCRIPTION_KEY` | `<your-key>` | From MSIL team |
| `MSIL_APIM_CLIENT_ID` | `<your-client-id>` | Optional |
| `MSIL_APIM_CLIENT_SECRET` | `<your-secret>` | Optional |
| `OPENAI_API_KEY` | `<your-openai-key>` | For OpenAI integration |
| `API_KEY` | `msil-mcp-secure-key-2026` | Change to secure value |

### 2.4 Deploy
1. Click **"Create Web Service"**
2. Wait 3-5 minutes for build + deploy
3. Watch logs for "Application startup complete" ✅

### 2.5 Get Backend URL
Your backend will be at:
```
https://msil-mcp-backend.onrender.com
```

**Test it:**
```powershell
curl https://msil-mcp-backend.onrender.com/health
# Should return: {"status":"healthy"}
```

---

## Step 3: Update CORS for Vercel (1 min)

Before deploying frontends, update `CORS_ORIGINS` in Render:

1. Go to **Environment** tab in Render
2. Find `CORS_ORIGINS` variable
3. Update value to:
   ```
   *
   ```
   (We'll narrow this down after getting Vercel URLs)

4. Click **"Save Changes"**
5. Render will auto-redeploy (30 seconds)

---

## Step 4: Deploy Admin UI to Vercel (3 mins)

```powershell
# Navigate to admin-ui
cd admin-ui

# Set environment variable for deployment
$env:VITE_API_URL = "https://msil-mcp-backend.onrender.com"

# Deploy to Vercel (using your token)
npx vercel --token bNfJYaewDukflqPgj3mrYGDV --prod

# Vercel will prompt:
# ? Set up and deploy? Yes
# ? Which scope? [Select your account]
# ? Link to existing project? No
# ? What's your project's name? msil-admin-ui
# ? In which directory is your code located? ./
# ? Want to modify settings? No
```

**Output:** `https://msil-admin-ui.vercel.app` (or similar)

**Add Vercel Environment Variable:**
```powershell
# Add environment variable to Vercel project
npx vercel env add VITE_API_URL production --token bNfJYaewDukflqPgj3mrYGDV
# When prompted, enter: https://msil-mcp-backend.onrender.com
```

---

## Step 5: Deploy Chat UI to Vercel (3 mins)

```powershell
# Navigate to chat-ui
cd ../chat-ui

# Set environment variable
$env:VITE_API_URL = "https://msil-mcp-backend.onrender.com"

# Deploy to Vercel
npx vercel --token bNfJYaewDukflqPgj3mrYGDV --prod

# Follow same prompts as admin-ui
# Project name: msil-chat-ui
```

**Output:** `https://msil-chat-ui.vercel.app`

**Add Environment Variable:**
```powershell
npx vercel env add VITE_API_URL production --token bNfJYaewDukflqPgj3mrYGDV
# Enter: https://msil-mcp-backend.onrender.com
```

---

## Step 6: Update CORS (Final) (1 min)

Now that you have Vercel URLs, update CORS in Render:

1. Go to Render dashboard → **Environment** tab
2. Update `CORS_ORIGINS` to:
   ```
   https://msil-admin-ui.vercel.app,https://msil-chat-ui.vercel.app
   ```
3. Click **"Save Changes"**
4. Render auto-redeploys (30 seconds)

---

## Step 7: Test End-to-End (5 mins)

### 7.1 Test Backend Health
```powershell
curl https://msil-mcp-backend.onrender.com/health
curl https://msil-mcp-backend.onrender.com/docs
```

### 7.2 Test Admin UI
1. Open: `https://msil-admin-ui.vercel.app`
2. Login with demo credentials (if demo mode enabled)
3. Navigate to:
   - **Dashboard** - Should load
   - **Tools** - Should show imported APIs
   - **Policies** - Should show RBAC roles
   - **Users** - Should list users
   - **OPA Policies** - Should load Rego editor
   - **Test Authorization** - Should allow testing
   - **Exposure Governance** - Should show role-tool mapping

### 7.3 Test Chat UI
1. Open: `https://msil-chat-ui.vercel.app`
2. Login
3. Try sending a message
4. Should connect to MCP backend

### 7.4 Test MSIL APIM Integration
1. Go to **Admin UI** → **Tools**
2. Should see APIM endpoints
3. Go to **Service Booking**
4. Test booking flow (calls MSIL APIM)
5. Check **Audit Logs** for request records

---

## 🎉 Deployment Complete!

### Your Live URLs:
- **Admin Portal:** `https://msil-admin-ui.vercel.app`
- **Chat Interface:** `https://msil-chat-ui.vercel.app`
- **Backend API:** `https://msil-mcp-backend.onrender.com`
- **API Docs:** `https://msil-mcp-backend.onrender.com/docs`

---

## 📊 Monitoring & Logs

### Render Logs
1. Go to Render dashboard
2. Click on **msil-mcp-backend** service
3. Go to **Logs** tab
4. See real-time application logs

### Vercel Logs
```powershell
# View deployment logs
npx vercel logs --token bNfJYaewDukflqPgj3mrYGDV

# Or visit Vercel dashboard at https://vercel.com
```

---

## 🐛 Troubleshooting

### Backend Issues

**Problem:** Service won't start
```powershell
# Check Render logs for errors
# Common issues:
# 1. Missing environment variables (check Step 2.3)
# 2. Port binding (should be 8000)
# 3. Database initialization (SQLite path issues)
```

**Problem:** 502 Bad Gateway
- Backend is starting (wait 30-60 seconds)
- Or backend crashed (check logs)

**Problem:** CORS errors in browser
- Check CORS_ORIGINS includes Vercel URLs
- Verify Vercel URL is correct (check URL bar)

### Frontend Issues

**Problem:** Can't connect to backend
```powershell
# Check environment variable
npx vercel env ls --token bNfJYaewDukflqPgj3mrYGDV

# Should show:
# VITE_API_URL = https://msil-mcp-backend.onrender.com
```

**Problem:** Build fails
```powershell
# Check build logs
npx vercel logs --token bNfJYaewDukflqPgj3mrYGDV

# Common issues:
# 1. TypeScript errors (run `npm run build` locally first)
# 2. Missing dependencies (check package.json)
```

### APIM Integration Issues

**Problem:** Tools not showing
- Check `API_GATEWAY_MODE=msil_apim` in Render
- Verify MSIL_APIM_SUBSCRIPTION_KEY is correct
- Check Render logs for APIM connection errors

**Problem:** 401 Unauthorized
- APIM subscription key is wrong
- Check with MSIL team for correct credentials

---

## 🔄 Redeployment (Updates)

### Backend Updates
```powershell
# Push changes to GitHub
git add .
git commit -m "Update backend code"
git push origin main

# Render auto-deploys (2-3 minutes)
```

### Frontend Updates
```powershell
# Admin UI
cd admin-ui
npx vercel --prod --token bNfJYaewDukflqPgj3mrYGDV

# Chat UI
cd chat-ui
npx vercel --prod --token bNfJYaewDukflqPgj3mrYGDV
```

---

## ⚠️ Demo Limitations

| Aspect | Demo Behavior | Production Behavior |
|--------|---------------|---------------------|
| **Database** | SQLite (ephemeral) | PostgreSQL (persistent) |
| **Data Persistence** | Lost on redeploy | Permanent storage |
| **Availability** | Sleeps after 15 min idle | Always on (24/7) |
| **Wake-up Time** | ~30 seconds cold start | Instant |
| **Concurrent Users** | 1-5 | Unlimited |
| **Performance** | Slower (free tier CPU) | Fast (dedicated resources) |
| **Backups** | None | Automated daily |

---

## 💰 Cost Tracking

### Current (Demo):
- Render.com Free Tier: **$0/month**
- Vercel Hobby Plan: **$0/month**
- **Total: $0/month**

### Limits:
- Render: 750 hours/month (enough for demo)
- Vercel: 100GB bandwidth/month
- Both: Auto-sleep after inactivity

---

## 🚀 Next Steps (After Demo Success)

### Option 1: Upgrade Render (Stay Serverless)
```
Render Starter Plan: $7/month
- No auto-sleep
- 512MB RAM → 2GB RAM
- Faster performance
```

### Option 2: Migrate to AWS
```
Use existing Terraform configs:
- infrastructure/aws/terraform-dev/ (~$25/month)
- infrastructure/aws/terraform/ (~$150/month)
```

---

## 📞 Support

**Issues?**
- Check logs first (Render + Vercel dashboards)
- Verify environment variables
- Test backend health endpoint
- Ensure CORS is configured correctly

**Still stuck?**
- Share Render logs
- Share Vercel deployment URL
- Share browser console errors (F12)

---

## ✅ Pre-Demo Checklist

- [ ] Backend deployed and healthy (`/health` returns 200)
- [ ] Admin UI accessible and loads
- [ ] Chat UI accessible and loads
- [ ] Can login to both UIs
- [ ] Tools page shows APIM endpoints
- [ ] Test Authorization works
- [ ] Service Booking can be tested
- [ ] Audit logs are captured
- [ ] MSIL team provided APIM credentials
- [ ] Demo data created (users, roles, policies)

---

**Deployment Date:** February 9, 2026  
**Demo URL:** https://msil-admin-ui.vercel.app  
**Status:** ✅ Ready for Demo
