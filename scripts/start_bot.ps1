# Script para iniciar el servidor FastAPI del BotAZ
Write-Host "=== INICIANDO SERVIDOR BOTAZ (FASTAPI) ===" -ForegroundColor Green
Set-Location "$PSScriptRoot\.."
.\venv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
