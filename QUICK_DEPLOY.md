# 🚀 Quick Deployment Commands

## Step 1: Push to GitHub
```powershell
cd c:\Users\deepakgupta13\Downloads\nagarro_development\msil_mcp

git add .
git commit -m "feat: Add Render.com + Vercel deployment configuration

- Add render.yaml for Render.com deployment
- Add vercel.json for both UIs
- Centralize API URL configuration
- Update all fetch calls to use getApiUrl
- Support environment-based API URLs
- Update CORS for Vercel domains
- Add SQLite support for demo"

git push origin main
```

## Step 2: Deploy to Render.com
1. Go to https://render.com
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Select repository: `Tannu-Git/msil_mcp`
5. Render will detect `render.yaml` automatically
6. Click "Apply"
7. Add secrets in Environment tab:
   - `MSIL_APIM_BASE_URL`
   - `MSIL_APIM_SUBSCRIPTION_KEY`
   - `OPENAI_API_KEY`
   - `API_KEY`
8. Click "Create Web Service"
9. Wait 3-5 minutes
10. Note the URL: `https://msil-mcp-backend.onrender.com`

## Step 3: Deploy Admin UI to Vercel
```powershell
cd admin-ui

# Deploy
npx vercel --token bNfJYaewDukflqPgj3mrYGDV --prod

# Add environment variable
npx vercel env add VITE_API_URL production --token bNfJYaewDukflqPgj3mrYGDV
# Enter: https://msil-mcp-backend.onrender.com

# Redeploy to apply env vars
npx vercel --prod --token bNfJYaewDukflqPgj3mrYGDV
```

## Step 4: Deploy Chat UI to Vercel
```powershell
cd ../chat-ui

# Deploy
npx vercel --token bNfJYaewDukflqPgj3mrYGDV --prod

# Add environment variable
npx vercel env add VITE_API_URL production --token bNfJYaewDukflqPgj3mrYGDV
# Enter: https://msil-mcp-backend.onrender.com

# Redeploy to apply env vars
npx vercel --prod --token bNfJYaewDukflqPgj3mrYGDV
```

## Step 5: Update CORS in Render
1. Go to Render dashboard
2. Click on "msil-mcp-backend"
3. Go to "Environment" tab
4. Update `CORS_ORIGINS` to your Vercel URLs:
   ```
   https://msil-admin-ui-xxx.vercel.app,https://msil-chat-ui-xxx.vercel.app
   ```
5. Click "Save Changes"

## Step 6: Test Everything
```powershell
# Test backend
curl https://msil-mcp-backend.onrender.com/health

# Test admin UI (open in browser)
start https://msil-admin-ui-xxx.vercel.app

# Test chat UI (open in browser)
start https://msil-chat-ui-xxx.vercel.app
```

## 🎯 Expected Results
- ✅ Backend returns `{"status":"healthy"}`
- ✅ Admin UI loads and shows login
- ✅ Chat UI loads and shows interface
- ✅ No CORS errors in browser console
- ✅ Can login and navigate all pages
- ✅ Tools page shows MSIL APIM endpoints

## 📝 Important URLs to Note
After deployment, save these:
- Backend: `https://msil-mcp-backend.onrender.com`
- Admin UI: `https://msil-admin-ui-xxx.vercel.app`
- Chat UI: `https://msil-chat-ui-xxx.vercel.app`

## ⚡ Quick Fixes

### If backend won't start:
```powershell
# Check Render logs
# Verify environment variables are set
# Make sure SQLite path is correct: sqlite+aiosqlite:///./data/msil_mcp_demo.db
```

### If frontend can't connect:
```powershell
# Verify VITE_API_URL is set
npx vercel env ls production --token bNfJYaewDukflqPgj3mrYGDV

# If missing, add it:
npx vercel env add VITE_API_URL production --token bNfJYaewDukflqPgj3mrYGDV
# Then redeploy
```

### If CORS errors:
1. Check browser console for exact error
2. Verify CORS_ORIGINS in Render includes your Vercel URLs
3. Make sure there are no typos in URLs
4. Wait 30 seconds after updating for Render to redeploy

## 🔄 To Update After Changes
```powershell
# Backend: Just push to GitHub
git add .
git commit -m "Update backend"
git push origin main
# Render auto-deploys

# Frontend: Redeploy to Vercel
cd admin-ui
npx vercel --prod --token bNfJYaewDukflqPgj3mrYGDV

cd ../chat-ui
npx vercel --prod --token bNfJYaewDukflqPgj3mrYGDV
```

---

**Total Time: ~15 minutes**  
**Total Cost: $0/month**  
**Demo Ready:** ✅
