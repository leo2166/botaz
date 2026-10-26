"""
Simulador de eventos Webhook de Meta para pruebas locales de integración.
Permite verificar la firma criptográfica HMAC SHA-256 y la respuesta del bot.

Uso:
  python scripts/simulate_meta_event.py --text "cantv"
  python scripts/simulate_meta_event.py --verify
  python scripts/simulate_meta_event.py --text "emergencia medica"
  python scripts/simulate_meta_event.py --text "desconocido"
"""

import argparse
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from app.config import settings


def test_verify_webhook(base_url: str):
    """Prueba la validación GET /webhook enviada por Meta al registrar el endpoint."""
    url = f"{base_url}/webhook"
    challenge = "123456789"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.META_VERIFY_TOKEN,
        "hub.challenge": challenge,
    }
    print(f"\n[GET /webhook] Probando verificación con token '{settings.META_VERIFY_TOKEN}'...")
    try:
        resp = httpx.get(url, params=params, timeout=5.0)
        print(f"Status Code: {resp.status_code}")
        print(f"Respuesta:   {resp.text}")
        if resp.status_code == 200 and resp.text == challenge:
            print("[ÉXITO] Verificación de token aprobada.")
        else:
            print("[FALLO] Verificación rechazada.")
    except Exception as exc:
        print(f"[ERROR] No se pudo conectar con el servidor: {exc}")


def send_simulated_message(base_url: str, text: str, sender_phone: str = "584121234567"):
    """Envía un webhook simulado de Meta con firma criptográfica HMAC-SHA256 válida."""
    url = f"{base_url}/webhook"
    wamid = f"wamid.sim_{int(time.time() * 1000)}"

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "SIMULATED_WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": settings.META_PHONE_NUMBER_ID,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Usuario Prueba"},
                                    "wa_id": sender_phone,
                                }
                            ],
                            "messages": [
                                {
                                    "from": sender_phone,
                                    "id": wamid,
                                    "timestamp": str(int(time.time())),
                                    "text": {"body": text},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    raw_body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        key=settings.META_APP_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={signature}",
    }

    print(f"\n[POST /webhook] Enviando mensaje: '{text}' (De: {sender_phone}, wamid: {wamid})")
    print(f"Firma HMAC: sha256={signature[:16]}...")
    try:
        resp = httpx.post(url, content=raw_body, headers=headers, timeout=5.0)
        print(f"Status Code: {resp.status_code}")
        print(f"Respuesta:   {resp.text}")
        if resp.status_code == 200:
            print("[ÉXITO] Webhook aceptado por el servidor local.")
        else:
            print("[FALLO] Servidor rechazó el webhook.")
    except Exception as exc:
        print(f"[ERROR] Fallo conectando al servidor: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de Webhooks de Meta")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base del servidor local")
    parser.add_argument("--text", default="cantv", help="Texto del mensaje a simular")
    parser.add_argument("--phone", default="584121234567", help="Número de teléfono remitente")
    parser.add_argument("--verify", action="store_true", help="Probar GET /webhook")

    args = parser.parse_args()

    if args.verify:
        test_verify_webhook(args.url)
    else:
        send_simulated_message(args.url, args.text, args.phone)
