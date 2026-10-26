import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.security import mask_phone_number, verify_hub_signature

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_get_verification_success():
    challenge = "1158201444"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.META_VERIFY_TOKEN,
        "hub.challenge": challenge,
    }
    response = client.get("/webhook", params=params)
    assert response.status_code == 200
    assert response.text == challenge


def test_webhook_get_verification_invalid_token():
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "token_falso_incorrecto",
        "hub.challenge": "1158201444",
    }
    response = client.get("/webhook", params=params)
    assert response.status_code == 403
    assert response.json()["detail"] == "Verification token mismatch"


def test_webhook_get_verification_invalid_mode():
    params = {
        "hub.mode": "unsubscribe",
        "hub.verify_token": settings.META_VERIFY_TOKEN,
        "hub.challenge": "1158201444",
    }
    response = client.get("/webhook", params=params)
    assert response.status_code == 403


def test_webhook_post_valid_signature():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15551234567",
                                "phone_number_id": "1234567890",
                            },
                            "messages": [
                                {
                                    "from": "584121234567",
                                    "id": "wamid.HBgL...",
                                    "timestamp": "1730000000",
                                    "text": {"body": "cantv"},
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

    response = client.post("/webhook", content=raw_body, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


def test_webhook_post_invalid_signature():
    raw_body = b'{"test": "payload"}'
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=firma_falsa_e_invalida_1234567890abcdef",
    }

    response = client.post("/webhook", content=raw_body, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature"


def test_webhook_post_missing_signature():
    raw_body = b'{"test": "payload"}'
    headers = {"Content-Type": "application/json"}

    response = client.post("/webhook", content=raw_body, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature"


def test_webhook_post_malformed_signature_prefix():
    raw_body = b'{"test": "payload"}'
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "invalido_sin_sha256_prefijo",
    }

    response = client.post("/webhook", content=raw_body, headers=headers)
    assert response.status_code == 403


def test_mask_phone_number():
    assert mask_phone_number("584121234567") == "58412***4567"
    assert mask_phone_number("+58-412-1234567") == "58412***4567"
    assert mask_phone_number("123") == "***"
