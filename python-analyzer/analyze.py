import json
import os
import sys
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
MESSAGES_FILE = ROOT / 'messages.json'

# Load .env file
env_file = ROOT / '.env'
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

client = Anthropic()

SYSTEM_PROMPT = """You are an assistant that analyzes WhatsApp conversations and extracts actionable open items for the user (referred to as "me" or messages where isMe=true).

Your job is to identify:
1. Tasks or action items assigned to the user that haven't been completed
2. Questions asked of the user that haven't been answered
3. Commitments the user made that appear unresolved
4. Follow-ups the user said they would do but haven't
5. Pending decisions waiting for the user's input

Output ONLY in this exact format for each item, separated by ---:

### 1. [short title of the action item]
**Chat:** [chat name]
**Description:** [one sentence description]
**Why open:** [why it's unresolved]
**Priority:** High / Medium / Low

---

### 2. [short title]
...

Be concise. Only include genuinely open items — ignore resolved conversations."""


def load_messages():
    if not MESSAGES_FILE.exists():
        print(f"Error: {MESSAGES_FILE} not found. Run the WhatsApp fetcher first.", file=sys.stderr)
        sys.exit(1)
    with open(MESSAGES_FILE) as f:
        return json.load(f)


def format_chat_for_prompt(chat: dict) -> str:
    lines = [f"--- Chat: {chat['chatName']} ({'Group' if chat['isGroup'] else 'Direct'}) ---"]
    for msg in chat['messages']:
        sender = 'Me' if msg['isMe'] else msg['from']
        lines.append(f"[{msg['timestamp'][:16]}] {sender}: {msg['body']}")
    return '\n'.join(lines)


def analyze_messages(chats: list) -> str:
    if not chats:
        return "No recent WhatsApp messages found."

    # Build conversation text, stay within token limits
    chat_blocks = []
    total_chars = 0
    for chat in chats:
        block = format_chat_for_prompt(chat)
        if total_chars + len(block) > 80_000:  # ~20k tokens buffer
            break
        chat_blocks.append(block)
        total_chars += len(block)

    conversation_text = '\n\n'.join(chat_blocks)

    response = client.messages.create(
        model='claude-haiku-3-5',
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{
            'role': 'user',
            'content': f"Here are my WhatsApp conversations from the last 24 hours:\n\n{conversation_text}\n\nList all open items I need to action."
        }]
    )

    return response.content[0].text


def main():
    chats = load_messages()
    print(f"Analyzing {len(chats)} chats...")
    result = analyze_messages(chats)
    print(result)

    # Also save for the email sender to pick up
    output_file = ROOT / 'open_items.txt'
    output_file.write_text(result)
    print(f"\nSaved to {output_file}")


if __name__ == '__main__':
    main()
