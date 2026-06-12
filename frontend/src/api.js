// Cliente del API Gateway. Adjunta el JWT a cada peticion protegida.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && getToken()) {
    headers["Authorization"] = `Bearer ${getToken()}`;
  }
  const resp = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.detail || `Error ${resp.status}`);
  }
  return data;
}

export const api = {
  login: (username, password) =>
    request("/auth/login", { method: "POST", body: { username, password }, auth: false }),

  // Servicio Academico
  listStudents: () => request("/api/academico/students"),
  getStudent: (id) => request(`/api/academico/students/${id}`),
  createStudent: (data) => request("/api/academico/students", { method: "POST", body: data }),
  createEnrollment: (data) => request("/api/academico/enrollments", { method: "POST", body: data }),
  studentEvents: (id) => request(`/api/academico/students/${id}/events`),

  // Servicio Pagos
  pagosStudents: () => request("/api/pagos/students"),
  payments: (status) => request(`/api/pagos/payments${status ? `?status=${status}` : ""}`),
  createDebt: (data) => request("/api/pagos/debts", { method: "POST", body: data }),
  confirmPayment: (id) => request(`/api/pagos/payments/${id}/confirm`, { method: "POST" }),

  // Servicio Asistencia
  asistenciaStudents: () => request("/api/asistencia/students"),
  registerAttendance: (data) => request("/api/asistencia/attendance", { method: "POST", body: data }),
  registerIncident: (data) => request("/api/asistencia/incidents", { method: "POST", body: data }),
  studentAttendance: (id) => request(`/api/asistencia/students/${id}/attendance`),
  studentIncidents: (id) => request(`/api/asistencia/students/${id}/incidents`),

  // Servicio Analitica
  dashboard: () => request("/api/analitica/dashboard"),
  recentEvents: () => request("/api/analitica/events"),

  // Servicio Notificaciones
  notifications: () => request("/api/notificaciones/notifications"),
  notifStats: () => request("/api/notificaciones/stats"),
  setChaos: (enabled) => request("/api/notificaciones/chaos", { method: "POST", body: { enabled } }),
  reprocessDlq: () => request("/api/notificaciones/dlq/reprocess", { method: "POST" }),

  // Health agregado
  health: () => request("/health", { auth: false }),
};
