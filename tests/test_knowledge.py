import pytest
from app.knowledge import KnowledgeBase, contains_whole_word, normalize_text


def test_normalize_text():
    assert normalize_text("¡CANTV!") == "cantv"
    assert normalize_text("Eléctrico y Teléfono") == "electrico y telefono"
    assert normalize_text("   ¿EMERGENCIA   médica?   ") == "emergencia medica"
    assert normalize_text("") == ""


def test_contains_whole_word():
    # Coincidencia exacta de palabra completa
    assert contains_whole_word("se fue la luz en la casa", "luz") is True
    assert contains_whole_word("tengo una averia", "avería") is True
    assert contains_whole_word("averia en el telefono", "telefono") is True

    # No debe coincidir como subcadena en otras palabras
    assert contains_whole_word("el salon es ilustre", "luz") is False
    assert contains_whole_word("aluzar la habitacion", "luz") is False
    assert contains_whole_word("abanderado", "aba") is False


def test_find_match_direct_and_synonyms():
    kb = KnowledgeBase()

    # Consulta directa por palabra clave
    match_cantv = kb.find_match("necesito informacion de cantv")
    assert match_cantv is not None
    assert match_cantv["id"] == "cantv"

    # Consulta por sinónimo
    match_sinonimo = kb.find_match("tengo una averia en mi casa")
    assert match_sinonimo is not None
    assert match_sinonimo["id"] == "cantv"

    # Consulta de IA
    match_ia = kb.find_match("quiero usar el chat de inteligencia artificial")
    assert match_ia is not None
    assert match_ia["id"] == "ia"


def test_find_match_priority_emergency():
    kb = KnowledgeBase()

    # Mensaje de emergencia médica
    match_urgente = kb.find_match("es una emergencia de salud")
    assert match_urgente is not None
    assert match_urgente["id"] == "emergencia"
    assert match_urgente["is_priority"] is True

    # Mensaje mixto con emergencia y cantv: la emergencia debe prevalecer por prioridad
    match_mixto = kb.find_match("emergencia con mi linea cantv")
    assert match_mixto is not None
    assert match_mixto["id"] == "emergencia"


def test_find_match_no_match_and_fallback_menu():
    kb = KnowledgeBase()

    # Consulta sin ninguna palabra clave registrada
    match_none = kb.find_match("ojala llueva mucho esta tarde")
    assert match_none is None

    # Menú de respaldo
    menu = kb.get_fallback_menu()
    assert "La información solicitada no se encuentra disponible" in menu
    assert "Emergencia" in menu
    assert "Cronograma" in menu
    assert "Farmacantv" in menu
    assert "Pago" in menu


def test_find_match_bootie_imported_topics():
    kb = KnowledgeBase()

    # Carta aval
    match_aval = kb.find_match("necesito los requisitos para una carta aval")
    assert match_aval is not None
    assert match_aval["id"] == "carta_aval"

    # Reembolsos
    match_reembolso = kb.find_match("como solicito el reembolso de mis medicinas")
    assert match_reembolso is not None
    assert match_reembolso["id"] == "reembolso"

    # Servicios funerarios
    match_funeraria = kb.find_match("informacion de la funeraria el rosal")
    assert match_funeraria is not None
    assert match_funeraria["id"] == "funeraria"

    match_sf = kb.find_match("servicio funerario")
    assert match_sf is not None
    assert match_sf["id"] == "funeraria"

    match_sfs = kb.find_match("servicios funerarios")
    assert match_sfs is not None
    assert match_sfs["id"] == "funeraria"

    # Precedencia: saludo con consulta específica debe responder el tema específico
    match_saludo_fun = kb.find_match("hola necesito saber de la funeraria")
    assert match_saludo_fun is not None
    assert match_saludo_fun["id"] == "funeraria"

    # Saludo puro sin tema debe responder bienvenida
    match_saludo_puro = kb.find_match("hola buenos dias")
    assert match_saludo_puro is not None
    assert match_saludo_puro["id"] == "bienvenida"

    # FarmaCANTV
    match_farmacantv = kb.find_match("correo de farmacantv para tratamiento permanente")
    assert match_farmacantv is not None
    assert match_farmacantv["id"] == "farmacantv"

    # Distribución de la Nómina
    match_dist = kb.find_match("cual es la distribucion de la nomina")
    assert match_dist is not None
    assert match_dist["id"] == "distribucion_nomina"

    # Cronograma y Nómina
    match_crono = kb.find_match("muestrame el cronograma y calendario de pagos")
    assert match_crono is not None
    assert match_crono["id"] == "cronograma"

    match_pago_nom = kb.find_match("cuando es el pago de la nomina")
    assert match_pago_nom is not None
    assert match_pago_nom["id"] == "cronograma"

    # Directorio AJUPTEL
    match_dir = kb.find_match("telefono y directorio de ajuptel zulia")
    assert match_dir is not None
    assert match_dir["id"] == "directorio_ajuptel"

    # Gestión Humana Zulia
    match_gh = kb.find_match("contactos de gestion humana cantv")
    assert match_gh is not None
    assert match_gh["id"] == "gestion_humana"

    # Atención al Jubilado Nivel Central
    match_atj = kb.find_match("numeros de atencion al jubilado")
    assert match_atj is not None
    assert match_atj["id"] == "atencion_al_jubilado"

    # Noticias y Tasas
    match_news = kb.find_match("cuales son las noticias y la tasa del bcv")
    assert match_news is not None
    assert match_news["id"] == "noticias_tasas"

    # Formato Bolsa de Alimentación
    match_bolsa = kb.find_match("donde descargo el formato bolsa de alimentacion")
    assert match_bolsa is not None
    assert match_bolsa["id"] == "autorizacion_bolsa"

    # Cumpleaños
    match_cumple = kb.find_match("quienes son los cumpleaneros del mes")
    assert match_cumple is not None
    assert match_cumple["id"] == "cumpleanos"

