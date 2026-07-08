#!/usr/bin/env bash
# ============================================================
#  Mide la cobertura de pruebas de todo el proyecto.
#  Cada microservicio corre en su propio proceso porque todos
#  tienen un paquete llamado "app" (evita colision en sys.modules).
#  Los resultados se combinan con coverage.
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYBIN="${PYBIN:-python}"
cd "$ROOT"

rm -f .coverage .coverage.*

run_cov() {
  local sources="$1"; shift
  "$PYBIN" -m coverage run --parallel-mode --source="$sources" -m pytest "$@" -q
}

# Capa compartida (pruebas en la raiz).
PYTHONPATH="$ROOT" run_cov "shared" tests

# Microservicios con base de datos (SQLite en memoria).
for svc in academico pagos asistencia notificaciones analitica; do
  DATABASE_URL="sqlite://" PYTHONPATH="$ROOT:$ROOT/services/$svc" \
    run_cov "$ROOT/services/$svc/app,$ROOT/shared" "services/$svc/tests"
done

# API Gateway (sin base de datos).
PYTHONPATH="$ROOT:$ROOT/gateway" \
  run_cov "$ROOT/gateway/app,$ROOT/shared" "gateway/tests"

"$PYBIN" -m coverage combine
"$PYBIN" -m coverage report --fail-under=95 -m
