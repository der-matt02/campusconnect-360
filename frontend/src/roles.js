// Mapeo rol -> portal, en espejo de ROLE_PERMISSIONS del Gateway
// (gateway/app/main.py). Cada rol tiene acceso a un unico portal.
export const ROLE_HOME = {
  academico: "/academico",
  pagos: "/pagos",
  docente: "/docente",
  director: "/dashboard",
};

export const ROLE_LABELS = {
  academico: "Portal Academico",
  pagos: "Portal Financiero",
  docente: "Portal Docente",
  director: "Dashboard Directivo",
};
