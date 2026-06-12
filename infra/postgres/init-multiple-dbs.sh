#!/bin/bash
# ============================================================
#  Crea una base de datos independiente por microservicio.
#  Esto cumple el requisito de "persistencia separada por servicio".
# ============================================================
set -e

create_db() {
  local db=$1
  echo "  -> creando base de datos: $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE $db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
}

for db in "$DB_ACADEMICO" "$DB_PAGOS" "$DB_ASISTENCIA" "$DB_NOTIFICACIONES" "$DB_ANALITICA"; do
  create_db "$db"
done

echo "Bases de datos por servicio creadas."
