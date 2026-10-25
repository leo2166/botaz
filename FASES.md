# PASO 3 — IMPLEMENTACIÓN POR FASES (confirmo al final de cada una)
Fase A: estructura del proyecto, dependencias, entorno virtual en PowerShell, configuración por variables.
Fase B: webhook + validación de firma + base de conocimiento + pruebas locales.
Fase C: envío de texto + imagen, menú de respaldo, contador con almacenamiento externo, aviso mensual único y alertas.
Fase D: exposición temporal (ngrok o cloudflared) y prueba con el número de prueba de Meta.
Fase E: despliegue en el hosting elegido, token permanente de usuario del sistema y checklist de producción.
Pruebas (pytest) obligatorias: firma válida/inválida, coincidencia de palabra clave, menú de respaldo, contador, umbral de corte y aviso único por usuario.

# ENTREGABLES FINALES
README con pasos de despliegue, lista de variables de entorno, cómo agregar una palabra clave nueva sin tocar código, cómo cambiar el límite o el umbral, y una lista de los riesgos que sigan abiertos.


Organizando cómo estructurar un prompt extenso para Antigravity.
Organizando cómo estructurar un prompt extenso para Antigravity.
Hay dos formas. La más fiable es dividirlo en archivos, porque un agente al que le das todo el plan junto tiende a adelantarse aunque le pidas que pare. Si no ve las fases posteriores, no puede saltar a ellas.
Opción recomendada: archivos + prompts cortos
Crea una carpeta de proyecto (por ejemplo bot-whatsapp) con estos archivos, copiando en cada uno la sección correspondiente del prompt definitivo:
Archivo	Contenido
REGLAS.md	“Rol y forma de trabajo” + “Objetivo del proyecto”
DATOS_META.md	Paso 1 (datos verificados + lo que debe investigar)
ARQUITECTURA.md	Paso 2 completo
FASES.md	Paso 3 (fases A a E) + entregables finales
PROGRESO.md	Archivo vacío por ahora (el agente lo llena)
