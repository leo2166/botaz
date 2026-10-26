import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.whatsapp_adapter import WhatsAppGatewayAdapter

client = TestClient(app)


def test_gateway_status_endpoint():
    with patch("app.main.whatsapp_adapter.get_status", new_callable=AsyncMock) as mock_status:
        mock_status.return_value = {"status": "connected", "user": "584121234567@s.whatsapp.net"}
        response = client.get("/gateway/status")
        assert response.status_code == 200
        assert response.json()["status"] == "connected"


def test_qr_page_endpoint():
    # Caso 1: QR listo para escanear
    with patch("app.main.whatsapp_adapter.get_qr_data", new_callable=AsyncMock) as mock_qr:
        mock_qr.return_value = {
            "status": "qr_ready",
            "qr": "2@xyz123...",
            "qr_data_url": "data:image/png;base64,iVBORw0KGgo..."
        }
        response = client.get("/qr")
        assert response.status_code == 200
        assert "Vincular WhatsApp BotAZ" in response.text
        assert "data:image/png;base64" in response.text

    # Caso 2: Ya conectado
    with patch("app.main.whatsapp_adapter.get_qr_data", new_callable=AsyncMock) as mock_qr:
        mock_qr.return_value = {
            "status": "connected",
            "qr_data_url": None
        }
        response = client.get("/qr")
        assert response.status_code == 200
        assert "WhatsApp Conectado" in response.text


def test_gateway_incoming_message_endpoint():
    payload = {
        "wamid": "wamid.gateway_test_001",
        "from": "584121112233",
        "text": "averia de cantv",
        "type": "text"
    }

    with patch("app.main.handle_incoming_message", new_callable=AsyncMock) as mock_handle:
        response = client.post("/gateway/incoming", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_whatsapp_gateway_adapter_send():
    async def _test():
        adapter = WhatsAppGatewayAdapter()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "messageId": "wamid.sent_001"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            res = await adapter.send_response(
                to="584121112233",
                text="Respuesta de averia",
                image_url="https://example.com/cantv.png"
            )
            assert res is not None
            assert res["success"] is True
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert payload["to"] == "584121112233"
            assert payload["jid"] == "584121112233"
            assert payload["image_url"] == "https://example.com/cantv.png"
            assert payload["text"] == "Respuesta de averia"

    asyncio.run(_test())


def test_whatsapp_gateway_adapter_send_lid_format():
    async def _test():
        adapter = WhatsAppGatewayAdapter()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"success": True, "messageId": "wamid.sent_lid_001"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            lid_user = "12373968605285@lid"
            res = await adapter.send_response(
                to=lid_user,
                text="Respuesta para usuario LID",
            )
            assert res is not None
            assert res["success"] is True
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert payload["to"] == lid_user
            assert payload["jid"] == lid_user
            assert payload["text"] == "Respuesta para usuario LID"

    asyncio.run(_test())

