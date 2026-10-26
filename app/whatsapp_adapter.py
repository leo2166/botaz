import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

from app.config import settings
from app.security import mask_phone_number

logger = logging.getLogger("botAZ.whatsapp_adapter")


class WhatsAppGatewayAdapter:
    """
    Adapter para el conector local WhatsApp Web QR (Baileys / Gateway).
    Reemplaza la dependencia directa de Meta Cloud API permitiendo vincular
    cualquier número mediante código QR sin tarjeta de crédito ni verificación de empresa.
    """

    def __init__(self):
        self.gateway_url = settings.GATEWAY_URL.rstrip("/")
        self.timeout = httpx.Timeout(10.0, connect=3.0)

    async def send_text_message(self, to: str, text: str) -> Optional[Dict[str, Any]]:
        """Envía un mensaje de texto a través del gateway QR."""
        return await self._post_to_gateway(to=to, text=text)

    async def send_image_message(self, to: str, image_url: str, caption: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Envía una imagen con pie de foto opcional a través del gateway QR."""
        return await self._post_to_gateway(to=to, text=caption or "", image_url=image_url)

    async def send_response(self, to: str, text: str, image_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Envía respuesta con imagen y texto o solo texto."""
        if image_url:
            return await self.send_image_message(to=to, image_url=image_url, caption=text)
        return await self.send_text_message(to=to, text=text)

    async def get_status(self) -> Dict[str, Any]:
        """Consulta el estado de conexión del gateway QR."""
        url = f"{self.gateway_url}/status"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return res.json()
        except Exception as exc:
            logger.debug("No se pudo obtener estado del gateway: %s", str(exc))
        return {"status": "disconnected", "error": "Gateway offline"}

    async def get_qr_data(self) -> Dict[str, Any]:
        """Obtiene el QR actual generado por el gateway."""
        url = f"{self.gateway_url}/qr-data"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return res.json()
        except Exception as exc:
            logger.debug("No se pudo obtener QR del gateway: %s", str(exc))
        return {"status": "disconnected", "qr": None, "qr_data_url": None}

    async def _post_to_gateway(
        self, to: str, text: str, image_url: Optional[str] = None, max_retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.gateway_url}/send"
        if image_url:
            payload = {
                "to": to,
                "jid": to,
                "type": "image",
                "url": image_url,
                "image_url": image_url,
                "caption": text or "",
                "text": text or "",
            }
        else:
            payload = {
                "to": to,
                "jid": to,
                "type": "text",
                "text": text or "",
            }

        masked_to = mask_phone_number(to)
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") is False:
                        logger.warning("Gateway reportó fallo enviando a %s: %s", masked_to, data.get("error"))
                    else:
                        logger.info("Mensaje enviado por Gateway a %s (intento %d)", masked_to, attempt)
                    return data
                logger.warning("Gateway respondió status %d enviando a %s", response.status_code, masked_to)
            except Exception as exc:
                logger.warning("Fallo comunicando con Gateway enviando a %s: %s", masked_to, str(exc))

            if attempt < max_retries:
                await asyncio.sleep(1.0 * attempt)

        return None


whatsapp_adapter = WhatsAppGatewayAdapter()
