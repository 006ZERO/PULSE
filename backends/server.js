const express = require('express');
const http    = require('http');
const path    = require('path');
const fs      = require('fs');
const WebSocket = require('ws');

const app    = express();
const server = http.createServer(app);
const wss    = new WebSocket.Server({ server });
let lastTelemetryAt = 0;
const dataDir = path.join(__dirname, '..', 'data');
const sessionsFile = path.join(dataDir, 'sessions.json');
fs.mkdirSync(dataDir, { recursive: true });
if (!fs.existsSync(sessionsFile)) fs.writeFileSync(sessionsFile, '[]\n');

app.use(express.json({ limit: '256kb' }));

function readSessions() {
    try { return JSON.parse(fs.readFileSync(sessionsFile, 'utf8')); }
    catch (_) { return []; }
}

function writeSessions(sessions) {
    const temporary = `${sessionsFile}.tmp`;
    fs.writeFileSync(temporary, `${JSON.stringify(sessions, null, 2)}\n`);
    fs.renameSync(temporary, sessionsFile);
}

function broadcast(payload, except = null) {
    const message = typeof payload === 'string' ? payload : JSON.stringify(payload);
    wss.clients.forEach(client => {
        if (client !== except && client.readyState === WebSocket.OPEN)
            client.send(message);
    });
}

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'dashboard.html'));
});

app.get('/api/health', (req, res) => {
    res.json({
        server: 'ok',
        telemetry: Date.now() - lastTelemetryAt < 3000 ? 'live' : 'stale',
        last_packet_at: lastTelemetryAt || null,
        websocket_clients: wss.clients.size,
        sessions: readSessions().length
    });
});

app.get('/api/sessions', (req, res) => {
    res.json(readSessions().slice(0, 100));
});

app.post('/api/sessions', (req, res) => {
    const body = req.body || {};
    if (typeof body.athlete !== 'string' || !body.athlete.trim() || body.athlete.length > 40)
        return res.status(400).json({ error: 'A valid athlete name is required.' });
    const session = {
        id: `session_${Date.now()}`,
        athlete: body.athlete.trim(),
        date: typeof body.date === 'string' ? body.date : new Date().toISOString(),
        duration: typeof body.duration === 'string' ? body.duration : '0:00',
        avg: Number.isFinite(body.avg) ? body.avg : null,
        peak: Number.isFinite(body.peak) ? body.peak : null,
        status: 'Completed',
        alerts: Number.isInteger(body.alerts) ? Math.max(0, body.alerts) : 0
    };
    const sessions = readSessions();
    sessions.unshift(session);
    writeSessions(sessions.slice(0, 200));
    res.status(201).json(session);
});

wss.on('connection', (ws) => {
    ws.send(JSON.stringify({
        type: 'source_status',
        connected: Date.now() - lastTelemetryAt < 3000,
        last_packet_at: lastTelemetryAt || null
    }));

    ws.on('message', (message) => {
        const text = message.toString();
        try {
            const packet = JSON.parse(text);
            if (typeof packet.heart_rate === 'number') {
                lastTelemetryAt = Date.now();
                broadcast(text, ws);
                broadcast({ type: 'source_status', connected: true, last_packet_at: lastTelemetryAt }, ws);
                return;
            }
        } catch (_) {}
        broadcast(text, ws);
    });
});

setInterval(() => {
    if (lastTelemetryAt && Date.now() - lastTelemetryAt >= 3000)
        broadcast({ type: 'source_status', connected: false, last_packet_at: lastTelemetryAt });
}, 1000);

server.listen(3000, () => console.log('http://localhost:3000'));
