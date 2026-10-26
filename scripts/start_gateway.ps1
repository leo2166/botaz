# Script para iniciar el conector WhatsApp Web QR (Baileys)
Write-Host "=== INICIANDO WHATSAPP QR GATEWAY (BAILEYS) ===" -ForegroundColor Cyan
Set-Location "$PSScriptRoot\..\gateway"
npm start
