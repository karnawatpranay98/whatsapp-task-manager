import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).parent.parent
OPEN_ITEMS_FILE = ROOT / 'open_items.txt'

# Load .env file
env_file = ROOT / '.env'
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ[k.strip()] = v.strip()

GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_APP_PASSWORD = os.environ['GMAIL_APP_PASSWORD']
TO_EMAIL = os.environ.get('TO_EMAIL', GMAIL_USER)


def parse_items(plain_text: str) -> list[dict]:
    import re
    items = []
    blocks = re.split(r'\n---\n', plain_text.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        item = {}

        # Format A: ### 1. Title
        m = re.search(r'###\s+(?:\d+\.\s+)?(.*)', block)
        if m:
            item['title'] = m.group(1).strip()

        # Format B: **1. Chat Name (Direct)**
        if not item.get('title'):
            m = re.search(r'\*\*\d+\.\s+(.*?)\*\*', block)
            if m:
                item['title'] = m.group(1).strip()

        # Chat field
        for label in ['Chat', 'chat']:
            m = re.search(rf'\*\*{label}:\*\*\s*(.*)', block)
            if m:
                item['chat'] = m.group(1).strip()
                break

        # Description / Item field
        for label in ['Description', 'Item', 'description']:
            m = re.search(rf'\*\*{label}:\*\*\s*(.*)', block)
            if m:
                item['description'] = m.group(1).strip()
                break

        # Why open
        m = re.search(r'\*\*Why open:\*\*\s*(.*)', block)
        if m:
            item['why_open'] = m.group(1).strip()

        # Priority — from field or from section header
        p_str = ''
        m = re.search(r'\*\*Priority:\*\*\s*(.*)', block)
        if m:
            p_str = m.group(1)
        elif '🔴' in plain_text[:plain_text.find(block) + 10] or 'HIGH' in plain_text[:plain_text.find(block) + 50]:
            p_str = 'High'

        if '🔴' in p_str or 'High' in p_str:
            item['priority'] = 'high'
        elif '🟡' in p_str or 'Medium' in p_str:
            item['priority'] = 'medium'
        else:
            item['priority'] = 'low'

        # Infer priority from section headers in the full text
        pos = plain_text.find(block[:40])
        preceding = plain_text[:pos]
        last_header = ''
        for hm in re.finditer(r'(HIGH|MEDIUM|LOW) PRIORITY', preceding, re.IGNORECASE):
            last_header = hm.group(1).upper()
        if last_header == 'HIGH':
            item['priority'] = 'high'
        elif last_header == 'MEDIUM':
            item['priority'] = 'medium'
        elif last_header == 'LOW':
            item['priority'] = 'low'

        if item.get('title'):
            items.append(item)
    return items


def priority_badge(p: str) -> str:
    if p == 'high':
        return '<span style="background:#fee2e2;color:#dc2626;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;letter-spacing:0.5px">HIGH</span>'
    if p == 'medium':
        return '<span style="background:#fef9c3;color:#b45309;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;letter-spacing:0.5px">MEDIUM</span>'
    return '<span style="background:#dbeafe;color:#1d4ed8;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;letter-spacing:0.5px">LOW</span>'


def render_item(i: int, item: dict) -> str:
    badge = priority_badge(item.get('priority', 'low'))
    chat = item.get('chat', '')
    desc = item.get('description', '')
    why = item.get('why_open', '')
    border = {'high': '#dc2626', 'medium': '#f59e0b', 'low': '#3b82f6'}.get(item.get('priority', 'low'), '#e5e7eb')
    return f"""
    <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border-left:4px solid {border};box-shadow:0 1px 4px rgba(0,0,0,0.06)">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
        <span style="background:#f3f4f6;color:#6b7280;font-size:12px;font-weight:700;width:24px;height:24px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center">{i}</span>
        <span style="font-size:16px;font-weight:700;color:#111827;flex:1">{item.get('title', '')}</span>
        {badge}
      </div>
      {'<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px"><span style="font-size:12px;color:#9ca3af">💬</span><span style="font-size:13px;color:#6b7280">' + chat + '</span></div>' if chat else ''}
      {'<p style="margin:0 0 8px;font-size:14px;color:#374151;line-height:1.6">' + desc + '</p>' if desc else ''}
      {'<div style="background:#f9fafb;border-radius:8px;padding:10px 14px;font-size:13px;color:#6b7280;line-height:1.5"><span style="font-weight:600;color:#374151">Why open: </span>' + why + '</div>' if why else ''}
    </div>"""


def build_html(plain_text: str) -> str:
    today = date.today().strftime('%A, %B %d %Y')
    items = parse_items(plain_text)

    high = [it for it in items if it.get('priority') == 'high']
    medium = [it for it in items if it.get('priority') == 'medium']
    low = [it for it in items if it.get('priority') == 'low']

    def section(label: str, color: str, subset: list, offset: int) -> str:
        if not subset:
            return ''
        cards = ''.join(render_item(offset + j + 1, it) for j, it in enumerate(subset))
        return f"""
        <div style="margin-bottom:28px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px">
            <div style="width:12px;height:12px;border-radius:50%;background:{color}"></div>
            <span style="font-size:13px;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:1px">{label} · {len(subset)}</span>
          </div>
          {cards}
        </div>"""

    body = (
        section('High Priority', '#dc2626', high, 0) +
        section('Medium Priority', '#f59e0b', medium, len(high)) +
        section('Low Priority', '#3b82f6', low, len(high) + len(medium))
    )

    if not items:
        body = '<p style="color:#6b7280;text-align:center;padding:40px 0">No open items found today.</p>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <div style="max-width:640px;margin:32px auto;padding:0 16px">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#25d366 0%,#128c7e 100%);border-radius:16px;padding:32px;margin-bottom:24px;text-align:center">
      <div style="font-size:36px;margin-bottom:8px">📋</div>
      <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700">WhatsApp Open Items</h1>
      <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:14px">{today}</p>
      <div style="display:inline-block;margin-top:16px;background:rgba(255,255,255,0.2);border-radius:999px;padding:6px 20px">
        <span style="color:#fff;font-size:14px;font-weight:600">{len(items)} items need your attention</span>
      </div>
    </div>

    <!-- Items -->
    {body}

    <!-- Footer -->
    <div style="text-align:center;padding:16px 0 32px">
      <p style="margin:0;font-size:12px;color:#9ca3af">Generated automatically · WhatsApp Task Manager</p>
    </div>
  </div>
</body>
</html>"""


def send_email(subject: str, plain_text: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = TO_EMAIL
    msg.attach(MIMEText(plain_text, 'plain'))
    msg.attach(MIMEText(build_html(plain_text), 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())

    print(f"Email sent to {TO_EMAIL}")


def main():
    if not OPEN_ITEMS_FILE.exists():
        print(f"Error: {OPEN_ITEMS_FILE} not found. Run analyze.py first.", file=sys.stderr)
        sys.exit(1)

    content = OPEN_ITEMS_FILE.read_text().strip()
    if not content:
        print("No open items found, skipping email.")
        return

    today = date.today().strftime('%b %d')
    send_email(f"WhatsApp Open Items — {today}", content)


if __name__ == '__main__':
    main()
