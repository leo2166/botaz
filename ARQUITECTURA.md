# PASO 2 — REQUISITOS DE ARQUITECTURA
Webhook y mensajes:
- GET /webhook (verificación de Meta) y POST /webhook (mensajes) en FastAPI.
- Validar la firma X-Hub-Signature-256 con el App Secret en cada POST; rechazar con 403 si no coincide.
- Responder 200 a Meta de inmediato y enviar la respuesta en segundo plano (BackgroundTasks), con httpx async, timeout y reintentos acotados. Nada de requests bloqueante.
- Ignorar sin error los webhooks de estado que no se necesiten y los tipos de mensaje no soportados (audio, stickers) con una respuesta cortés.

Base de conocimiento:
- Archivo JSON o YAML editable por una persona no técnica: palabra clave, sinónimos, texto, imagen, y una marca "prioritaria" para contenido de emergencia.
- Normalizar la entrada: minúsculas, sin tildes, coincidencia por palabra completa (no por subcadena).
- Si no hay coincidencia, responder con un menú breve de las palabras clave disponibles (cuenta como mensaje, mantenerlo corto).
- Imágenes servidas desde una URL pública estable (carpeta estática del propio servicio o equivalente gratuito), optimizadas en tamaño.

Contador y corte:
- Contar con los webhooks de estado "delivered" y su objeto `pricing` (billable / type / subtype), no con envíos propios.
- Almacenamiento externo gratuito, incremento atómico, reinicio mensual en America/Caracas.
- Variables configurables: LIMITE_MENSUAL (por defecto 1000) y UMBRAL_CORTE (por defecto 950, para reservar colchón para avisos).
- Al llegar al umbral: dejar de responder consultas normales y enviar UNA SOLA vez por usuario al mes un aviso con la fecha de restablecimiento y una vía alternativa de contacto. Después, silencio total para ese usuario hasta el nuevo mes.
- Las palabras clave marcadas como prioritarias (emergencia) pueden seguir respondiendo hasta el límite duro de Meta, si yo lo activo con una variable.
- Si service_pricing_policy = PAID_EXEMPT, desactivar el corte y dejar solo las alertas.
- Alertas (a mí, por correo o mensaje) al 70% y al 90% del límite.
- Los fallos de entrega después del tope son esperados: registrarlos sin reintentar en bucle.
- Mensaje de aviso sugerido (adaptable): "Lo sentimos. Se alcanzó el cupo de respuestas automáticas de este mes. El servicio se restablece el 1 de [mes siguiente]. Para asuntos urgentes, comuníquese directamente con AJUPTEL Zulia."

Seguridad y privacidad:
- Secretos solo en variables de entorno (.env local, panel del hosting en producción). Crear .env.example y .gitignore. Nunca secretos en código ni en el repo.
- Enmascarar los números de teléfono en los logs. No guardar más datos de usuarios que los necesarios para el aviso mensual.
- Endpoint /health para monitoreo (UptimeRobot) y manejo del arranque en frío del hosting.

# REQUISITOS ADICIONALES (tras revisión del Paso 1)
- Idempotencia: Meta reintenta webhooks (sobre todo tras el arranque en frío de Render, ~1 minuto). Guardar el ID de cada mensaje entrante (wamid) en Upstash con SET NX y expiración de 24 h, y descartar duplicados. Un reintento NUNCA debe generar una segunda respuesta.
- Firma X-Hub-Signature-256: calcularla sobre los BYTES CRUDOS del cuerpo (await request.body()), no sobre el JSON ya parseado, y comparar con hmac.compare_digest. Error clásico: validar sobre el JSON re-serializado.
- Responder 200 a Meta lo antes posible; todo el trabajo pesado va en segundo plano.
- Imágenes: ≤ 200 KB cada una. El plan Hobby de Render incluye solo 5 GB de salida al mes. Preferible alojarlas en un sitio estático aparte (por ejemplo Vercel) para que la descarga de la imagen no dependa del servidor que se duerme.
- Keep-alive: endpoint /health y un ping cada 5 minutos con UptimeRobot. Desplegar UN solo servicio en Render (las 750 h son por cuenta, y un mes de 31 días tiene 744 h).
- Datos corregidos de Upstash: capa gratuita de 500.000 comandos/mes, sin tarjeta. Usar las llamadas REST.
- Datos corregidos de Render: arranque en frío de aproximadamente un minuto.
