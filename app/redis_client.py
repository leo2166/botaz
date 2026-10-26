import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import httpx

try:
    from zoneinfo import ZoneInfo
    CARACAS_TZ = ZoneInfo("America/Caracas")
except Exception:
    # Fallback seguro para entornos Windows sin paquete tzdata
    CARACAS_TZ = timezone(timedelta(hours=-4))

from app.config import settings
from app.security import mask_phone_number

logger = logging.getLogger("botAZ.redis_client")

MESES_ESPANOL = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def get_caracas_now() -> datetime:
    """Retorna la fecha y hora actual en la zona horaria de Caracas."""
    try:
        return datetime.now(CARACAS_TZ)
    except Exception:
        return datetime.now(timezone(timedelta(hours=-4)))


def get_current_month_key() -> str:
    """Retorna la clave del mes en curso (ej. '2026_10')."""
    return get_caracas_now().strftime("%Y_%m")


def get_next_month_name() -> str:
    """Retorna el nombre en español del mes siguiente al actual."""
    now = get_caracas_now()
    # now.month está en rango 1..12.
    # El mes siguiente tiene índice now.month % 12 (0 para enero, 10 para noviembre, etc.)
    next_idx = now.month % 12
    return MESES_ESPANOL[next_idx]


class UpstashRedisClient:
    """
    Cliente REST para Upstash Redis Serverless.
    Soporta fallback en memoria para pruebas locales y tests automatizados.
    """

    def __init__(self):
        self.url = settings.UPSTASH_REDIS_REST_URL.strip()
        self.token = settings.UPSTASH_REDIS_REST_TOKEN.strip()
        self.is_live = bool(self.url and self.token and "dummy" not in self.url)
        # Almacenamiento en memoria para modo mock/offline
        self._memory_store: Dict[str, Any] = {}
        self._memory_expires: Dict[str, float] = {}

    async def execute_command(self, *args: Any) -> Any:
        """Ejecuta un comando Redis vía REST hacia Upstash o sobre el almacén local en memoria."""
        if not self.is_live:
            return self._execute_memory(*args)

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        body = [str(arg) for arg in args]

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
                response = await client.post(self.url, headers=headers, json=body)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("result")
                logger.error("Error respuesta Upstash REST: status=%d body=%s", response.status_code, response.text)
                return None
        except Exception as exc:
            logger.error("Error de conexión con Upstash Redis REST: %s. Usando memoria temporal.", str(exc))
            return self._execute_memory(*args)

    def _execute_memory(self, *args: Any) -> Any:
        """Simulación en memoria de comandos básicos de Redis."""
        now = time.time()
        cmd = str(args[0]).upper()

        # Limpiar llaves expiradas
        expired_keys = [k for k, exp in self._memory_expires.items() if exp <= now]
        for k in expired_keys:
            self._memory_store.pop(k, None)
            self._memory_expires.pop(k, None)

        if cmd == "GET":
            key = str(args[1])
            return self._memory_store.get(key)

        if cmd == "SET":
            key = str(args[1])
            val = str(args[2])
            nx = "NX" in [str(a).upper() for a in args]
            ex = None
            for idx, a in enumerate(args):
                if str(a).upper() == "EX" and idx + 1 < len(args):
                    ex = int(args[idx + 1])

            if nx and key in self._memory_store:
                return None

            self._memory_store[key] = val
            if ex:
                self._memory_expires[key] = now + ex
            return "OK"

        if cmd == "INCR":
            key = str(args[1])
            current = int(self._memory_store.get(key, 0))
            current += 1
            self._memory_store[key] = str(current)
            return current

        return None

    async def check_and_set_wamid(self, wamid: str) -> bool:
        """
        Idempotencia: Registra el ID único del mensaje (wamid) con TTL de 24 horas (86400s).
        Retorna True si es un mensaje nuevo, False si ya existía (duplicado).
        """
        key = f"botaz:wamid:{wamid}"
        res = await self.execute_command("SET", key, "1", "NX", "EX", 86400)
        return res == "OK"

    async def increment_monthly_counter(self) -> int:
        """Incrementa atómicamente el contador de mensajes entregados del mes actual."""
        month = get_current_month_key()
        key = f"botaz:counter:{month}"
        new_count = await self.execute_command("INCR", key)
        return int(new_count) if new_count is not None else 1

    async def get_monthly_count(self) -> int:
        """Obtiene la cantidad acumulada de mensajes entregados en el mes en curso."""
        month = get_current_month_key()
        key = f"botaz:counter:{month}"
        val = await self.execute_command("GET", key)
        return int(val) if val is not None else 0

    async def has_received_monthly_notice(self, phone: str) -> bool:
        """Verifica si el usuario ya recibió el aviso único de agotamiento de cupo este mes."""
        month = get_current_month_key()
        key = f"botaz:notice:{month}:{phone}"
        val = await self.execute_command("GET", key)
        return val is not None

    async def mark_monthly_notice_sent(self, phone: str) -> bool:
        """Registra que se envió el aviso de cupo al usuario este mes (expira en 31 días)."""
        month = get_current_month_key()
        key = f"botaz:notice:{month}:{phone}"
        res = await self.execute_command("SET", key, "1", "NX", "EX", 2678400)
        return res == "OK"

    async def check_and_set_alert(self, percentage: int) -> bool:
        """
        Registra la emisión de alerta de umbral (70% o 90%) en el mes.
        Retorna True si aún no se había emitido (debe enviarse), False si ya fue emitida.
        """
        month = get_current_month_key()
        key = f"botaz:alert:{month}:{percentage}"
        res = await self.execute_command("SET", key, "1", "NX", "EX", 2678400)
        return res == "OK"


redis_client = UpstashRedisClient()
