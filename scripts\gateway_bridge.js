const crypto = require('crypto');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const http = require('http');

const KEY_FILE = path.join(__dirname, '.gateway_key.json');
const CLAWVIZ_API = 'http://127.0.0.1:18998/api/chat/last';
const POLL_INTERVAL = 2000; // 2s poll for new ClawViz messages

function getToken() {
  try {
    const cfg = JSON.parse(fs.readFileSync(process.env.USERPROFILE + '\\.qclaw\\openclaw.json', 'utf8'));
    return cfg?.gateway?.auth?.token || cfg?.gateway?.token || '';
  } catch { return ''; }
}

const TOKEN = getToken();
const GATEWAY_URL = 'ws://127.0.0.1:28789';

// Generate fresh keypair and save it
function generateIdentity() {
  const k = crypto.generateKeyPairSync('ed25519', {
    publicKeyEncoding: { type: 'spki', format: 'der' },
    privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
  });
  const rawPub = k.publicKey.subarray(-32);
  const identity = {
    deviceId: crypto.createHash('sha256').update(rawPub).digest('hex'),
    pubKeyB64: Buffer.from(rawPub).toString('base64url'),
    privKeyPem: k.privateKey.toString(),
    createdAt: Date.now()
  };
  fs.writeFileSync(KEY_FILE, JSON.stringify(identity, null, 2));
  console.log('New identity generated, deviceId:', identity.deviceId);
  console.log('Approve with: openclaw devices approve <requestId>');
  return identity;
}

function loadIdentity() {
  try {
    const data = JSON.parse(fs.readFileSync(KEY_FILE, 'utf8'));
    console.log('Using saved identity, deviceId:', data.deviceId);
    return data;
  } catch {
    return generateIdentity();
  }
}

let lastForwardedTs = Date.now();
let pollTimer = null;

function forwardToGateway(ws, message) {
  ws.send(JSON.stringify({
    type: 'req', id: crypto.randomUUID(), method: 'chat.send',
    params: { sessionKey: 'agent:main:main', message, idempotencyKey: crypto.randomUUID() }
  }));
}

function pollClawViz(ws) {
  http.get(CLAWVIZ_API, (res) => {
    let data = '';
    res.on('data', (c) => { data += c; });
    res.on('end', () => {
      try {
        const json = JSON.parse(data);
        const msgs = json.messages || [];
        for (const m of msgs) {
          const msgTs = new Date(m.timestamp).getTime();
          if (msgTs > lastForwardedTs && m.user && m.user.startsWith('[WB]')) {
            const text = m.user || '';
            console.log(`[poll] Forwarding WB msg: ${text.substring(0, 60)}...`);
            forwardToGateway(ws, `[WB] ${text}`);
            if (msgTs > lastForwardedTs) lastForwardedTs = msgTs;
          }
        }
      } catch(e) { /* ignore parse errors */ }
    });
  }).on('error', () => { /* ClawViz down, will retry next poll */ });
}

function connect(identity) {
  let ws = null;
  let paired = false;
  let reconnectTimer = null;

  function doConnect() {
    if (pollTimer) clearInterval(pollTimer);
    ws = new WebSocket(GATEWAY_URL, { origin: 'http://127.0.0.1:18789' });
    paired = false;

    ws.on('open', () => {});
    
    ws.on('message', (d) => {
      const m = JSON.parse(d.toString());
      
      if (m.event === 'connect.challenge') {
        const nonce = m.payload.nonce;
        const ts = m.payload.ts || Date.now();
        const payload = [
          'v2', identity.deviceId, 'openclaw-control-ui', 'webchat',
          'operator', 'operator.admin,operator.read,operator.write',
          String(ts), TOKEN, nonce
        ].join('|');
        const sig = crypto.sign(null, Buffer.from(payload, 'utf8'), identity.privKeyPem).toString('base64url');

        ws.send(JSON.stringify({
          type: 'req', id: crypto.randomUUID(), method: 'connect',
          params: {
            minProtocol: 1, maxProtocol: 5,
            client: { id: 'openclaw-control-ui', version: '1.0', platform: 'web', mode: 'webchat' },
            role: 'operator',
            scopes: ['operator.admin', 'operator.read', 'operator.write'],
            device: {
              id: identity.deviceId,
              publicKey: identity.pubKeyB64,
              signature: sig,
              signedAt: ts,
              nonce: nonce
            },
            auth: { token: TOKEN }
          }
        }));
        console.log('Connect request sent');
      }

      if (m.type === 'res' && m.ok && m.payload?.type === 'hello-ok') {
        if (!paired) {
          paired = true;
          console.log('=== CONNECTED (hello-ok) ===');
          // Send startup beacon
          const initMsg = process.argv[2] || '[ClawViz] 桥接已建立';
          forwardToGateway(ws, initMsg);
          console.log('Startup beacon sent:', initMsg);
          // Start polling ClawViz for WB messages
          pollTimer = setInterval(() => pollClawViz(ws), POLL_INTERVAL);
          console.log(`Polling ClawViz every ${POLL_INTERVAL}ms for [WB] messages`);
        }
      }
    });

    ws.on('close', (code) => {
      console.log(`WS closed (code=${code}), reconnecting in 3s...`);
      if (pollTimer) clearInterval(pollTimer);
      paired = false;
      reconnectTimer = setTimeout(() => doConnect(), 3000);
    });

    ws.on('error', (e) => {
      console.log('WS error:', e.message);
      // ws.on('close') will fire next, triggering reconnect
    });
  }

  doConnect();
}

// Main
const identity = loadIdentity();
console.log('Gateway Bridge (persistent) starting...');
console.log('Device:', identity.deviceId);
console.log('Token:', TOKEN.substring(0,8) + '...');
connect(identity);

// Keep alive
process.stdin.resume();
process.on('SIGINT', () => { console.log('Shutting down...'); process.exit(0); });
