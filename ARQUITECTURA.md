# ARQUITECTURA DEL PROYECTO: BotAZ

> **PIVOTE ESTRATÉGICO (WhatsApp Web QR Gateway)**:
> Debido a las restricciones administrativas de Meta (verificación de empresa comercial, cuenta de pago y límites del entorno de prueba), el proyecto pivota hacia una arquitectura desacoplada con **Gateway QR (WhatsApp Web / Baileys)** manteniendo el núcleo inteligente en **Python + FastAPI**.

---

## 1. Componentes del Sistema

### A. Núcleo Inteligente (FastAPI - Puerto 8000)
- **Base de Conocimiento**: Archivo `app/knowledge.json` editable por no técnicos (palabra clave, sinónimos, texto de respuesta, URL de imagen y flag de prioridad para emergencias).
- **Normalización y Búsqueda**: Minúsculas, remoción completa de tildes y diacríticos, coincidencia exacta por palabra completa (`\b`) para evitar falsos positivos por subcadenas.
- **Idempotencia y Deduplicación**: Almacén con clave por `wamid` / `id` de mensaje con TTL de 24 horas (`SET NX`).
- **Control de Cupo y Reglas de Negocio**:
  - Umbral de corte configurable (por defecto 950) y límite mensual (1.000).
  - Aviso mensual único por usuario tras superar el umbral; posterior silencio para ese usuario hasta el 1 del mes siguiente.
  - Excepción de emergencias prioritarias permitida tras corte (`PERMITIR_EMERGENCIAS_TRAS_CORTE=true`).
  - Menú de respaldo conciso ante consultas no reconocidas.
- **Endpoints FastAPI**:
  - `GET /health`: Monitoreo y keep-alive.
  - `GET /qr`: Visualizador web del código QR para vinculación rápida desde navegador.
  - `GET /gateway/status`: Estado de la conexión de WhatsApp.
  - `POST /gateway/incoming`: Recepción de eventos desde el conector Baileys.
  - `POST /webhook` & `GET /webhook`: Compatibilidad dual preservada.

### B. Conector WhatsApp Web (Gateway Baileys - Puerto 3001)
- Microservicio en Node.js utilizando `@whiskeysockets/baileys` (multi-device WebSocket sin navegador pesado).
- Generación y refresco del código QR:
  - Visible en consola/terminal mediante `qrcode-terminal`.
  - Servido en navegador vía `http://localhost:8000/qr` y `http://localhost:3001/qr`.
- Almacenamiento persistente de sesión en `gateway/auth_info_baileys/` (no requiere re-escanear tras reiniciar).
- Reenvío de mensajes entrantes a FastAPI vía HTTP `POST /gateway/incoming`.
- Endpoint saliente `POST /send` para emisión de texto e imágenes con pie de foto (*caption*).

---

## 2. Ventajas del Pivote
1. **$0 Presupuesto Real**: Sin necesidad de tarjeta de crédito, facturación en Meta ni riesgo de cobros sorpresivos.
2. **Cero Burocracia**: Sin exigencias de verificación fiscal, documentos comerciales o aprobación de plantillas por Meta.
3. **Número Flexible**: Se puede conectar directamente cualquier número móvil regular de WhatsApp mediante vinculación multi-dispositivo.
4. **Preservación Total del Código**: La base de conocimiento, lógica de normalización, pruebas unitarias y motor de negocio se mantienen al 100%.
