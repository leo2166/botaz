# Script de PowerShell para exponer el bot local a Internet mediante túnel seguro (HTTPS)
# Uso: .\scripts\run_tunnel.ps1

Write-Host "=== EXPOSICIÓN LOCAL TEMPORAL - BOTAZ ===" -ForegroundColor Cyan

# 1. Comprobar si cloudflared o ngrok están instalados
$hasCloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
$hasNgrok = Get-Command ngrok -ErrorAction SilentlyContinue

if ($hasCloudflared) {
    Write-Host "[OK] Detectado cloudflared. Iniciando túnel rápido gratuito hacia http://localhost:8000..." -ForegroundColor Green
    cloudflared tunnel --url http://localhost:8000
} elseif ($hasNgrok) {
    Write-Host "[OK] Detectado ngrok. Iniciando túnel hacia http://localhost:8000..." -ForegroundColor Green
    ngrok http 8000
} else {
    Write-Host "[INFO] No se detectó cloudflared ni ngrok en el PATH." -ForegroundColor Yellow
    Write-Host "Puedes instalar cloudflared fácilmente (gratuito y sin registro) con winget:" -ForegroundColor Yellow
    Write-Host "    winget install --id Cloudflare.cloudflared -e" -ForegroundColor White
    Write-Host "O si prefieres ngrok:" -ForegroundColor Yellow
    Write-Host "    winget install --id Inconshreveable.ngrok -e" -ForegroundColor White
}
