import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.bot_service import handle_incoming_message, handle_status_update
from app.config import settings
from app.meta_client import MetaWhatsAppClient
from app.redis_client import UpstashRedisClient, get_next_month_name


@pytest.fixture
def mock_redis():
    """Provee una instancia limpia de UpstashRedisClient en memoria."""
    client = UpstashRedisClient()
    client._memory_store.clear()
    client._memory_expires.clear()
    return client


def test_meta_client_send_text():
    async def _test():
        client = MetaWhatsAppClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.HBgL..."}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            res = await client.send_text_message("584121234567", "Hola mundo")
            assert res is not None
            assert "messages" in res
            mock_post.assert_called_once()
            sent_payload = mock_post.call_args[1]["json"]
            assert sent_payload["type"] == "text"
            assert sent_payload["text"]["body"] == "Hola mundo"

    asyncio.run(_test())


def test_meta_client_send_image_with_caption():
    async def _test():
        client = MetaWhatsAppClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.HBgL..."}]}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            res = await client.send_response(
                to="584121234567",
                text="Texto de respuesta",
                image_url="https://example.com/imagen.png"
            )
            assert res is not None
            mock_post.assert_called_once()
            sent_payload = mock_post.call_args[1]["json"]
            assert sent_payload["type"] == "image"
            assert sent_payload["image"]["link"] == "https://example.com/imagen.png"
            assert sent_payload["image"]["caption"] == "Texto de respuesta"

    asyncio.run(_test())


def test_redis_wamid_deduplication(mock_redis):
    async def _test():
        wamid = "wamid.HBgL_UNIQUE_TEST_123"
        # Primera vez: debe ser True (mensaje fresco)
        assert await mock_redis.check_and_set_wamid(wamid) is True
        # Segunda vez: debe ser False (duplicado descartado)
        assert await mock_redis.check_and_set_wamid(wamid) is False

    asyncio.run(_test())


def test_redis_counter_and_alerts(mock_redis):
    async def _test():
        # Contador inicial en 0
        assert await mock_redis.get_monthly_count() == 0

        # Incrementos
        assert await mock_redis.increment_monthly_counter() == 1
        assert await mock_redis.increment_monthly_counter() == 2
        assert await mock_redis.get_monthly_count() == 2

        # Alerta al 70%: primera vez True, segunda vez False (ya enviada)
        assert await mock_redis.check_and_set_alert(70) is True
        assert await mock_redis.check_and_set_alert(70) is False

    asyncio.run(_test())


def test_status_update_increments_only_billable_delivered():
    async def _test():
        with patch("app.bot_service.redis_client.increment_monthly_counter", new_callable=AsyncMock) as mock_incr:
            mock_incr.return_value = 10

            # Status delivered billable: debe incrementar
            status_billable = {
                "status": "delivered",
                "pricing": {"billable": True, "category": "service"}
            }
            await handle_status_update(status_billable)
            mock_incr.assert_called_once()

            mock_incr.reset_mock()
            # Status delivered NO billable: NO debe incrementar
            status_free = {
                "status": "delivered",
                "pricing": {"billable": False}
            }
            await handle_status_update(status_free)
            mock_incr.assert_not_called()

            # Status 'sent' o 'read': NO debe incrementar
            status_sent = {
                "status": "sent",
                "pricing": {"billable": True}
            }
            await handle_status_update(status_sent)
            mock_incr.assert_not_called()

    asyncio.run(_test())


def test_incoming_message_keyword_match_below_threshold():
    async def _test():
        message = {
            "id": "wamid.test_normal_kw_001",
            "from": "584121112233",
            "type": "text",
            "text": {"body": "tengo averia en cantv"}
        }

        with patch("app.bot_service.redis_client.check_and_set_wamid", new_callable=AsyncMock, return_value=True), \
             patch("app.bot_service.redis_client.get_monthly_count", new_callable=AsyncMock, return_value=50), \
             patch("app.bot_service.meta_client.send_response", new_callable=AsyncMock) as mock_send:

            await handle_incoming_message(message)
            mock_send.assert_called_once()
            args = mock_send.call_args[1]
            assert args["to"] == "584121112233"
            assert "CANTV" in args["text"]
            assert args["image_url"] is not None

    asyncio.run(_test())


def test_incoming_message_fallback_menu():
    async def _test():
        message = {
            "id": "wamid.test_fallback_002",
            "from": "584121112233",
            "type": "text",
            "text": {"body": "ojala llueva mucho esta tarde"}
        }

        with patch("app.bot_service.redis_client.check_and_set_wamid", new_callable=AsyncMock, return_value=True), \
             patch("app.bot_service.redis_client.get_monthly_count", new_callable=AsyncMock, return_value=50), \
             patch("app.bot_service.meta_client.send_text_message", new_callable=AsyncMock) as mock_send_text:

            await handle_incoming_message(message)
            mock_send_text.assert_called_once()
            args = mock_send_text.call_args[1]
            assert "La información solicitada no se encuentra disponible" in args["text"]
            assert "Emergencia" in args["text"]
            assert "Cronograma" in args["text"]

    asyncio.run(_test())


def test_incoming_message_unsupported_type():
    async def _test():
        message = {
            "id": "wamid.test_audio_003",
            "from": "584121112233",
            "type": "audio",
            "audio": {"id": "12345"}
        }

        with patch("app.bot_service.redis_client.check_and_set_wamid", new_callable=AsyncMock, return_value=True), \
             patch("app.bot_service.meta_client.send_text_message", new_callable=AsyncMock) as mock_send_text:

            await handle_incoming_message(message)
            mock_send_text.assert_called_once()
            args = mock_send_text.call_args[1]
            assert "solo puede atender consultas en texto" in args["text"]

    asyncio.run(_test())


def test_corte_threshold_single_notice_and_silence():
    async def _test():
        phone = "584129998877"
        msg_1 = {
            "id": "wamid.test_corte_001",
            "from": phone,
            "type": "text",
            "text": {"body": "info sobre cantv"}
        }
        msg_2 = {
            "id": "wamid.test_corte_002",
            "from": phone,
            "type": "text",
            "text": {"body": "hola nuevamente"}
        }

        # Simular que el contador superó el umbral (955 >= 950)
        with patch("app.bot_service.redis_client.check_and_set_wamid", new_callable=AsyncMock, return_value=True), \
             patch("app.bot_service.redis_client.get_monthly_count", new_callable=AsyncMock, return_value=955), \
             patch("app.bot_service.redis_client.has_received_monthly_notice", new_callable=AsyncMock) as mock_has_noticed, \
             patch("app.bot_service.redis_client.mark_monthly_notice_sent", new_callable=AsyncMock) as mock_mark_sent, \
             patch("app.bot_service.meta_client.send_text_message", new_callable=AsyncMock) as mock_send_text:

            # Primer mensaje: No ha recibido aviso aún -> debe enviar aviso único
            mock_has_noticed.return_value = False
            await handle_incoming_message(msg_1)

            mock_send_text.assert_called_once()
            sent_text = mock_send_text.call_args[1]["text"]
            assert "Se alcanzó el cupo de respuestas automáticas" in sent_text
            assert get_next_month_name() in sent_text
            mock_mark_sent.assert_called_once_with(phone)

            # Segundo mensaje del mismo usuario: Ya fue notificado -> silencio total
            mock_send_text.reset_mock()
            mock_has_noticed.return_value = True
            await handle_incoming_message(msg_2)

            mock_send_text.assert_not_called()

    asyncio.run(_test())


def test_corte_threshold_allows_emergency():
    async def _test():
        phone = "584125556677"
        emergency_msg = {
            "id": "wamid.test_emergency_corte_001",
            "from": phone,
            "type": "text",
            "text": {"body": "tengo una emergencia médica urgente auxilio"}
        }

        # Superó el umbral (960 >= 950) pero PERMITIR_EMERGENCIAS_TRAS_CORTE es True
        with patch("app.bot_service.redis_client.check_and_set_wamid", new_callable=AsyncMock, return_value=True), \
             patch("app.bot_service.redis_client.get_monthly_count", new_callable=AsyncMock, return_value=960), \
             patch("app.bot_service.meta_client.send_response", new_callable=AsyncMock) as mock_send_response:

            await handle_incoming_message(emergency_msg)
            mock_send_response.assert_called_once()
            args = mock_send_response.call_args[1]
            # El texto real de emergencia ahora incluye el enlace web y números de emergencia
            assert "https://tuinfo.vercel.app/emergencias" in args["text"]
            assert args["image_url"] is None

    asyncio.run(_test())
