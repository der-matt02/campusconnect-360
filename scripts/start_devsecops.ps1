# start_devsecops.ps1
# Ecosistema CampusConnect 360 - Levantamiento rápido
# ====================================================

# Colores de Consola
$GREEN  = "`e[92m"
$YELLOW = "`e[93m"
$CYAN   = "`e[96m"
$RED    = "`e[91m"
$RESET  = "`e[0m"

Write-Host "`n$CYAN==================================================$RESET"
Write-Host "$CYAN🚀 CAMPUSCONNECT 360 - START DEVSECOPS$RESET"
Write-Host "$CYAN==================================================$RESET`n"

# 1. Verificar variable de entorno GITHUB_TOKEN
if (-not $env:GITHUB_TOKEN) {
    Write-Host "$RED[✗] Error: La variable `$env:GITHUB_TOKEN` no está configurada.$RESET"
    Write-Host "$YELLOWPor favor, configúrala antes de arrancar:`n`$env:GITHUB_TOKEN = `"ghp_xxxx`"$RESET`n"
    Exit 1
}
Write-Host "$GREEN[✓] Variable GITHUB_TOKEN detectada.$RESET"

# 2. Verificar que Minikube está corriendo
$minikubeStatus = minikube status --format "{{.Host}}" 2>$null
if ($minikubeStatus -ne "Running") {
    Write-Host "$YELLOW[!] Minikube no está en ejecución. Iniciando Minikube...$RESET"
    minikube start
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$RED[✗] Error al iniciar Minikube.$RESET"
        Exit 1
    }
}
Write-Host "$GREEN[✓] Minikube está corriendo.$RESET"

# 3. Asegurar que existe el secreto de GHCR en campusconnect-dev
Write-Host "$CYAN[*] Verificando secreto ghcr-secret en namespace campusconnect-dev...$RESET"
$secretExists = kubectl get secret ghcr-secret -n campusconnect-dev 2>$null
if (-not $secretExists) {
    Write-Host "$YELLOW[!] Creando secreto ghcr-secret con tus credenciales...$RESET"
    kubectl create secret docker-registry ghcr-secret `
      --docker-server=ghcr.io `
      --docker-username="galeyro" `
      --docker-password="$env:GITHUB_TOKEN" `
      -n campusconnect-dev
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$RED[✗] Error al crear el secreto ghcr-secret.$RESET"
        Exit 1
    }
    # Forzar recreación de pods si el secreto es nuevo
    Write-Host "$YELLOW[!] Reiniciando pods para aplicar el nuevo secreto...$RESET"
    kubectl delete pods --all -n campusconnect-dev --grace-period=0 --force
} else {
    Write-Host "$GREEN[✓] Secreto ghcr-secret ya existe.$RESET"
}

# 4. Iniciar Port-Forward en una ventana de consola independiente
Write-Host "$CYAN[*] Levantando Port-Forward al puerto 8080 en segundo plano...$RESET"
$pfProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward service/ingress-nginx-controller 8080:80 -n ingress-nginx" -PassThru
Write-Host "$GREEN[✓] Port-Forward iniciado. Mantén abierta la ventana emergente.$RESET"

# 5. Iniciar ngrok en esta ventana (mantiene el proceso vivo)
Write-Host "`n$YELLOW[*] Iniciando ngrok sobre tu dominio estático...$RESET"
Write-Host "$CYANURL pública persistente: https://runaround-think-sublet.ngrok-free.dev$RESET"
Write-Host "$YELLOWPresiona Ctrl+C en esta terminal para detener ngrok cuando hayas terminado.`n$RESET"

ngrok http 127.0.0.1:8080 --domain=runaround-think-sublet.ngrok-free.dev
