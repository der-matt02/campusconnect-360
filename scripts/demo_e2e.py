#!/usr/bin/env python3
"""
CampusConnect 360 — Demostración automática "un día de operación" (E2E) en Python.
Ejecuta el flujo completo a través del API Gateway con JWT y realiza validaciones.
Multiplataforma: Funciona en Windows, macOS y Linux sin requerir dependencias externas.
"""
import json
import sys
import time
import urllib.error
import urllib.request

GATEWAY = "http://localhost:8000"

def request_json(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}

    req_headers = {"Content-Type": "application/json"}
    req_headers.update(headers)

    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            resp_body = response.read().decode("utf-8")
            if resp_body:
                return status, json.loads(resp_body)
            return status, {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        err_msg = f"HTTP Error {e.code}: {e.reason}"
        if resp_body:
            try:
                err_json = json.loads(resp_body)
                err_msg += f" - {err_json}"
            except Exception:
                err_msg += f" - {resp_body}"
        print(f"Error en petición a {url}: {err_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"Error de conexión a {url}: {e}")
        sys.exit(1)

def login(username):
    url = f"{GATEWAY}/auth/login"
    status, body = request_json(url, "POST", {"username": username, "password": "campus123"})
    assert status == 200, "Error en login"
    return body["access_token"]

def print_step(title):
    print("\n" + "=" * 60)
    print(f" PASO: {title}")
    print("=" * 60)

def main():
    print("Verificando que el API Gateway esté corriendo...")
    try:
        urllib.request.urlopen(f"{GATEWAY}/health", timeout=3)
    except Exception as e:
        print(f"Error: El Gateway en {GATEWAY} no está accesible. ¿Docker Compose está corriendo?")
        print(e)
        sys.exit(1)

    # ----------------------------------------------------
    print_step("0. Obtención de tokens por actor (Autenticación JWT)")
    # ----------------------------------------------------
    token_sec = login("secretaria")
    token_fin = login("finanzas")
    token_doc = login("docente")
    token_dir = login("director")

    auth_sec = {"Authorization": f"Bearer {token_sec}"}
    auth_fin = {"Authorization": f"Bearer {token_fin}"}
    auth_doc = {"Authorization": f"Bearer {token_doc}"}
    auth_dir = {"Authorization": f"Bearer {token_dir}"}
    print("✓ Tokens obtenidos exitosamente para todos los roles.")

    # ----------------------------------------------------
    print_step("1. Secretaría registra un nuevo estudiante")
    # ----------------------------------------------------
    student_payload = {
        "full_name": "Estudiante E2E Python",
        "document_id": "1700PYTHON01",
        "email": "python_e2e@example.edu",
        "school_id": "SCH-001",
        "grade": "8vo EGB"
    }
    status, student = request_json(f"{GATEWAY}/api/academico/students", "POST", student_payload, auth_sec)
    assert status == 201, "Error al registrar estudiante"
    student_id = student["id"]
    print(f"✓ Estudiante registrado exitosamente. ID: {student_id}")

    # ----------------------------------------------------
    print_step("2. Secretaría crea la matrícula -> Publica StudentEnrolled")
    # ----------------------------------------------------
    enrollment_payload = {
        "student_id": student_id,
        "period": "2026-1"
    }
    status, _ = request_json(f"{GATEWAY}/api/academico/enrollments", "POST", enrollment_payload, auth_sec)
    assert status == 201, "Error al matricular estudiante"
    print("✓ Matrícula creada. Esperando 3 segundos para la propagación de eventos...")
    time.sleep(3)

    # ----------------------------------------------------
    print_step("3. Finanzas confirma el pago de matrícula -> Publica PaymentConfirmed")
    # ----------------------------------------------------
    # Buscar el ID del pago autogenerado para el estudiante
    status, financial_info = request_json(f"{GATEWAY}/api/pagos/students/{student_id}", "GET", headers=auth_fin)
    assert status == 200, "Error al buscar ficha financiera"
    payments = financial_info.get("payments", [])
    assert len(payments) > 0, "No se generó el pago correspondiente"
    payment_id = payments[0]["id"]
    print(f"✓ Deuda autodetectada. ID de Pago: {payment_id}. Confirmando pago...")

    status, _ = request_json(f"{GATEWAY}/api/pagos/payments/{payment_id}/confirm", "POST", headers=auth_fin)
    assert status == 200, "Error al confirmar el pago"
    print("✓ Pago confirmado. Esperando 3 segundos para la propagación del estado...")
    time.sleep(3)

    # ----------------------------------------------------
    print_step("4. Secretaría verifica el estado financiero actualizado")
    # ----------------------------------------------------
    status, student_info = request_json(f"{GATEWAY}/api/academico/students/{student_id}", "GET", headers=auth_sec)
    assert status == 200, "Error al obtener ficha académica"
    financial_status = student_info.get("financial_status")
    print(f"✓ Estado financiero del alumno: {financial_status}")
    assert financial_status == "AL_DIA", "El estado financiero no se actualizó a AL_DIA"

    # ----------------------------------------------------
    print_step("5. Docente registra asistencia e incidente")
    # ----------------------------------------------------
    attendance_payload = {
        "student_id": student_id,
        "date": "2026-06-12",
        "status": "PRESENTE"
    }
    status, _ = request_json(f"{GATEWAY}/api/asistencia/attendance", "POST", attendance_payload, auth_doc)
    assert status == 201, "Error al registrar asistencia"

    incident_payload = {
        "student_id": student_id,
        "severity": "BAJA",
        "description": "Prueba de integración en Python"
    }
    status, _ = request_json(f"{GATEWAY}/api/asistencia/incidents", "POST", incident_payload, auth_doc)
    assert status == 201, "Error al registrar incidente"
    print("✓ Asistencia e incidente registrados de forma segura.")
    time.sleep(2)

    # ----------------------------------------------------
    print_step("6. Dashboard directivo (Lectura consolidada CQRS)")
    # ----------------------------------------------------
    status, dashboard = request_json(f"{GATEWAY}/api/analitica/dashboard", "GET", headers=auth_dir)
    assert status == 200, "Error al leer dashboard directivo"
    print(json.dumps(dashboard, indent=2, ensure_ascii=False))

    # ----------------------------------------------------
    print_step("7. Escenario de falla: Activar chaos, generar evento -> DLQ")
    # ----------------------------------------------------
    # Activar modo Caos en Notificaciones
    status, _ = request_json(f"{GATEWAY}/api/notificaciones/chaos", "POST", {"enabled": True}, auth_dir)
    assert status == 200, "Error al activar el modo caos"
    print("✓ Modo Caos activado en el servicio de Notificaciones.")

    # El docente genera una nueva asistencia para forzar un fallo al notificar
    attendance_payload_fail = {
        "student_id": student_id,
        "date": "2026-06-13",
        "status": "AUSENTE"
    }
    status, _ = request_json(f"{GATEWAY}/api/asistencia/attendance", "POST", attendance_payload_fail, auth_doc)
    assert status == 201
    print("✓ Nueva asistencia generada bajo fallo simulado.")
    print("Esperando 9 segundos para que se completen los 3 reintentos y el evento caiga en la DLQ...")
    time.sleep(9)

    # Comprobar la profundidad de la DLQ
    status, dlq_info = request_json(f"{GATEWAY}/api/notificaciones/dlq", "GET", headers=auth_dir)
    assert status == 200
    dlq_depth = dlq_info.get("dlqDepth", 0)
    print(f"✓ Mensajes acumulados en la Dead Letter Queue (DLQ): {dlq_depth}")
    assert dlq_depth >= 1, "La DLQ debería tener al menos 1 mensaje fallido"

    # ----------------------------------------------------
    print_step("8. Recuperación: Desactivar caos y reprocesar la DLQ")
    # ----------------------------------------------------
    # Desactivar modo caos
    status, _ = request_json(f"{GATEWAY}/api/notificaciones/chaos", "POST", {"enabled": False}, auth_dir)
    assert status == 200, "Error al desactivar el modo caos"
    print("✓ Modo Caos desactivado.")

    # Lanzar el reprocesamiento manual de la DLQ
    status, reprocess_result = request_json(f"{GATEWAY}/api/notificaciones/dlq/reprocess", "POST", headers=auth_dir)
    assert status == 200, "Error al reprocesar DLQ"
    print("✓ Petición de reprocesamiento completada:")
    print(json.dumps(reprocess_result, indent=2, ensure_ascii=False))

    # Comprobar que la DLQ se vació
    status, dlq_info_after = request_json(f"{GATEWAY}/api/notificaciones/dlq", "GET", headers=auth_dir)
    assert status == 200
    assert dlq_info_after.get("dlqDepth", 0) == 0, "La DLQ debería haberse vaciado tras el reprocesamiento"
    print("✓ DLQ vaciada con éxito tras el reprocesamiento manual (Resiliencia confirmada).")

    # ----------------------------------------------------
    print_step("9. Salud agregada del ecosistema (Health Checks)")
    # ----------------------------------------------------
    status, health = request_json(f"{GATEWAY}/health", "GET")
    assert status == 200
    print(json.dumps(health, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print(" ✓✓ DEMOSTRACIÓN COMPLETADA Y VERIFICADA EXITOSAMENTE ✓✓")
    print("=" * 60)

if __name__ == "__main__":
    main()
