# PLAN DE IMPLEMENTACIÓN POR FASES (BotAZ)

> **HISTORIAL DE PIVOTE**:
> Fases A, B y C desarrollaron la estructura, base de conocimiento y lógica de negocio.
> La Fase D incorpora el pivote a **Conector Gateway QR (WhatsApp Web / Baileys)** para eliminar bloqueos administrativos de Meta.

- **Fase A**: Estructura del proyecto, dependencias, entorno virtual en PowerShell, configuración por variables (.env). *(COMPLETADA)*
- **Fase B**: Webhook FastAPI, validación de firma criptográfica, base de conocimiento JSON, normalización y pruebas locales. *(COMPLETADA)*
- **Fase C**: Envío de texto + imagen con caption, menú de respaldo, contador, reglas de corte (950 msgs) y aviso mensual único. *(COMPLETADA)*
- **Fase D (Pivote Gateway QR)**: Microservicio Gateway con Baileys en Node.js, adapter FastAPI (`/gateway/incoming`, `/qr`, `/status`), visualizador de código QR en consola y navegador, y pruebas integradas. *(COMPLETADA)*
- **Fase E**: Despliegue en producción (servidor/VPS o contenedor), persistencia de credenciales de sesión WhatsApp y documentación de mantenimiento. *(PENDIENTE)*

---

# ENTREGABLES FINALES
- Manual de inicio y escaneo de QR.
- Lista de variables de entorno.
- Guía para agregar o modificar palabras clave en `knowledge.json` sin tocar código.
- Configuración de límites y umbral de aviso mensual.
