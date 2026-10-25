
# PASO 0 — SKILLS (obligatorio, antes de escribir código)
1. Usa la skill `find-skills` (o `npx skills find <término>`) para buscar skills útiles. Términos: fastapi, python, whatsapp, webhook, api-security, deployment, render, testing, env-secrets.
2. NO instales nada todavía. Preséntame una lista corta (máximo 5): nombre, qué hace, por qué la necesito y cuánto contexto/tokens consume.
3. Cuando yo apruebe, instala solo esas, a nivel de proyecto (sin `-g`), y confírmame la ruta donde quedaron.
4. Si no hay skills útiles, dilo y continúa sin ellas. No instales "por si acaso".

# PASO 1 — DATOS YA VERIFICADOS (fuente oficial de Meta, leída el 25-oct-2026)
Tómalos como base, pero reconfirma en la documentación oficial antes de implementar (Meta solo cambia precios el 1 de ene/abr/jul/oct):
- Cada número de negocio tiene 1,000 mensajes de servicio gratis por mes. Se cuentan mensajes ENTREGADOS del bot al usuario. Texto e imagen cuentan igual. Un envío con imagen + caption = 1 mensaje. Los mensajes del usuario al bot no cuentan.
- El cupo se reinicia a las 12 a.m. en la zona horaria de la cuenta de mensajería (configurarla en America/Caracas). Lo no usado no se acumula.
- Desde el mensaje 1,001 se cobra (Venezuela entra en la región "Rest of Latin America").
- Sin método de pago en Billing Hub, Meta entrega mensajes dentro del cupo gratis y deja de entregarlos después, sin aviso al usuario. Es el freno de seguridad que quiero conservar.
- Organizaciones elegibles (ONG comunitarias, gobierno) tienen mensajes de servicio gratis sin tope hasta el 31-dic-2027. Verifica si mi cuenta es elegible con `GET /<WABA_ID>?fields=id,name,service_pricing_policy` (PAID_EXEMPT = exenta) y dime el resultado.
- El plan original hablaba de "1,000 conversaciones/mes". Eso está obsoleto: ya no existe el modelo por conversación.

Investiga además, y resúmeme en pocas líneas:
- Versión vigente de la Graph API (el borrador usaba v18.0, que es vieja). Dejarla en una variable de configuración.
- Requisitos reales para producción: verificación del negocio, el número no puede estar activo en la app normal de WhatsApp, el número de prueba solo permite 5 destinatarios, token de usuario del sistema permanente.
- Estado actual de la capa gratuita de Render, Koyeb y Oracle Always Free: ¿piden tarjeta?, ¿duermen el servicio?, ¿funcionan desde Venezuela? Recomiéndame UNA opción con su punto débil.
- Almacenamiento externo gratuito para el contador (Supabase, Upstash Redis u otro viable desde Venezuela).
