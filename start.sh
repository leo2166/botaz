#!/bin/bash
set -e

# Tomar el puerto asignado por Hostless o usar 8000 por defecto
APP_PORT=${PORT:-8000}
export FASTAPI_WEBHOOK_URL="http://localhost:${APP_PORT}/gateway/incoming"
export GATEWAY_URL="http://localhost:3001"
export GATEWAY_PORT=3001

echo "=========================================================="
echo "Iniciando BotAZ (FastAPI + Baileys QR Gateway)..."
echo "Puerto FastAPI: ${APP_PORT}"
echo "Puerto Gateway: ${GATEWAY_PORT}"
echo "FastAPI Webhook: ${FASTAPI_WEBHOOK_URL}"
echo "=========================================================="

# 1. Iniciar Gateway de Baileys en segundo plano con auto-recuperación permanente
(
  cd /app/gateway
  while true; do
    echo "[start.sh] Iniciando Gateway Node.js (Baileys)..."
    node server.js
    EXIT_CODE=$?
    echo "[start.sh] Gateway Node.js finalizó con código ${EXIT_CODE}. Reiniciando automáticamente en 2 segundos..."
    sleep 2
  done
) &
GATEWAY_PID=$!
cd /app

# 2. Iniciar FastAPI en primer plano con Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}"
