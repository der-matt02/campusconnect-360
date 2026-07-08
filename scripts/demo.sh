#!/usr/bin/env bash
# ============================================================
#  CampusConnect 360 — Demostracion automatica "un dia de operacion"
#  Ejecuta el flujo completo a traves del API Gateway con JWT.
#  Cada actor usa su propio token segun el rol asignado.
#  Requisitos: el ecosistema corriendo (docker compose up) y python3.
# ============================================================
set -e

GATEWAY="${GATEWAY:-http://localhost:8000}"

jqget() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }
step()  { echo; echo "==== $1 ===="; }
login() { curl -s -X POST "$GATEWAY/auth/login" -H "Content-Type: application/json" \
            -d "{\"username\":\"$1\",\"password\":\"campus123\"}" | jqget "['access_token']"; }

step "0. Obtencion de tokens por actor"
AUTH_SEC="Authorization: Bearer $(login secretaria)"
AUTH_FIN="Authorization: Bearer $(login finanzas)"
AUTH_DOC="Authorization: Bearer $(login docente)"
AUTH_DIR="Authorization: Bearer $(login director)"
echo "Tokens obtenidos para secretaria, finanzas, docente y director."

step "1. Secretaria registra un estudiante"
SID=$(curl -s -X POST "$GATEWAY/api/academico/students" -H "$AUTH_SEC" -H "Content-Type: application/json" \
  -d '{"full_name":"Demo Estudiante","document_id":"1700DEMO01","email":"demo@example.edu","school_id":"SCH-001","grade":"8vo EGB"}' \
  | jqget "['id']")
echo "Estudiante creado: $SID"

step "2. Secretaria crea la matricula -> publica StudentEnrolled"
curl -s -X POST "$GATEWAY/api/academico/enrollments" -H "$AUTH_SEC" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"period\":\"2026-1\"}" >/dev/null
echo "Matricula creada. Esperando propagacion de eventos..."; sleep 3

step "3. Finanzas confirma el pago de matricula -> publica PaymentConfirmed"
PAY=$(curl -s -H "$AUTH_FIN" "$GATEWAY/api/pagos/students/$SID" | jqget "['payments'][0]['id']")
curl -s -X POST -H "$AUTH_FIN" "$GATEWAY/api/pagos/payments/$PAY/confirm" >/dev/null
echo "Pago $PAY confirmado. Esperando propagacion..."; sleep 3

step "4. Secretaria verifica el estado financiero actualizado (StudentStatusUpdated)"
curl -s -H "$AUTH_SEC" "$GATEWAY/api/academico/students/$SID" | jqget "['financial_status']" \
  | sed 's/^/Estado financiero: /'

step "5. Docente registra asistencia e incidente"
curl -s -X POST "$GATEWAY/api/asistencia/attendance" -H "$AUTH_DOC" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"date\":\"2026-06-12\",\"status\":\"PRESENTE\"}" >/dev/null
curl -s -X POST "$GATEWAY/api/asistencia/incidents" -H "$AUTH_DOC" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"severity\":\"BAJA\",\"description\":\"Sin novedad mayor\"}" >/dev/null
echo "Asistencia e incidente registrados."; sleep 3

step "6. Dashboard directivo (indicadores CQRS)"
curl -s -H "$AUTH_DIR" "$GATEWAY/api/analitica/dashboard" | python3 -m json.tool

step "7. Escenario de falla: activar chaos, generar evento -> DLQ"
curl -s -X POST "$GATEWAY/api/notificaciones/chaos" -H "$AUTH_DIR" -H "Content-Type: application/json" \
  -d '{"enabled":true}' >/dev/null
curl -s -X POST "$GATEWAY/api/asistencia/attendance" -H "$AUTH_DOC" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"date\":\"2026-06-13\",\"status\":\"AUSENTE\"}" >/dev/null
echo "Evento generado bajo fallo. Esperando reintentos + dead-letter..."; sleep 9
curl -s -H "$AUTH_DIR" "$GATEWAY/api/notificaciones/dlq" | jqget "['dlqDepth']" | sed 's/^/Mensajes en DLQ: /'

step "8. Recuperacion: desactivar chaos y reprocesar la DLQ"
curl -s -X POST "$GATEWAY/api/notificaciones/chaos" -H "$AUTH_DIR" -H "Content-Type: application/json" \
  -d '{"enabled":false}' >/dev/null
curl -s -X POST -H "$AUTH_DIR" "$GATEWAY/api/notificaciones/dlq/reprocess" | python3 -m json.tool

step "9. Salud agregada del ecosistema"
curl -s "$GATEWAY/health" | python3 -m json.tool

echo; echo "==== Demostracion completada ===="
