# SiteSnap Backend — Deploy & Connect Guide

## Step 1: GitHub pe Upload Karo

```bash
cd sitesnap-backend
git init
git add .
git commit -m "SiteSnap backend initial"
# GitHub pe naya repo banao: sitesnap-backend
git remote add origin https://github.com/TUMHARA_USERNAME/sitesnap-backend.git
git push -u origin main
```

---

## Step 2: Railway pe Deploy Karo

1. railway.app pe jao → Login with GitHub
2. "New Project" → "Deploy from GitHub repo"
3. Apna `sitesnap-backend` repo select karo
4. Railway automatically Dockerfile detect kar lega
5. Deploy hone do (3-5 min lagenge)
6. Deploy ke baad URL milega: `https://sitesnap-backend-xxxx.railway.app`

---

## Step 3: Test Karo

Browser mein yeh URL kholo:
```
https://your-app.railway.app/api/health
```
Response aana chahiye:
```json
{"status": "ok", "service": "SiteSnap API"}
```

API docs yahan hain:
```
https://your-app.railway.app/docs
```

---

## Step 4: Lovable mein Connect Karo

Lovable ke chat mein yeh prompt paste karo
(LOVABLE_INTEGRATION.js file ke end mein diya hua hai):

```
Update the SiteSnap app to connect to a real backend API.

Backend base URL: https://YOUR-RAILWAY-URL.railway.app

API Endpoints:
- POST /api/scans/start
- GET  /api/scans/status/{scan_id}
- POST /api/scans/stop

[... baaki LOVABLE_INTEGRATION.js se copy karo ...]
```

---

## CORS Note

Agar Lovable domain se request block ho to
`app/main.py` mein `allow_origins` update karo:

```python
allow_origins=["https://your-lovable-app.lovable.app"]
```

---

## Free Tier Limits (Railway)

- $5 free credit har mahine
- ~500 hours runtime
- 1 GB RAM (Playwright ke liye kaafi hai)
- Agar zyada chahiye: $5/month Hobby plan

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Playwright install fail | Dockerfile use ho raha hai confirm karo |
| CORS error | allow_origins mein Lovable URL daalo |
| Scan timeout | max_pages kam karo (20-30) |
| Login fail | login_url manually specify karo |
