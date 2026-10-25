# PROGRESO DEL PROYECTO: BotAZ (WhatsApp Bot)

## Sesión 1: Pasos 0 y 1 (Investigación y Definición)

### Paso 0: Skills para el Proyecto
- **Decisión acordada**: Sin skills externas instaladas para evitar sobrecarga de contexto y consumo innecesario de tokens.

### Paso 1: Decisiones de Arquitectura e Infraestructura
1. **Versión de Meta Graph API**: `v26.0` (parametrizada en variables de entorno).
2. **Requisitos de Producción**: Número telefónico limpio (sin app activa), token de usuario del sistema permanente y operación inicial dentro del cupo gratuito de 1.000 mensajes de servicio.
3. **Hosting**: Render (Web Service gratuito, 750h/mes, sin tarjeta). Punto débil: cold start de ~50s tras 15 min de inactividad.
4. **Contador e Idempotencia**: Upstash Redis (Serverless vía REST API por HTTP).

---

## Fase A: Estructura del Proyecto y Configuración (COMPLETADA)

### Lo Realizado:
- **Entorno Virtual**: Creado con PowerShell en `.venv` bajo Python 3.15.
- **Dependencias**: Archivo `requirements.txt` creado con `fastapi`, `uvicorn`, `httpx`, `pydantic-settings`, `python-dotenv` y `pytest`. Instalación verificada con éxito.
- **Seguridad y Secretos**:
  - Creado `.gitignore` protegiendo entornos virtuales, cache y archivos de entorno (`.env`).
  - Creado `.env.example` con la documentación de todas las variables requeridas (Meta API, Upstash, cupo, umbral y alertas).
  - Creado `.env` local para desarrollo.
- **Módulo de Configuración**: Creado `app/__init__.py` y `app/config.py` con Pydantic Settings para validación tipada y carga automática de variables. Probado y funcionando correctamente.

### Lo Pendiente (Siguiente: Fase B):
- Implementar los endpoints `GET /webhook` (verificación de Meta) y `POST /webhook` (recepción de mensajes).
- Implementar la validación criptográfica de la firma `X-Hub-Signature-256` sobre bytes crudos.
- Crear la base de conocimiento estructurada (JSON) con soporte de palabras clave, sinónimos y marca de emergencia prioritaria.
- Escribir pruebas locales con `pytest` para verificar firma válida/inválida y coincidencia de palabras clave.