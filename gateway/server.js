const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const express = require('express');
const pino = require('pino');
const qrcodeTerminal = require('qrcode-terminal');
const QRCode = require('qrcode');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

const PORT = process.env.GATEWAY_PORT || 3001;
const FASTAPI_WEBHOOK_URL = process.env.FASTAPI_WEBHOOK_URL || 'http://localhost:8000/gateway/incoming';
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');

let sock = null;
let currentQR = null;
let currentQRDataUrl = null;
let connectionStatus = 'initializing';
let connectedUser = null;

// Logger silencioso para Baileys para no saturar la consola
const logger = pino({ level: 'silent' });

async function connectToWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  connectionStatus = 'connecting';
  console.log('[Gateway] Iniciando conector WhatsApp Web...');

  sock = makeWASocket({
    version,
    logger,
    printQRInTerminal: false, // Lo manejamos manualmente con qrcode-terminal
    auth: state,
    browser: ['BotAZ AJUPTEL', 'Chrome', '1.0.0']
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQR = qr;
      connectionStatus = 'qr_ready';
      try {
        currentQRDataUrl = await QRCode.toDataURL(qr);
      } catch (err) {
        console.error('[Gateway] Error generando QR data URL:', err);
      }

      console.log('\n=============================================================');
      console.log('>>> ESCANEA ESTE CÓDIGO QR CON TU WHATSAPP (VINCULAR DISPOSITIVO) <<<');
      console.log('=============================================================\n');
      qrcodeTerminal.generate(qr, { small: true });
      console.log('\nTambién puedes ver el QR en tu navegador: http://localhost:8000/qr');
      console.log('O directamente en el gateway: http://localhost:3001/qr\n');
    }

    if (connection === 'close') {
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      connectionStatus = 'disconnected';
      currentQR = null;
      currentQRDataUrl = null;
      console.log(`[Gateway] Conexión cerrada (código ${statusCode}). Reconectando: ${shouldReconnect}`);

      if (shouldReconnect) {
        setTimeout(connectToWhatsApp, 3000);
      } else {
        console.log('[Gateway] Sesión cerrada permanentemente. Limpiando credenciales...');
        fs.rmSync(AUTH_DIR, { recursive: true, force: true });
        setTimeout(connectToWhatsApp, 2000);
      }
    } else if (connection === 'open') {
      connectionStatus = 'connected';
      currentQR = null;
      currentQRDataUrl = null;
      connectedUser = sock.user?.id || 'Desconocido';
      console.log('\n=============================================================');
      console.log(`[Gateway] ¡CONECTADO CON ÉXITO A WHATSAPP!`);
      console.log(`Usuario: ${connectedUser}`);
      console.log('=============================================================\n');
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return;

    for (const msg of messages) {
      if (!msg.message) continue;
      if (msg.key.fromMe) continue; // Ignorar mensajes enviados por el propio bot

      const remoteJid = msg.key.remoteJid;
      if (!remoteJid || remoteJid.includes('@g.us') || remoteJid.includes('broadcast')) {
        continue; // Ignorar grupos y difusiones de estado
      }

      // Preservar JID original intacto (@s.whatsapp.net o @lid)
      const senderJid = remoteJid;
      const wamid = msg.key.id;

      // Extraer texto
      let text = '';
      let msgType = 'text';

      if (msg.message.conversation) {
        text = msg.message.conversation;
      } else if (msg.message.extendedTextMessage?.text) {
        text = msg.message.extendedTextMessage.text;
      } else if (msg.message.imageMessage) {
        msgType = 'image';
        text = msg.message.imageMessage.caption || '';
      } else if (msg.message.audioMessage) {
        msgType = 'audio';
      } else if (msg.message.stickerMessage) {
        msgType = 'sticker';
      } else {
        msgType = Object.keys(msg.message)[0] || 'unknown';
      }

      console.log(`[Gateway] Mensaje entrante de ${senderJid}: "${text}" (tipo: ${msgType})`);

      // Reenviar a FastAPI
      try {
        const payload = {
          wamid: wamid,
          from: senderJid,
          jid: senderJid,
          text: text,
          type: msgType
        };

        const response = await fetch(FASTAPI_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          console.error(`[Gateway] FastAPI respondió con status ${response.status}`);
        }
      } catch (err) {
        console.error('[Gateway] Error comunicando con FastAPI:', err.message);
      }
    }
  });
}

// Endpoint para consultar el estado
app.get('/status', (req, res) => {
  res.json({
    status: connectionStatus,
    user: connectedUser,
    has_qr: !!currentQR
  });
});

// Endpoint para visualizar el código QR en navegador
app.get('/qr', (req, res) => {
  if (connectionStatus === 'connected') {
    return res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>BotAZ WhatsApp Gateway - Conectado</title>
        <meta charset="utf-8">
        <style>
          body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: #0f172a; color: #f8fafc; }
          .card { background: #1e293b; padding: 2rem; border-radius: 1rem; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
          .badge { background: #10b981; color: white; padding: 0.5rem 1rem; border-radius: 9999px; font-weight: bold; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>✅ BotAZ WhatsApp Conectado</h1>
          <p><span class="badge">ACTIVO</span></p>
          <p>Dispositivo vinculado: <strong>${connectedUser || 'Listo'}</strong></p>
          <p>El bot está procesando consultas y respondiendo normalmente.</p>
        </div>
      </body>
      </html>
    `);
  }

  if (currentQRDataUrl) {
    return res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Vincular WhatsApp - BotAZ</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="5">
        <style>
          body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; background: #0f172a; color: #f8fafc; margin: 0; }
          .card { background: #1e293b; padding: 2.5rem; border-radius: 1rem; text-align: center; max-width: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
          img { border-radius: 0.5rem; margin: 1.5rem 0; background: white; padding: 10px; }
          .instructions { text-align: left; background: #334155; padding: 1rem; border-radius: 0.5rem; font-size: 0.9rem; line-height: 1.5; }
        </style>
      </head>
      <body>
        <div class="card">
          <h2>📱 Vincular WhatsApp BotAZ</h2>
          <p>Escanea el código QR con tu WhatsApp móvil para conectar el bot:</p>
          <img src="${currentQRDataUrl}" alt="Código QR WhatsApp" width="280" height="280" />
          <div class="instructions">
            <strong>Instrucciones:</strong><br/>
            1. Abre WhatsApp en tu teléfono.<br/>
            2. Toca <strong>Menú (⋮)</strong> o <strong>Configuración</strong>.<br/>
            3. Selecciona <strong>Dispositivos vinculados</strong>.<br/>
            4. Toca <strong>Vincular un dispositivo</strong> y apunta la cámara a esta pantalla.
          </div>
          <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 1rem;">La página se actualiza automáticamente cada 5 segundos.</p>
        </div>
      </body>
      </html>
    `);
  }

  return res.send(`
    <!DOCTYPE html>
    <html>
    <head><meta http-equiv="refresh" content="3"><title>Iniciando...</title></head>
    <body style="font-family: sans-serif; text-align: center; padding-top: 5rem; background: #0f172a; color: white;">
      <h2>Iniciando conector de WhatsApp...</h2>
      <p>Esperando generación del código QR...</p>
    </body>
    </html>
  `);
});

// Endpoint JSON para obtener datos del QR
app.get('/qr-data', (req, res) => {
  res.json({
    status: connectionStatus,
    qr: currentQR,
    qr_data_url: currentQRDataUrl
  });
});

// Endpoint para enviar mensajes salientes desde FastAPI
app.post('/send', async (req, res) => {
  const { to, jid: reqJid, type, url, image_url, caption, text, message: reqMessage } = req.body;

  if (!sock || connectionStatus !== 'connected') {
    return res.status(503).json({
      success: false,
      error: 'WhatsApp no está conectado todavía',
      status: connectionStatus
    });
  }

  const rawTarget = reqJid || to;
  if (!rawTarget) {
    return res.status(400).json({
      success: false,
      error: 'Falta el destinatario (jid o to)'
    });
  }

  const targetStr = String(rawTarget).trim();
  let jid = '';

  // 1. Si el JID de destino contiene '@lid', se usa exactamente ese JID completo
  if (targetStr.includes('@lid')) {
    jid = targetStr;
  // 2. Si el JID termina en '@s.whatsapp.net', se mantiene tal cual
  } else if (targetStr.endsWith('@s.whatsapp.net')) {
    jid = targetStr;
  // 3. Si solo vienen dígitos (ej. 584141234567), se anexa '@s.whatsapp.net'
  } else {
    const cleanDigits = targetStr.replace(/\D/g, '');
    jid = `${cleanDigits}@s.whatsapp.net`;
  }

  const targetUrl = url || image_url;
  const isImage = type === 'image' || Boolean(targetUrl);
  const targetCaption = caption !== undefined ? caption : (text !== undefined ? text : (reqMessage || ''));
  const messageText = text !== undefined ? text : (reqMessage || '');

  // 4. Bloque try/catch para capturar excepciones al llamar a sock.sendMessage y retornar JSON claro sin colapsar con 500
  try {
    let sentMessage = null;
    if (isImage) {
      try {
        sentMessage = await sock.sendMessage(jid, {
          image: { url: targetUrl },
          caption: targetCaption || ''
        });
      } catch (imgErr) {
        console.warn(`[Gateway] Falló envío de imagen desde ${targetUrl} (${imgErr.message}). Enviando solo texto como respaldo...`);
        sentMessage = await sock.sendMessage(jid, {
          text: targetCaption || messageText
        });
      }
    } else {
      // Respuesta de texto normal
      sentMessage = await sock.sendMessage(jid, {
        text: messageText
      });
    }

    return res.json({
      success: true,
      messageId: sentMessage?.key?.id,
      to: jid,
      jid: jid
    });
  } catch (err) {
    console.error(`[Gateway] Error al enviar mensaje a ${jid}:`, err.message || err);
    return res.status(200).json({
      success: false,
      error: `Error al enviar mensaje vía WhatsApp: ${err.message || 'Error desconocido'}`,
      jid: jid
    });
  }
});

// Iniciar servidor express y conector Baileys
app.listen(PORT, () => {
  console.log(`[Gateway] Servidor QR Gateway activo en http://localhost:${PORT}`);
  connectToWhatsApp();
});
