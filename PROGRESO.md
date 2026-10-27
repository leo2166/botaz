# PROGRESO DEL PROYECTO: BotAZ (WhatsApp Bot)

> **ESTADO DEL PROYECTO: PRODUCCIÓN ACTIVA EN LA NUBE**  
> **Fecha y Hora:** 2026-10-26 22:15 (America/Caracas)  
> **Estado:** Fases A, B, C, D y E completadas al 100%. Desplegado en producción en **Render.com** (`https://botaz.onrender.com`), vinculado y respondiendo en vivo por WhatsApp Web.

---

## 1. Arquitectura y Despliegue en la Nube
- **Hosting en la Nube**: Render.com (Web Service Docker multi-stage ultra ligero < 250 MB).
- **URL Pública**: `https://botaz.onrender.com`
- **Página de Vinculación QR**: `https://botaz.onrender.com/qr` (Monitoreo visual del estado de conexión).
- **Keep-Alive 24/7**: Endpoint `/health` integrable con UptimeRobot (pings cada 5 minutos para evitar suspensión por inactividad).
- **Cerebro del Bot (FastAPI)**: Motor de conocimiento (`knowledge.json`), normalización de texto, coincidencia por palabra completa (`\b`), deduplicación y control de cupo.
- **Gateway QR (Baileys Node.js)**: Manejo de sesión persistente multi-dispositivo y envío/recepción de mensajes en tiempo real.

---

## 2. Estado de Fases
- [x] **Fase A (Estructura y Configuración)**: Venv en PowerShell, dependencias FastAPI, Pydantic Settings, `.env` y seguridad gitignore.
- [x] **Fase B (Base de Conocimiento y Webhooks)**: Normalización de texto sin tildes, minúsculas y strip en `bot_service.py`, expresiones regulares de palabra completa (`\b`), prioridad para emergencias médicas (`tuinfo.vercel.app/emergencias`), bienvenida/menú inicial personalizado y mensaje de respaldo. **Base de conocimiento afinada (16 temas activos)**.
- [x] **Fase C (Reglas de Negocio e Idempotencia)**: Deduplicación con TTL de 24 horas, contador de mensajes entregados, umbral de corte (950 mensajes) con aviso único mensual y excepción de emergencias.
- [x] **Fase D (Pivote y Conector Gateway QR)**: Microservicio en `gateway/server.js`, adaptador `app/whatsapp_adapter.py`, endpoints en FastAPI y batería de 30 pruebas aprobadas (100%).
- [x] **Fase E (Despliegue y Producción en Render)**:
  - `Dockerfile` multi-etapa unificado para Python 3.11 + Node.js 20.
  - Script de arranque `start.sh` para iniciar Gateway y FastAPI coordinadamente en el puerto asignado.
  - Despliegue exitoso en Render.com (`https://botaz.onrender.com`).
  - Vinculación exitosa mediante código QR servido en `/qr`.
  - Manual explicativo en PDF generado: `MANUAL_BASE_DE_CONOCIMIENTO_BOTAZ.pdf`.

---

## 3. Guía de Mantenimiento y Actualización de la Base de Conocimiento

### A. Modificar o Añadir Temas en `app/knowledge.json`
Cada tema cuenta con la siguiente estructura limpia:
```json
{
  "keywords": ["palabra_clave", "sinonimo"],
  "response": "Texto claro de respuesta para el jubilado con enlaces oficiales.",
  "image_url": "https://enlace-opcional-a-imagen.png",
  "priority": false
}
```

### B. Regenerar el Manual en PDF Ordenado por Temas
Para generar el manual en PDF con la lista de temas numerada y explicada:
```powershell
.\venv\Scripts\python scripts/generate_kb_pdf.py
```
El archivo `MANUAL_BASE_DE_CONOCIMIENTO_BOTAZ.pdf` se actualizará automáticamente con todos los cambios.

### C. Desplegar los Cambios a la Nube (Render)
Para que los cambios se apliquen automáticamente en producción:
```powershell
git add app/knowledge.json
git commit -m "update: actualización de base de conocimiento"
git push origin main
```
Render detectará el cambio en GitHub y desplegará la actualización en menos de 1 minuto sin perder la sesión de WhatsApp.