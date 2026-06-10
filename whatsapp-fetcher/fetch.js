const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

const OUTPUT_FILE = path.join(__dirname, '..', 'messages.json');
const HOURS_BACK = parseInt(process.env.HOURS_BACK || '24');

async function fetchMessages() {
    const client = new Client({
        authStrategy: new LocalAuth({ dataPath: path.join(__dirname, '.wwebjs_auth') }),
        puppeteer: {
            headless: true,
            protocolTimeout: 120000,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        }
    });

    client.on('qr', (qr) => {
        console.log('\nScan this QR code with WhatsApp on your phone:\n');
        qrcode.generate(qr, { small: true });
        console.log('\nWaiting for scan...');
    });

    client.on('authenticated', () => console.log('Authenticated.'));
    client.on('auth_failure', (msg) => { console.error('Auth failed:', msg); process.exit(1); });

    await new Promise((resolve, reject) => {
        client.on('ready', resolve);
        client.on('disconnected', () => reject(new Error('Client disconnected')));
        client.initialize().catch(reject);
    });

    console.log('WhatsApp connected. Waiting for chats to load...');
    await new Promise(r => setTimeout(r, 120000));
    console.log('Fetching messages...');

    const cutoff = Date.now() - HOURS_BACK * 60 * 60 * 1000;
    // Fetch chats in batches to avoid protocol timeout on slower machines
    let chats;
    let retries = 3;
    while (retries > 0) {
        try {
            chats = await client.getChats();
            break;
        } catch (e) {
            retries--;
            if (retries === 0) throw e;
            console.log(`Retrying getChats... (${retries} attempts left)`);
            await new Promise(r => setTimeout(r, 10000));
        }
    }

    const result = [];

    for (const chat of chats) {
        // Skip broadcast lists
        if (chat.id.server === 'broadcast') continue;

        const messages = await chat.fetchMessages({ limit: 100 });
        const recent = messages.filter(m => m.timestamp * 1000 >= cutoff);

        if (recent.length === 0) continue;

        const formatted = recent.map(m => ({
            id: m.id.id,
            from: m.fromMe ? 'me' : (m.author || m.from),
            body: m.body,
            timestamp: new Date(m.timestamp * 1000).toISOString(),
            isMe: m.fromMe,
            type: m.type,
        }));

        result.push({
            chatName: chat.name,
            chatId: chat.id._serialized,
            isGroup: chat.isGroup,
            messages: formatted,
        });
    }

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(result, null, 2));
    console.log(`Saved ${result.length} chats to messages.json`);

    await client.destroy();
}

fetchMessages().catch(err => {
    console.error('Error:', err);
    process.exit(1);
});
