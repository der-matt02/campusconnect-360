// Cliente del API Gateway. Adjunta el JWT a cada peticion protegida.
// En producción (Docker + Nginx) se deja vacío: Nginx actúa como reverse proxy
// y enruta /api/* y /auth/* al Gateway internamente (mismo origen, sin CORS).
// En desarrollo local con Vite, definir VITE_API_URL=http://localhost:8000 en .env
const API_URL = import.meta.env.VITE_API_URL || "";

function getToken() {
  return localStorage.getItem("token");
}

/**
 * Realiza una petición HTTP al API Gateway, adjuntando opcionalmente el token JWT.
 * @param {string} path - Ruta de la API (ej. /auth/login)
 * @param {Object} options - Opciones de la petición
 * @param {string} [options.method="GET"] - Método HTTP
 * @param {Object} [options.body] - Cuerpo de la petición (se serializa a JSON)
 * @param {boolean} [options.auth=true] - Si es true, adjunta el token JWT
 * @returns {Promise<any>} Datos JSON de la respuesta
 * @throws {Error} Si la respuesta no es OK
 */
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

/**
 * Objeto central que expone todos los endpoints del backend de CampusConnect 360.
 */
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
