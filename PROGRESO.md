# PROGRESO DEL PROYECTO: BotAZ (WhatsApp Bot)

> **ESTADO DEL PROYECTO TRAS PIVOTE ESTRATÉGICO**  
> **Fecha y Hora:** 2026-10-26 06:05 (America/Caracas)  
> **Estado:** Fases A, B, C y D completadas al 100%. Pivote a conector local WhatsApp Web QR (Baileys) implementado y validado. Listo para vincular por QR.

---

## 1. Pivote Estratégico: Conector WhatsApp Web QR
- **Motivo**: Eliminación de bloqueos administrativos de Meta for Developers (requisito de empresa verificada, tarjeta de crédito y límite restrictivo de números de prueba).
- **Nueva Arquitectura**:
  - **Gateway QR (`gateway/`)**: Servicio en Node.js con Baileys (`@whiskeysockets/baileys`) en puerto 3001. Maneja la sesión persistente multi-dispositivo y genera el QR tanto en terminal como vía web.
  - **Cerebro del Bot (FastAPI)**: Mantiene al 100% el motor de conocimiento (`knowledge.json`), normalización de texto, coincidencia por palabra completa, deduplicación (`wamid`) y control de umbrales.
  - **Adapter Python (`app/whatsapp_adapter.py`)**: Interfaz asíncrona unificada para envío de texto e imágenes y consulta de estado del gateway.

---

## 2. Estado de Fases
- [x] **Fase A (Estructura y Configuración)**: Venv en PowerShell, dependencias FastAPI, Pydantic Settings, `.env` y seguridad gitignore.
- [x] **Fase B (Base de Conocimiento y Webhooks)**: Normalización de texto sin tildes, minúsculas y strip en `bot_service.py`, expresiones regulares de palabra completa (`\b`), prioridad para emergencias médicas (`tuinfo.vercel.app/emergencias`), bienvenida/menú inicial personalizado y mensaje de respaldo. **Base de conocimiento revisada y afinada tema por tema (13 temas activos)**:
  1. `bienvenida`: Saludo interactivo y ejemplos de consulta.
  2. `emergencia`: Líneas 24h y enlace a `tuinfo.vercel.app/emergencias` (prioridad alta).
  3. `carta_aval`: Requisitos de carta aval y correo CANTV.
  4. `reembolso`: Recaudos para reembolso médico y correo CANTV.
  5. `funeraria`: Previsivos El Rosal y enlace a `tuinfo.vercel.app/servicios-funerarios`.
  6. `farmacantv`: FarmaCANTV Occidente y correo oficial.
  7. `distribucion_nomina`: Desglose detallado de Pensión (571,20 Bs + 500 Bs), Bono Alimentario ($68) y Bono Vital ($150).
  8. `cronograma`: Calendario y pagos enlazado a `tuinfo.vercel.app/nomina`.
  9. `directorio_ajuptel`: Sede de AJUPTEL y teléfonos de la Junta Directiva.
  10. `gestion_humana`: Gestión Humana Región Zulia.
  11. `atencion_al_jubilado`: Atención al Jubilado Nivel Central.
  12. `cantv`: Averías y reportes CANTV / ABA.
  13. `ia`: Asistente con Inteligencia Artificial enlazado a `tuinfo.vercel.app/chat-deepseek`.
  14. `noticias_tasas`: Noticias y tasas de cambio oficiales enlazado a `leo2166.github.io/news-scraper` y `bcv.org.ve`.
  15. `autorizacion_bolsa`: Formato de autorización para retiro de bolsa de alimentación enlazado a `tuinfo.vercel.app/documentos/autorizacion-bolsa`.
  16. `cumpleanos`: Libreta de cumpleaños y felicitaciones enlazado a `cumpleaz.vercel.app`.
  - **Manual explicativo en PDF actualizado:** `MANUAL_BASE_DE_CONOCIMIENTO_BOTAZ.pdf`.
- [x] **Fase C (Reglas de Negocio e Idempotencia)**: Deduplicación con TTL de 24 horas, contador de mensajes entregados, umbral de corte (950 mensajes) con aviso único mensual y excepción de emergencias.
- [x] **Fase D (Pivote y Conector Gateway QR)**:
  - Creación de microservicio en `gateway/server.js` con dependencias instaladas (`@whiskeysockets/baileys`, `express`, `qrcode-terminal`, `qrcode`).
  - Implementación de `app/whatsapp_adapter.py` y endpoints en FastAPI: `POST /gateway/incoming`, `GET /qr` y `GET /gateway/status`.
  - Scripts de ejecución directa: `scripts/start_gateway.ps1` y `scripts/start_bot.ps1`.
  - **Corrección de Enrutamiento JID / LID y Robustez en Envío**:
    - Si el destino contiene `@lid`, se mantiene intacto (`...es@lid`) para `sock.sendMessage`.
    - Si contiene `@s.whatsapp.net`, se respeta tal cual.
    - Si solo contiene dígitos, se anexa `@s.whatsapp.net`.
    - Bloque `try/catch` envolviendo `sock.sendMessage` para retornar un JSON descriptivo con el fallo (`success: false, error: ...`) evitando errores 500 no controlados.
  - **Pruebas Automatizadas**: 30 pruebas ejecutadas, **30 aprobadas al 100%**.
- [ ] **Fase E (Despliegue y Mantenimiento)**: Persistencia de sesión y documentación de entrega final.

---

## 3. Instrucciones de Inicio y Vinculación QR
1. Terminal 1 (Servidor FastAPI):
   ```powershell
   .\venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
   ```
2. Terminal 2 (WhatsApp QR Gateway):
   ```powershell
   cd gateway
   npm start
   ```
3. Visualización y Vinculación:
   - El código QR se dibuja directamente en la terminal 2.
   - O bien, abre en tu navegador: **`http://localhost:8000/qr`** (se actualiza automáticamente).
   - Abre WhatsApp en tu celular > **Dispositivos vinculados** > **Vincular un dispositivo** y escanea el código.