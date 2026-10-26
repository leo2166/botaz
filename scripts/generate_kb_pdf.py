import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para añadir número de página total en el pie."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Encabezado (solo a partir de la página 2)
        if self._pageNumber > 1:
            self.drawString(54, letter[1] - 36, "AJUPTEL Zulia - Manual de la Base de Conocimientos de BotAZ")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

        # Pie de página
        page_str = f"Página {self._pageNumber} de {total_pages}"
        self.drawRightString(letter[0] - 54, 30, page_str)
        self.drawString(54, 30, "Documento de Uso Administrativo - BotAZ WhatsApp 2026")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 42, letter[0] - 54, 42)
        self.restoreState()


def build_pdf():
    base_dir = Path(__file__).resolve().parent.parent
    kb_path = base_dir / "app" / "knowledge.json"
    output_pdf = base_dir / "MANUAL_BASE_DE_CONOCIMIENTO_BOTAZ.pdf"

    with open(kb_path, "r", encoding="utf-8") as f:
        kb_items = json.load(f)

    # Configuración de página: márgenes de 54 pt (0.75 pulgadas)
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Paleta de colores profesional
    primary_color = colors.HexColor("#0f3b6c")    # Azul institucional CANTV
    secondary_color = colors.HexColor("#0284c7")  # Celeste moderno
    dark_neutral = colors.HexColor("#0f172a")     # Texto principal oscuro
    accent_green = colors.HexColor("#059669")     # Verde actualización
    card_bg = colors.HexColor("#f8fafc")          # Fondo de cajas
    border_color = colors.HexColor("#e2e8f0")     # Borde sutil

    # Estilos tipográficos
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=primary_color,
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        alignment=0,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "TopicH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=dark_neutral,
        spaceAfter=4,
    )
    bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=primary_color,
    )
    code_box = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
    )
    action_box = ParagraphStyle(
        "ActionText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#065f46"),
    )

    story = []

    # ==========================
    # PORTADA / ENCABEZADO
    # ==========================
    story.append(Paragraph("MANUAL DE GESTIÓN Y GUÍA DETALLADA", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Base de Conocimientos de BotAZ WhatsApp", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Asociación de Jubilados y Pensionados CANTV Zulia (AJUPTEL)</b> | Versión 2.0 (2026)", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=14))

    # Resumen introductorio en recuadro
    intro_html = (
        "<b>Propósito de este documento:</b> Este manual está diseñado para que cualquier directivo "
        "o administrador de AJUPTEL Zulia entienda a fondo cómo responde el Bot de WhatsApp, qué información "
        "tiene almacenada actualmente (desde el saludo <b>'hola'</b> hasta los trámites médicos más avanzados), "
        "y exactamente <b>qué campos debe actualizar o cambiar</b> cuando varíen fechas, números telefónicos, "
        "montos de bonos o recaudos."
    )
    intro_table = Table([[Paragraph(intro_html, body_style)]], colWidths=[504])
    intro_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 14))

    # ==========================
    # SECCIÓN 1: CÓMO FUNCIONA
    # ==========================
    story.append(Paragraph("1. ¿Cómo Funciona el Motor de Búsqueda del Bot?", h1_style))
    story.append(Paragraph(
        "El bot opera con el archivo <code>app/knowledge.json</code> siguiendo estas reglas clave:",
        body_style,
    ))

    rules_data = [
        [
            Paragraph("<b>Regla</b>", bold_label),
            Paragraph("<b>¿Cómo actúa el Bot?</b>", bold_label),
            Paragraph("<b>Beneficio para el Jubilado</b>", bold_label),
        ],
        [
            Paragraph("<b>Normalización</b>", body_style),
            Paragraph("Convierte todo a minúsculas, elimina espacios extra y suprime tildes ('eléctrico' → 'electrico').", body_style),
            Paragraph("No importa cómo escriban los abuelos (con o sin mayúsculas/acentos), el bot siempre los entenderá.", body_style),
        ],
        [
            Paragraph("<b>Palabra Completa (\\b)</b>", body_style),
            Paragraph("Busca palabras completas. Por ejemplo, 'luz' solo coincide si la palabra está aislada, no dentro de 'ilustre'.", body_style),
            Paragraph("Evita respuestas incorrectas por coincidencias accidentales de letras.", body_style),
        ],
        [
            Paragraph("<b>Prioridad de Emergencia</b>", body_style),
            Paragraph("La clave de emergencias tiene <code>is_priority: true</code> y se evalúa antes que las demás.", body_style),
            Paragraph("Si alguien pide auxilio médico en horario de corte o junto a otra duda, la emergencia prevalece de inmediato.", body_style),
        ],
        [
            Paragraph("<b>Menú de Respaldo</b>", body_style),
            Paragraph("Si el mensaje no contiene ninguna palabra registrada, el bot envía un menú breve de opciones.", body_style),
            Paragraph("El usuario nunca queda sin respuesta; el bot le enseña qué palabras puede enviar.", body_style),
        ],
    ]
    rules_table = Table(rules_data, colWidths=[110, 204, 190])
    rules_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(rules_table)
    story.append(Spacer(1, 14))

    # ==========================
    # SECCIÓN 2: INVENTARIO DE TEMAS
    # ==========================
    story.append(Paragraph("2. Inventario Detallado de Temas: Qué Responder y Qué Actualizar", h1_style))
    story.append(Paragraph(
        "A continuación se presenta cada uno de los <b>13 temas cargados</b>, ordenados desde el saludo inicial "
        "hasta los servicios de apoyo:",
        body_style,
    ))
    story.append(Spacer(1, 6))

    # Guías específicas de qué cambiar por cada item
    tips_dict = {
        "bienvenida": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Si añades un nuevo servicio al bot (ej. 'odontologia'), agrega la viñeta en este mensaje para que los jubilados se enteren.<br/>"
            "• Puedes agregar más palabras clave al menú como 'buen dia', 'buenas', 'que hay'."
        ),
        "emergencia": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Si cambian los números de ambulancias o de la Coordinación de Salud en Maracaibo, edítalos aquí.<br/>"
            "• Si se diseña una nueva lámina gráfica de emergencia, cambia el enlace en <code>image_url</code>.<br/>"
            "• <b>Importante:</b> Este tema SIEMPRE debe mantener <code>\"is_priority\": true</code>."
        ),
        "carta_aval": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Si CANTV modifica el correo de recepción (actualmente <code>cartaavalgss@cantv.com.ve</code>).<br/>"
            "• Si la empresa exige algún requisito adicional (ej. copia de carnet SAP o vigencia máxima del informe)."
        ),
        "reembolso": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Si cambia el correo de reembolso (actualmente <code>reembolsogss@cantv.com.ve</code>).<br/>"
            "• Si el SENIAT o CANTV modifican el tiempo máximo de recepción de facturas (actualmente 6 meses)."
        ),
        "funeraria": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Teléfonos de contacto de guardia de la funeraria El Rosal o números celulares de los agentes.<br/>"
            "• Si cambia el alcance de la cobertura familiar o cementerios con convenio de cremación en Zulia."
        ),
        "farmacantv": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Si cambia el correo electrónico de FarmaCANTV Occidente (<code>farmacantv.regionoccidente@gmail.com</code>).<br/>"
            "• Si abren entrega presencial en Maracaibo o cambian los recaudos periódicos."
        ),
        "pago": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• <b>¡Muy frecuente!</b> Cada vez que el Ejecutivo o CANTV decreten aumentos en la pensión (571,20 Bs), "
            "bono de ayuda (500 Bs), bono alimentario ($68) o bono vital ($200), actualiza los montos aquí."
        ),
        "cronograma": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• <b>¡Anual o semestral!</b> Al inicio de cada año o cuando SUDABAN y CANTV publiquen el nuevo calendario oficial.<br/>"
            "• Si se adelanta o pospone una quincena (ej. por días festivos o Carnaval)."
        ),
        "directorio_ajuptel": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Teléfonos celulares o personas de la Junta Directiva (Euclides Díaz, Mercedes Luengo, Tibisay Castellanos, Olga Infante).<br/>"
            "• Horarios de atención presencial en la sede de la asociación en Maracaibo."
        ),
        "gestion_humana": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Nombres, teléfonos y correos del personal de Gestión Humana CANTV Zulia (María de Los Ángeles, Gilberto Marcano, Lisdeth Carruyo).<br/>"
            "• Teléfonos del nivel central en Caracas si cambian las extensiones (0212-500xxxx)."
        ),
        "cantv": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Si CANTV habilita un número especial de averías para jubilados.<br/>"
            "• Si cambia el asistente virtual (Cati) o la URL de reporte web."
        ),
        "electricidad": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Número de WhatsApp oficial de CORPOELEC (actualmente 0426-5555555) o canales parroquiales del Zulia.<br/>"
            "• Enlaces a la aplicación VenApp Línea 58."
        ),
        "fe_de_vida": (
            "<b>¿Qué actualizar aquí?</b><br/>"
            "• Las fechas de las jornadas de Fe de Vida cuando la Junta Directiva las convoque.<br/>"
            "• Requisitos específicos de supervivencias para sobrevivientes o casos encamados."
        ),
    }

    for idx, item in enumerate(kb_items, start=1):
        item_id = item.get("id", "")
        title = item.get("title", "")
        keywords = ", ".join(item.get("keywords", []))
        resp_text = item.get("response_text", "").replace("\n", "<br/>")
        img_url = item.get("image_url") or "Ninguna (Solo Texto)"
        is_prio = "Sí (Prioridad Alta)" if item.get("is_priority") else "Normal"
        tip_text = tips_dict.get(item_id, "Mantener los datos de contacto y fechas actualizadas.")

        card_content = [
            [
                Paragraph(f"<b>Tema #{idx}: {title}</b> (<code>id: {item_id}</code>)", h2_style),
                Paragraph(f"<b>Prioridad:</b> {is_prio}", bold_label),
            ],
            [
                Paragraph("<b>Palabras Clave activadoras:</b>", bold_label),
                Paragraph(f"<code>{keywords}</code>", body_style),
            ],
            [
                Paragraph("<b>Imagen adjunta:</b>", bold_label),
                Paragraph(f"<font size=7.5 color='#0369a1'>{img_url}</font>", body_style),
            ],
            [
                Paragraph("<b>Mensaje que envía el Bot:</b>", bold_label),
                Paragraph(f"<font color='#0f172a'>{resp_text}</font>", body_style),
            ],
            [
                Paragraph("<b>GUÍA DE ACTUALIZACIÓN:</b>", bold_label),
                Paragraph(tip_text, action_box),
            ],
        ]

        item_table = Table(card_content, colWidths=[130, 374])
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), card_bg),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("LINEBELOW", (0, 0), (-1, 0), 1, primary_color),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("SPAN", (0, 0), (0, 0)),
            ("SPAN", (1, 1), (1, 1)),
            ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#ecfdf5")), # Fondo verde claro para el tip
            ("LINEABOVE", (0, 4), (-1, 4), 0.5, colors.HexColor("#a7f3d0")),
        ]))

        story.append(KeepTogether([
            item_table,
            Spacer(1, 10),
        ]))

    # ==========================
    # SECCIÓN 3: CÓMO EDITAR EL ARCHIVO
    # ==========================
    story.append(PageBreak())
    story.append(Paragraph("3. Guía Paso a Paso para Editar <code>app/knowledge.json</code>", h1_style))
    story.append(Paragraph(
        "El archivo de conocimiento es un archivo de texto plano en formato JSON ubicado en la carpeta del proyecto en:<br/>"
        "<b><code>c:\\Users\\Lucidio\\Proyectos\\botAZ\\app\\knowledge.json</code></b>",
        body_style,
    ))
    story.append(Spacer(1, 6))

    how_to_html = (
        "<b>Pasos sencillos para hacer cambios:</b><br/>"
        "1. <b>Abre el archivo:</b> Puedes abrirlo con cualquier editor de texto como Visual Studio Code, Notepad++ o Bloc de Notas.<br/>"
        "2. <b>Localiza el tema:</b> Busca por el <code>\"id\"</code> del tema que deseas cambiar (ej. <code>\"pago\"</code> o <code>\"emergencia\"</code>).<br/>"
        "3. <b>Modifica el texto:</b> Cambia el valor dentro de <code>\"response_text\": \"...\"</code>. Puedes usar negritas de WhatsApp encerrando entre asteriscos (ej. <code>*Nuevo Monto: 700 Bs*</code>).<br/>"
        "4. <b>Saltos de línea:</b> Para que el bot salte de renglón en WhatsApp, escribe <code>\\n</code>.<br/>"
        "5. <b>Agregar palabras clave:</b> En <code>\"keywords\": [...]</code> agrega la palabra entre comillas separada por coma (ej. <code>\"bonos\", \"nuevo cobro\"</code>). <i>Siempre en minúsculas y sin acentos.</i><br/>"
        "6. <b>Guarda el archivo:</b> Presiona <code>Ctrl + S</code>. El servidor de FastAPI recargará el bot automáticamente sin necesidad de reiniciar."
    )

    how_table = Table([[Paragraph(how_to_html, body_style)]], colWidths=[504])
    how_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(how_table)
    story.append(Spacer(1, 12))

    # Cuidado con errores JSON
    warn_html = (
        "<b>⚠️ REGLAS DE ORO DE SEGURIDAD (Para no romper el archivo JSON):</b><br/>"
        "• Cada elemento debe estar separado por una coma (<code>,</code>).<br/>"
        "• El último elemento de una lista no debe llevar coma al final.<br/>"
        "• Todas las comillas deben ser dobles rectas (<code>\"</code>) y nunca comillas tipográficas curvadas.<br/>"
        "• Si tienes dudas, puedes ejecutar en la terminal: <code>.\\venv\\Scripts\\python -m pytest -v</code> para verificar que todas las pruebas pasen al 100%."
    )
    warn_table = Table([[Paragraph(warn_html, body_style)]], colWidths=[504])
    warn_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#fcd34d")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(warn_table)

    # Construir PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente en: {output_pdf}")


if __name__ == "__main__":
    build_pdf()
