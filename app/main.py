import json
import logging
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.bot_service import handle_incoming_message, process_webhook_payload
from app.config import settings
from app.security import verify_hub_signature
from app.whatsapp_adapter import whatsapp_adapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("botAZ.main")

app = FastAPI(
    title="BotAZ - WhatsApp Cloud API Bot",
    description="Bot oficial de WhatsApp para AJUPTEL Zulia",
    version="1.0.0"
)


@app.get("/health", tags=["Monitoreo"])
async def health_check():
    """Endpoint de salud para monitoreo externo (UptimeRobot) y keep-alive."""
    return {"status": "ok"}


@app.get("/webhook", tags=["Meta Webhook"])
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Validación inicial del Webhook de WhatsApp Cloud API (Meta).
    Meta envía hub.mode='subscribe', hub.verify_token y hub.challenge.
    Se debe responder con hub.challenge en texto plano y status 200 si coincide el token.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("Verificación exitosa del Webhook de Meta.")
        return PlainTextResponse(content=hub_challenge or "", status_code=200)

    logger.warning("Fallo de verificación de token en GET /webhook.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@app.post("/webhook", tags=["Meta Webhook"])
async def receive_webhook_event(request: Request, background_tasks: BackgroundTasks):
    """
    Recepción de eventos de Meta WhatsApp Cloud API.
    Valida la firma criptográfica obligatoria X-Hub-Signature-256
    sobre los bytes crudos antes de cualquier procesamiento.
    Responde 200 OK inmediatamente a Meta y delega el procesamiento a BackgroundTasks.
    """
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not verify_hub_signature(raw_body, signature_header, settings.META_APP_SECRET):
        logger.warning("Rechazada petición POST /webhook: firma X-Hub-Signature-256 inválida o ausente.")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as exc:
        logger.error("Error decodificando JSON de webhook: %s", str(exc))
        payload = {}

    # Despachar procesamiento asíncrono en segundo plano
    if payload:
        background_tasks.add_task(process_webhook_payload, payload)

    return {"status": "received"}


@app.post("/gateway/incoming", tags=["QR Gateway"])
async def receive_gateway_message(request: Request, background_tasks: BackgroundTasks):
    """
    Recepción de mensajes entrantes desde el conector WhatsApp Web QR (Baileys).
    Despacha el procesamiento del mensaje en segundo plano.
    """
    try:
        data = await request.json()
    except Exception as exc:
        logger.error("Error decodificando payload de Gateway: %s", str(exc))
        data = {}

    if data:
        background_tasks.add_task(handle_incoming_message, data)

    return {"status": "ok"}


@app.get("/qr", tags=["QR Gateway"], response_class=HTMLResponse)
async def view_qr_code():
    """Muestra la página interactiva para escanear el código QR de WhatsApp Web."""
    qr_data = await whatsapp_adapter.get_qr_data()
    status = qr_data.get("status")
    data_url = qr_data.get("qr_data_url")

    if status == "connected":
        return HTMLResponse(content="""
        <!DOCTYPE html><html><head><title>BotAZ Conectado</title><meta charset='utf-8'>
        <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#0f172a;color:#fff;}
        .card{background:#1e293b;padding:2.5rem;border-radius:1rem;text-align:center;box-shadow:0 10px 25px rgba(0,0,0,0.5);}
        .badge{background:#10b981;color:#fff;padding:6px 16px;border-radius:999px;font-weight:bold;display:inline-block;margin-bottom:1rem;}</style></head>
        <body><div class='card'><span class='badge'>ACTIVO</span><h1>✅ WhatsApp Conectado</h1>
        <p>El bot está vinculado y listo para procesar consultas y enviar imágenes.</p></div></body></html>
        """)

    if data_url:
        return HTMLResponse(content=f"""
        <!DOCTYPE html><html><head><title>Vincular WhatsApp - BotAZ</title><meta charset='utf-8'><meta http-equiv='refresh' content='5'>
        <style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#0f172a;color:#fff;margin:0;}}
        .card{{background:#1e293b;padding:2rem;border-radius:1rem;text-align:center;max-width:420px;box-shadow:0 10px 25px rgba(0,0,0,0.5);}}
        img{{border-radius:8px;background:white;padding:10px;margin:1rem 0;}}
        .instr{{background:#334155;padding:12px;border-radius:8px;text-align:left;font-size:0.85rem;line-height:1.5;}}</style></head>
        <body><div class='card'><h2>📱 Vincular WhatsApp BotAZ</h2><p>Escanea el código QR con tu teléfono:</p>
        <img src='{data_url}' width='260' height='260' alt='QR WhatsApp'/>
        <div class='instr'><strong>Pasos:</strong><br>1. Abre WhatsApp en tu celular.<br>2. Toca <strong>Dispositivos vinculados</strong>.<br>3. Toca <strong>Vincular un dispositivo</strong> y escanea este QR.</div>
        <p style='font-size:0.75rem;color:#94a3b8;margin-top:1rem;'>Actualización automática cada 5 segundos.</p></div></body></html>
        """)

    return HTMLResponse(content="""
    <!DOCTYPE html><html><head><meta http-equiv='refresh' content='3'><title>Iniciando Gateway...</title></head>
    <body style='font-family:sans-serif;text-align:center;padding-top:4rem;background:#0f172a;color:#fff;'>
    <h2>Iniciando Conector WhatsApp Web...</h2>
    <p>Asegúrate de que el Gateway en Node.js esté corriendo (<code>npm start</code> en la carpeta <code>gateway</code>).</p>
    </body></html>
    """)


@app.get("/gateway/status", tags=["QR Gateway"])
async def get_gateway_status():
    """Consulta el estado del conector WhatsApp QR."""
    return await whatsapp_adapter.get_status()

