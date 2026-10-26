import hashlib
import hmac
import re
from typing import Optional


def verify_hub_signature(
    raw_body: bytes,
    signature_header: Optional[str],
    app_secret: str
) -> bool:
    """
    Valida la firma criptográfica X-Hub-Signature-256 de Meta.
    Debe calcularse sobre los bytes crudos de la petición HTTP usando HMAC-SHA256
    y compararse en tiempo constante con hmac.compare_digest.
    """
    if not signature_header or not app_secret:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    expected_header = f"sha256={expected_hash}"
    return hmac.compare_digest(expected_header, signature_header)


def mask_phone_number(phone: str) -> str:
    """
    Enmascara el número de teléfono para resguardar la privacidad en los logs.
    Ejemplo: '584121234567' -> '58412***4567'.
    """
    cleaned = re.sub(r"\D", "", phone)
    if len(cleaned) <= 6:
        return "***"
    return f"{cleaned[:5]}***{cleaned[-4:]}"
