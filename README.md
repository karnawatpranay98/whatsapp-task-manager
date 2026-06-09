# WhatsApp Task Manager

> Never miss a follow-up again. Get a nightly email digest of every open item, unanswered question, and pending commitment from your WhatsApp conversations — analysed by AI.

![Email Preview](https://img.shields.io/badge/Daily_Digest-9pm_every_night-25d366?style=for-the-badge&logo=whatsapp)

---

## What it does

Every night at 9pm, this tool:

1. Reads your WhatsApp conversations from the last 24 hours
2. Uses Claude AI to understand context and identify what's genuinely unresolved
3. Sends you a clean, prioritised email with every open item

**Example items it catches:**
- A question someone asked that you never answered
- A commitment you made ("I'll send it today") with no follow-up
- A task assigned to you with no confirmation
- A pending decision waiting for your input

---

## How it works

```
WhatsApp Web (headless Chrome)
        ↓
   fetch.js — pulls last 24hrs of messages
        ↓
   messages.json
        ↓
   analyze.py — sends to Claude AI
        ↓
   open_items.txt
        ↓
   send_email.py — sends via Gmail
        ↓
   Your inbox at 9pm
```

Everything runs **locally on your machine**. Your messages are never stored on any server.

---

## Setup

### Prerequisites
- Mac (Windows support coming soon)
- Gmail account with 2-Step Verification enabled
- An Anthropic API key

### One-command install

```bash
git clone https://github.com/YOUR_USERNAME/whatsapp-task-manager.git
cd whatsapp-task-manager
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Then run:

```bash
bash setup.sh
```

The script will:
- Install Homebrew, Node.js, and Python if not already present
- Ask for your Gmail address and App Password
- Walk you through the one-time WhatsApp QR scan
- Send your first digest email immediately
- Schedule nightly emails at 9pm automatically

---

## Gmail App Password

Gmail requires an App Password (not your regular password) to send emails programmatically.

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Make sure 2-Step Verification is ON
3. Create a new App Password named "WhatsApp Digest"
4. Copy the 16-character code — the setup script will ask for it

---

## Running manually

```bash
# Fetch latest messages
node whatsapp-fetcher/fetch.js

# Analyse with AI
python3 python-analyzer/analyze.py

# Send email
python3 python-analyzer/send_email.py

# Or run all three at once
bash run.sh
```

---

## File structure

```
whatsapp-task-manager/
├── setup.sh                  ← one-command setup
├── run.sh                    ← runs the full pipeline
├── .env.example              ← copy to .env and fill in
├── whatsapp-fetcher/
│   └── fetch.js              ← connects to WhatsApp Web, saves messages
└── python-analyzer/
    ├── analyze.py            ← sends messages to Claude AI
    └── send_email.py         ← formats and sends the digest email
```

---

## Privacy

- Your WhatsApp messages are processed locally
- Messages are sent to the [Anthropic API](https://anthropic.com) for analysis — they are not used for training
- Nothing is stored on any third-party server
- Your Gmail App Password is stored only in your local `.env` file

---

## Built with

- [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) — WhatsApp Web client
- [Puppeteer](https://pptr.dev) — headless Chrome automation
- [Claude API](https://anthropic.com) — AI analysis
- Python `smtplib` — email delivery

---

## License

MIT — free to use and modify.
