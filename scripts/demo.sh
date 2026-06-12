#!/usr/bin/env bash
# ============================================================
#  CampusConnect 360 — Demostracion automatica "un dia de operacion"
#  Ejecuta el flujo completo a traves del API Gateway con JWT.
#  Requisitos: el ecosistema corriendo (docker compose up) y python3.
# ============================================================
set -e

GATEWAY="${GATEWAY:-http://localhost:8000}"

jqget() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }
step()  { echo; echo "==== $1 ===="; }

step "0. Login como Secretaria (obtiene JWT)"
TOKEN=$(curl -s -X POST "$GATEWAY/auth/login" -H "Content-Type: application/json" \
  -d '{"username":"secretaria","password":"campus123"}' | jqget "['access_token']")
AUTH="Authorization: Bearer $TOKEN"
echo "JWT obtenido."

step "1. Secretaria registra un estudiante"
SID=$(curl -s -X POST "$GATEWAY/api/academico/students" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"full_name":"Demo Estudiante","document_id":"1700DEMO01","email":"demo@example.edu","school_id":"SCH-001","grade":"8vo EGB"}' \
  | jqget "['id']")
echo "Estudiante creado: $SID"

step "2. Crea la matricula -> publica StudentEnrolled"
curl -s -X POST "$GATEWAY/api/academico/enrollments" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"period\":\"2026-1\"}" >/dev/null
echo "Matricula creada. Esperando propagacion de eventos..."; sleep 3

step "3. Finanzas confirma el pago de matricula -> publica PaymentConfirmed"
PAY=$(curl -s -H "$AUTH" "$GATEWAY/api/pagos/students/$SID" | jqget "['payments'][0]['id']")
curl -s -X POST -H "$AUTH" "$GATEWAY/api/pagos/payments/$PAY/confirm" >/dev/null
echo "Pago $PAY confirmado."; sleep 3

step "4. El Servicio Academico refleja el estado financiero"
curl -s -H "$AUTH" "$GATEWAY/api/academico/students/$SID" | jqget "['financial_status']" \
  | sed 's/^/Estado financiero: /'

step "5. Docente registra asistencia e incidente"
curl -s -X POST "$GATEWAY/api/asistencia/attendance" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"date\":\"2026-06-12\",\"status\":\"presente\"}" >/dev/null
curl -s -X POST "$GATEWAY/api/asistencia/incidents" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"severity\":\"baja\",\"description\":\"Sin novedad mayor\"}" >/dev/null
echo "Asistencia e incidente registrados."; sleep 3

step "6. Dashboard directivo (indicadores CQRS)"
curl -s -H "$AUTH" "$GATEWAY/api/analitica/dashboard" | python3 -m json.tool

step "7. Escenario de falla: activar chaos, generar evento -> DLQ"
curl -s -X POST "$GATEWAY/api/notificaciones/chaos" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"enabled":true}' >/dev/null
curl -s -X POST "$GATEWAY/api/asistencia/attendance" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"student_id\":\"$SID\",\"date\":\"2026-06-13\",\"status\":\"ausente\"}" >/dev/null
echo "Evento generado bajo fallo. Esperando reintentos + dead-letter..."; sleep 9
curl -s -H "$AUTH" "$GATEWAY/api/notificaciones/dlq" | jqget "['dlqDepth']" | sed 's/^/Mensajes en DLQ: /'

step "8. Recuperacion: desactivar chaos y reprocesar la DLQ"
curl -s -X POST "$GATEWAY/api/notificaciones/chaos" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"enabled":false}' >/dev/null
curl -s -X POST -H "$AUTH" "$GATEWAY/api/notificaciones/dlq/reprocess" | python3 -m json.tool

step "9. Salud agregada del ecosistema"
curl -s "$GATEWAY/health" | python3 -m json.tool

echo; echo "==== Demostracion completada ===="
