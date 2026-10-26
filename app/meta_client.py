import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

from app.config import settings
from app.security import mask_phone_number

logger = logging.getLogger("botAZ.meta_client")


class MetaWhatsAppClient:
    """Cliente asíncrono para la WhatsApp Cloud API de Meta (v26.0)."""

    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.GRAPH_API_VERSION}/{settings.META_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def send_text_message(self, to: str, text: str) -> Optional[Dict[str, Any]]:
        """Envía un mensaje de texto simple al número destino."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
            }
        }
        return await self._post_message(payload, recipient=to)

    async def send_image_message(self, to: str, image_url: str, caption: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Envía un mensaje de imagen con pie de foto (caption) opcional."""
        image_obj: Dict[str, Any] = {"link": image_url}
        if caption:
            image_obj["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": image_obj
        }
        return await self._post_message(payload, recipient=to)

    async def send_response(self, to: str, text: str, image_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Envía la respuesta al usuario.
        Si incluye URL de imagen, la envía con el texto como caption en un solo mensaje.
        Si no hay imagen o falla, envía el texto.
        """
        if image_url:
            return await self.send_image_message(to=to, image_url=image_url, caption=text)
        return await self.send_text_message(to=to, text=text)

    async def _post_message(self, payload: Dict[str, Any], recipient: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
        """
        Realiza la petición POST hacia Meta con reintentos controlados para 5xx o errores de red.
        No reintenta errores 4xx (errores del cliente).
        """
        masked_to = mask_phone_number(recipient)
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.base_url, headers=self.headers, json=payload)

                if response.status_code == 200:
                    logger.info("Mensaje enviado con éxito a %s (intento %d)", masked_to, attempt)
                    return response.json()

                if 400 <= response.status_code < 500:
                    logger.error(
                        "Error 4xx de Meta enviando a %s: status=%d body=%s",
                        masked_to, response.status_code, response.text
                    )
                    return None

                logger.warning(
                    "Error de servidor Meta (%d) enviando a %s (intento %d/%d): %s",
                    response.status_code, masked_to, attempt, max_retries, response.text
                )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    "Fallo de conexión con Meta enviando a %s (intento %d/%d): %s",
                    masked_to, attempt, max_retries, str(exc)
                )

            if attempt < max_retries:
                await asyncio.sleep(1.0 * attempt)

        logger.error("No se pudo enviar el mensaje a %s tras %d intentos.", masked_to, max_retries)
        return None


meta_client = MetaWhatsAppClient()
