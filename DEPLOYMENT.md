# Deployment Guide

## 1. Push To GitHub

Create an empty GitHub repository named `whatsapp-fashion-agent`, then run:

```powershell
cd "C:\Users\hp\Desktop\IBM\whatsapp-fashion-agent"
git remote add origin https://github.com/YOUR_USERNAME/whatsapp-fashion-agent.git
git push -u origin main
```

If `origin` already exists:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/whatsapp-fashion-agent.git
git push -u origin main
```

## 2. Deploy On Render

1. Go to Render.
2. Create a new **Web Service**.
3. Connect the GitHub repo.
4. Render should detect `render.yaml`.
5. Use these settings if entering manually:

```text
Environment: Python
Build command: pip install -r requirements.txt
Start command: gunicorn backend.app:app
```

## 3. Add Render Environment Variables

Add these in Render dashboard:

```text
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
WHATSAPP_VERIFY_TOKEN=fashion-agent-verify
WHATSAPP_ACCESS_TOKEN=your_meta_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
FLASK_DEBUG=0
```

Do not commit `.env` to GitHub.

## 4. Connect Meta Webhook

After Render deploys, copy your Render URL:

```text
https://your-render-service.onrender.com
```

In Meta, set:

```text
Callback URL:
https://your-render-service.onrender.com/webhook/whatsapp

Verify token:
fashion-agent-verify
```

Subscribe to:

```text
messages
```

## 5. Test

Open:

```text
https://your-render-service.onrender.com/health
```

Expected:

```json
{"service":"whatsapp-fashion-agent","status":"ok"}
```

Then message the connected WhatsApp Business number.
