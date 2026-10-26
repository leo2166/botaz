import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("botAZ.knowledge")


def normalize_text(text: str) -> str:
    """
    Normaliza el texto para búsquedas robustas:
    - Minúsculas.
    - Eliminación de acentos y diacríticos (ej. 'eléctrico' -> 'electrico').
    - Reemplazo de signos de puntuación y símbolos por espacios.
    - Limpieza de espacios múltiples.
    """
    if not text:
        return ""

    # Convertir a minúsculas
    text = text.lower()

    # Descomponer diacríticos y filtrar caracteres no espaciados
    decomposed = unicodedata.normalize("NFD", text)
    without_accents = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )

    # Reemplazar cualquier carácter no alfanumérico por espacio
    clean_chars = re.sub(r"[^\w\s]", " ", without_accents)

    # Reducir espacios consecutivos
    normalized = " ".join(clean_chars.split())
    return normalized


def contains_whole_word(text_normalized: str, keyword: str) -> bool:
    """
    Comprueba si una palabra clave existe como palabra completa
    dentro del texto normalizado (evita falsos positivos por subcadenas).
    Ejemplo: 'luz' coincide en 'se fue la luz', pero NO en 'ilustre'.
    """
    norm_keyword = normalize_text(keyword)
    if not norm_keyword:
        return False

    pattern = rf"\b{re.escape(norm_keyword)}\b"
    return bool(re.search(pattern, text_normalized))


class KnowledgeBase:
    """Gestor de base de conocimiento cargada desde archivo JSON."""

    def __init__(self, file_path: Optional[Path] = None):
        if file_path is None:
            self.file_path = Path(__file__).parent / "knowledge.json"
        else:
            self.file_path = file_path
        self.items: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """Carga o recarga los datos desde el archivo JSON."""
        if not self.file_path.exists():
            logger.warning("Archivo de conocimiento no encontrado en: %s", self.file_path)
            self.items = []
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            self.items = json.load(f)

    def find_match(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Busca coincidencia por palabra clave completa en el mensaje.
        Prioriza los elementos marcados con is_priority=True (ej. emergencias).
        """
        normalized_message = normalize_text(user_message)
        if not normalized_message:
            return None

        # 1. Comprobar primero elementos de emergencia/prioritarios
        priority_items = [item for item in self.items if item.get("is_priority")]
        for item in priority_items:
            for kw in item.get("keywords", []):
                if contains_whole_word(normalized_message, kw):
                    return item

        # 2. Comprobar elementos temáticos específicos (excluyendo bienvenida para que saludos o palabras generales no secuestren consultas)
        specific_items = [item for item in self.items if not item.get("is_priority") and item.get("id") != "bienvenida"]
        for item in specific_items:
            for kw in item.get("keywords", []):
                if contains_whole_word(normalized_message, kw):
                    return item

        # 3. Comprobar bienvenida/saludos/menú general si no coincidió ningún tema específico
        welcome_items = [item for item in self.items if item.get("id") == "bienvenida"]
        for item in welcome_items:
            for kw in item.get("keywords", []):
                if contains_whole_word(normalized_message, kw):
                    return item

        return None

    def get_fallback_menu(self) -> str:
        """
        Mensaje de respuesta cuando la consulta no coincide con ninguna palabra clave.
        """
        return (
            "La información solicitada no se encuentra disponible. "
            "Por favor, intenta con otra palabra clave (por ejemplo: Emergencia, Cronograma, Farmacantv, Pago)."
        )


# Instancia por defecto
knowledge_base = KnowledgeBase()
