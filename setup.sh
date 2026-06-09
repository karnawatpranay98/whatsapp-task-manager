#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     WhatsApp Task Manager — Setup      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# ── Install Homebrew, Node, Python ───────────────────────────────
echo -e "${BLUE}Checking system dependencies...${NC}"
echo ""

# Homebrew
if ! command -v brew &>/dev/null; then
    echo "  Installing Homebrew (this may take a few minutes)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for Apple Silicon Macs
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
    echo -e "  ${GREEN}✓ Homebrew installed${NC}"
else
    echo -e "  ${GREEN}✓ Homebrew already installed${NC}"
fi

# Node.js
if ! command -v node &>/dev/null; then
    echo "  Installing Node.js..."
    brew install node
    echo -e "  ${GREEN}✓ Node.js installed${NC}"
else
    echo -e "  ${GREEN}✓ Node.js already installed${NC}"
fi

# Python
if ! command -v python3 &>/dev/null; then
    echo "  Installing Python..."
    brew install python
    echo -e "  ${GREEN}✓ Python installed${NC}"
else
    echo -e "  ${GREEN}✓ Python already installed${NC}"
fi

echo ""

# ── Step 1: Gmail address ──────────────────────────────────────────
echo -e "${BLUE}Step 1 of 3 — Your Gmail address${NC}"
echo ""
read -p "  Enter your Gmail address: " GMAIL_USER
echo ""

# ── Step 2: Gmail App Password ────────────────────────────────────
echo -e "${BLUE}Step 2 of 3 — Gmail App Password${NC}"
echo ""
echo "  We need a one-time App Password from Google."
echo "  This lets the app send emails on your behalf."
echo ""
echo -e "  ${YELLOW}Follow these steps:${NC}"
echo "  1. Go to: https://myaccount.google.com/apppasswords"
echo "  2. Sign in if asked"
echo "  3. Click 'Create a new app password'"
echo "  4. Type the name: WhatsApp Digest"
echo "  5. Click 'Create' — Google will show a 16-character password"
echo "  6. Copy it and paste it below (spaces don't matter)"
echo ""
open "https://myaccount.google.com/apppasswords" 2>/dev/null || true
echo ""
read -p "  Paste your App Password here: " RAW_PASSWORD
GMAIL_APP_PASSWORD="${RAW_PASSWORD// /}"  # strip spaces
echo ""

# ── Step 3: Write .env ────────────────────────────────────────────
echo -e "${BLUE}Step 3 of 3 — Saving your settings${NC}"
echo ""

cat > "$DIR/.env" <<EOF
ANTHROPIC_API_KEY=YOUR_KEY_HERE
GMAIL_USER=$GMAIL_USER
GMAIL_APP_PASSWORD=$GMAIL_APP_PASSWORD
TO_EMAIL=$GMAIL_USER
EOF

echo -e "  ${GREEN}✓ Settings saved${NC}"
echo ""

# ── API Key ───────────────────────────────────────────────────────
echo -e "${YELLOW}⚠️  One manual step required:${NC}"
echo ""
echo "  Open the file: $DIR/.env"
echo "  Replace YOUR_KEY_HERE with the actual API key"
echo ""
echo "  Once done, come back here and press Enter to continue."
read -p "  Press Enter when the API key is added..."
echo ""

# ── Install dependencies ──────────────────────────────────────────
echo -e "${BLUE}Installing dependencies...${NC}"
cd "$DIR/whatsapp-fetcher" && npm install --silent 2>/dev/null
pip3 install anthropic -q 2>/dev/null
echo -e "  ${GREEN}✓ Done${NC}"
echo ""

# ── WhatsApp QR scan ──────────────────────────────────────────────
echo -e "${BLUE}Now let's connect your WhatsApp.${NC}"
echo ""
echo "  1. Open WhatsApp on your phone"
echo "  2. Tap Settings → Linked Devices → Link a Device"
echo "  3. Scan the QR code that appears below"
echo ""
read -p "  Press Enter when your phone is ready..."
echo ""

cd "$DIR"
node whatsapp-fetcher/fetch.js

echo ""
echo -e "${BLUE}Analysing your conversations...${NC}"
python3 python-analyzer/analyze.py

echo ""
echo -e "${BLUE}Sending your first digest email...${NC}"
python3 python-analyzer/send_email.py

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         All done! Check your inbox.    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "  Every night at 9pm, you'll automatically"
echo "  receive a summary of your WhatsApp open items."
echo ""

# ── Set up nightly cron ───────────────────────────────────────────
CRON_LINE="0 21 * * * $DIR/run.sh"
if ! crontab -l 2>/dev/null | grep -qF "$DIR/run.sh"; then
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
fi
