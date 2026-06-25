# WhatsApp Fashion Agent MVP

An MVP WhatsApp AI sales assistant for fashion businesses. It can answer catalog and story-item questions, explain product details, collect order intent, and run a local admin/chat simulator before WhatsApp credentials are connected.

## What Is Included

- Flask backend with WhatsApp webhook endpoints.
- SQLite database for products, story items, customers, conversations, and orders.
- AI assistant layer using Groq when `GROQ_API_KEY` is set.
- Offline fallback assistant for local demos without API keys.
- WhatsApp sender service with dry-run mode when Meta credentials are missing.
- Admin console for adding products, mapping story items, testing chat, and viewing orders.

## Project Structure

```text
whatsapp-fashion-agent/
  backend/
    app.py
    data/
    services/
      agent.py
      db.py
      whatsapp.py
  frontend/
    index.html
    styles.css
    app.js
  .env.example
  requirements.txt
```

## Run Locally

```powershell
cd "C:\Users\hp\Desktop\IBM\whatsapp-fashion-agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python backend\app.py
```

Open:

```text
http://localhost:5000
```

Try these messages in the chat simulator:

```text
How much is the dress from your story?
Do you have the emerald dress in medium?
I want to order the ivory kaftan
Show me handbags
```

## WhatsApp Setup

1. Create a Meta Developer app with WhatsApp Business Platform enabled.
2. Add your webhook URL:

```text
https://your-domain.com/webhook/whatsapp
```

3. Use the same verify token as `WHATSAPP_VERIFY_TOKEN` in `.env`.
4. Add:

```text
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
```

5. Restart the Flask app.

## Groq Setup

1. Create a Groq API key from the Groq Console.
2. Add it to `.env`:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

3. Restart the Flask app.

If `GROQ_API_KEY` is blank, the app still works with the built-in local fallback assistant.

For local webhook testing, expose your app with a tunnel such as ngrok:

```powershell
ngrok http 5000
```

## MVP Data Flow

```text
Customer WhatsApp message
  -> Meta webhook
  -> Flask /webhook/whatsapp
  -> agent.generate_reply()
  -> catalog/story lookup
  -> Groq or local fallback response
  -> WhatsApp Cloud API reply
```

## Next Production Steps

- Add authentication to the admin console.
- Add payment provider integration, such as Paystack, Flutterwave, or Stripe.
- Add real order-state flows: pending, confirmed, paid, packed, delivered.
- Add staff handoff inbox.
- Add image upload and OCR/vision extraction for story screenshots.
- Add inventory locking to prevent overselling.
- Add deployment config for Render, Railway, Fly.io, or Azure.
