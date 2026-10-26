import logging
from typing import Any, Dict

from app.config import settings
from app.knowledge import knowledge_base
from app.whatsapp_adapter import whatsapp_adapter as meta_client
from app.redis_client import get_next_month_name, redis_client
from app.security import mask_phone_number

logger = logging.getLogger("botAZ.service")


async def handle_status_update(status: Dict[str, Any]) -> None:
    """
    Procesa webhooks de estado enviados por Meta.
    Contabiliza exclusivamente mensajes con status 'delivered' y pricing billable.
    """
    status_type = status.get("status")
    pricing = status.get("pricing", {})
    is_billable = pricing.get("billable", False)

    if status_type == "delivered" and is_billable:
        count = await redis_client.increment_monthly_counter()
        logger.info("Mensaje entregado billable registrado. Conteo mensual actual: %d", count)

        # Monitoreo de alertas de cupo
        limite = settings.LIMITE_MENSUAL
        if count >= int(limite * 0.90):
            if await redis_client.check_and_set_alert(90):
                logger.warning("ALERTA CRÍTICA: Consumo del 90%% del cupo mensual (%d/%d)", count, limite)
        elif count >= int(limite * 0.70):
            if await redis_client.check_and_set_alert(70):
                logger.warning("ALERTA PREVENTIVA: Consumo del 70%% del cupo mensual (%d/%d)", count, limite)


async def handle_incoming_message(message: Dict[str, Any]) -> None:
    """
    Procesa un mensaje entrante de un usuario:
    1. Idempotencia: descarta duplicados por wamid.
    2. Filtrado de tipo: solo texto (respuestas corteses a multimedia).
    3. Normalización y búsqueda en base de conocimiento.
    4. Control de umbral de corte y aviso único mensual.
    5. Envío asíncrono de respuesta (texto e imagen) o menú de respaldo.
    """
    wamid = message.get("id") or message.get("wamid")
    from_phone = message.get("jid") or message.get("from")

    if not wamid or not from_phone:
        return

    masked_phone = mask_phone_number(from_phone)

    # 1. Deduplicación e Idempotencia (TTL 24h)
    is_fresh = await redis_client.check_and_set_wamid(wamid)
    if not is_fresh:
        logger.info("Mensaje duplicado descartado por idempotencia: wamid=%s usuario=%s", wamid, masked_phone)
        return

    # 2. Tipos de mensaje no soportados (audio, imágenes, stickers)
    msg_type = message.get("type", "text")
    if msg_type not in ("text", "conversation", "extendedTextMessage"):
        polite_msg = (
            "Por los momentos este canal de AJUPTEL Zulia solo puede atender consultas en texto. "
            "Por favor escriba su consulta por palabra clave (ej. cantv, emergencia, electricidad)."
        )
        await meta_client.send_text_message(to=from_phone, text=polite_msg)
        return

    raw_text = message.get("text")
    if isinstance(raw_text, dict):
        user_text = raw_text.get("body", "")
    else:
        user_text = str(raw_text or "")

    # Normalizar texto entrante: minúsculas y eliminación de espacios iniciales/finales
    clean_text = user_text.lower().strip()

    # 3. Búsqueda en Base de Conocimiento
    match = knowledge_base.find_match(clean_text)
    is_priority = bool(match and match.get("is_priority"))

    # 4. Verificación de Umbral de Corte
    current_count = await redis_client.get_monthly_count()
    if current_count >= settings.UMBRAL_CORTE:
        if is_priority and settings.PERMITIR_EMERGENCIAS_TRAS_CORTE:
            logger.info("Atendiendo mensaje de emergencia para %s tras superar umbral de corte.", masked_phone)
            await meta_client.send_response(
                to=from_phone,
                text=match["response_text"],
                image_url=match.get("image_url")
            )
        else:
            # Consulta normal bloqueada: enviar aviso único por usuario al mes
            already_notified = await redis_client.has_received_monthly_notice(from_phone)
            if not already_notified:
                next_month = get_next_month_name()
                notice_text = (
                    f"Lo sentimos. Se alcanzó el cupo de respuestas automáticas de este mes. "
                    f"El servicio se restablece el 1 de {next_month}. "
                    f"Para asuntos urgentes, comuníquese directamente con AJUPTEL Zulia."
                )
                await meta_client.send_text_message(to=from_phone, text=notice_text)
                await redis_client.mark_monthly_notice_sent(from_phone)
                logger.info("Aviso mensual único de corte enviado a %s.", masked_phone)
            else:
                logger.info("Usuario %s ya fue notificado este mes; silencio conforme a política de ahorro.", masked_phone)
        return

    # 5. Respuestas ordinarias por debajo del umbral
    if match:
        await meta_client.send_response(
            to=from_phone,
            text=match["response_text"],
            image_url=match.get("image_url")
        )
    else:
        # Menú de respaldo breve si no hubo coincidencia
        fallback_menu = knowledge_base.get_fallback_menu()
        await meta_client.send_text_message(to=from_phone, text=fallback_menu)


async def process_webhook_payload(payload: Dict[str, Any]) -> None:
    """Desempaqueta el payload del webhook de Meta y enruta statuses y messages."""
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            # Webhooks de estado de entrega
            for status in value.get("statuses", []):
                try:
                    await handle_status_update(status)
                except Exception as exc:
                    logger.error("Error procesando status webhook: %s", str(exc))

            # Webhooks de mensajes entrantes
            for message in value.get("messages", []):
                try:
                    await handle_incoming_message(message)
                except Exception as exc:
                    logger.error("Error procesando mensaje entrante: %s", str(exc))
