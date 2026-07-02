#!/usr/bin/env python3
"""
start_tunnel.py — Túnel Cloudflare para CampusConnect 360
==========================================================
Expone el ecosistema completo (Frontend + Gateway via Nginx reverse proxy)
a internet con una sola URL pública usando cloudflared en Docker.

Uso:
    python scripts/start_tunnel.py

Requisitos:
    - Docker en ejecución
    - docker compose up -d (el stack de CampusConnect levantado)

Funcionamiento:
    1. Detecta la red Docker del proyecto automáticamente.
    2. Limpia contenedores de túneles anteriores (ejecuciones repetidas).
    3. Lanza un contenedor cloudflared apuntando a http://frontend:80.
    4. Espera a que Cloudflare asigne una URL pública (máx. 30 seg).
    5. Muestra la URL en pantalla de forma destacada.
    6. Mantiene el túnel activo hasta Ctrl+C y limpia al salir.
"""

import re
import signal
import subprocess
import sys
import time

# ─── Configuración ────────────────────────────────────────────────────────────
CONTAINER_NAME = "cc360-tunnel"
TUNNEL_TARGET = "http://frontend:80"
NETWORK_PATTERN = re.compile(r"campusconnect360_default")
URL_PATTERN = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")
WAIT_TIMEOUT_SEC = 45
POLL_INTERVAL_SEC = 1

# ─── Colores ANSI (compatibles con Windows 10+) ───────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    """Ejecuta un comando de shell y retorna el resultado."""
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )


def detect_docker_network() -> str:
    """Detecta automáticamente la red Docker del proyecto."""
    result = run(["docker", "network", "ls", "--format", "{{.Name}}"], capture=True)
    for line in result.stdout.splitlines():
        if NETWORK_PATTERN.search(line):
            return line.strip()

    # Fallback: buscar cualquier red que contenga 'campusconnect'
    for line in result.stdout.splitlines():
        if "campusconnect" in line.lower():
            return line.strip()

    return None


def cleanup_tunnel():
    """Elimina el contenedor del túnel si existe (limpieza idempotente)."""
    result = run(
        ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
        capture=True,
    )
    if CONTAINER_NAME in result.stdout:
        print(f"{YELLOW}⚠  Eliminando contenedor anterior: {CONTAINER_NAME}{RESET}")
        run(["docker", "rm", "-f", CONTAINER_NAME])


def wait_for_tunnel_url() -> str | None:
    """
    Espera y extrae la URL pública asignada por Cloudflare desde los logs
    del contenedor, con reintentos durante WAIT_TIMEOUT_SEC segundos.
    """
    print(f"{CYAN}⏳ Esperando URL de Cloudflare", end="", flush=True)
    deadline = time.time() + WAIT_TIMEOUT_SEC

    while time.time() < deadline:
        result = run(["docker", "logs", CONTAINER_NAME], capture=True)
        # cloudflared escribe la URL tanto en stdout como stderr
        combined = result.stdout + result.stderr
        match = URL_PATTERN.search(combined)
        if match:
            print()  # nueva línea tras los puntos de progreso
            return match.group(0)
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL_SEC)

    print()
    return None


def verify_frontend_running() -> bool:
    """Verifica que el contenedor 'frontend' esté en ejecución."""
    result = run(
        ["docker", "ps", "--filter", "name=frontend", "--filter", "status=running",
         "--format", "{{.Names}}"],
        capture=True,
    )
    return "frontend" in result.stdout


def print_banner(url: str):
    """Imprime la URL pública de forma destacada en la terminal."""
    separator = "═" * 60
    print(f"\n{BOLD}{GREEN}{separator}{RESET}")
    print(f"{BOLD}{GREEN}  🚀 CAMPUSCONNECT 360 — EN LÍNEA{RESET}")
    print(f"{BOLD}{GREEN}{separator}{RESET}")
    print(f"\n  {BOLD}Portal Web:{RESET}")
    print(f"  {CYAN}{BOLD}{url}{RESET}")
    print(f"\n  {BOLD}Comparte esta URL para la demostración.{RESET}")
    print(f"  Usuarios: {YELLOW}director{RESET} / {YELLOW}secretaria{RESET} / "
          f"{YELLOW}finanzas{RESET} / {YELLOW}docente{RESET}")
    print(f"  Contraseña: {YELLOW}campus123{RESET}")
    print(f"\n{BOLD}{GREEN}{separator}{RESET}")
    print(f"\n{YELLOW}  Presiona Ctrl+C para detener el túnel y cerrar.{RESET}\n")


def main():
    # Habilitar colores ANSI en Windows
    if sys.platform == "win32":
        import os
        os.system("color")

    print(f"\n{BOLD}CampusConnect 360 — Iniciando túnel Cloudflare...{RESET}\n")

    # 1. Verificar que Docker está disponible
    result = run(["docker", "info"], capture=True)
    if result.returncode != 0:
        print(f"{RED}✗ Docker no está en ejecución. Inicia Docker Desktop e intenta de nuevo.{RESET}")
        sys.exit(1)

    # 2. Verificar que el stack está levantado
    if not verify_frontend_running():
        print(f"{RED}✗ El contenedor 'frontend' no está corriendo.{RESET}")
        print(f"  Ejecuta primero: {CYAN}docker compose up -d{RESET}")
        sys.exit(1)

    # 3. Detectar la red Docker
    network = detect_docker_network()
    if not network:
        print(f"{RED}✗ No se encontró la red Docker de CampusConnect 360.{RESET}")
        print(f"  Asegúrate de que el docker-compose.yml define 'name: campusconnect360'.")
        sys.exit(1)
    print(f"{GREEN}✓ Red Docker detectada:{RESET} {network}")

    # 4. Limpiar contenedores de túneles anteriores
    cleanup_tunnel()

    # 5. Lanzar el contenedor del túnel
    print(f"{GREEN}✓ Iniciando túnel hacia {TUNNEL_TARGET}...{RESET}")
    result = run([
        "docker", "run",
        "--detach",
        "--name", CONTAINER_NAME,
        "--network", network,
        "--restart", "unless-stopped",
        "cloudflare/cloudflared:latest",
        "tunnel",
        "--url", TUNNEL_TARGET,
        "--no-autoupdate",
    ])

    if result.returncode != 0:
        print(f"{RED}✗ Error al iniciar el contenedor cloudflared.{RESET}")
        sys.exit(1)

    # 6. Esperar y extraer la URL pública
    public_url = wait_for_tunnel_url()
    if not public_url:
        print(f"{RED}✗ Tiempo de espera agotado. Cloudflare no generó la URL en {WAIT_TIMEOUT_SEC}s.{RESET}")
        print(f"  Revisa los logs con: {CYAN}docker logs {CONTAINER_NAME}{RESET}")
        cleanup_tunnel()
        sys.exit(1)

    # 7. Mostrar la URL de forma destacada
    print_banner(public_url)

    # 8. Mantener vivo hasta Ctrl+C y limpiar al salir
    def handle_exit(sig, frame):
        print(f"\n{YELLOW}⏹  Deteniendo túnel...{RESET}")
        cleanup_tunnel()
        print(f"{GREEN}✓ Túnel cerrado. ¡Hasta luego!{RESET}\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Mantener el proceso vivo
    while True:
        time.sleep(5)


if __name__ == "__main__":
    main()
