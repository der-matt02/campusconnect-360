import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  GraduationCap,
  CreditCard,
  ClipboardList,
  LayoutDashboard,
  LogIn,
  School,
  ShieldCheck,
  Activity,
  Radar,
} from "lucide-react";
import { useAuth } from "../auth";
import { ROLE_HOME } from "../roles";

const DEMO_USERS = [
  { u: "secretaria", Icon: GraduationCap, label: "Secretaria", desc: "Portal Academico" },
  { u: "finanzas", Icon: CreditCard, label: "Finanzas", desc: "Portal Financiero" },
  { u: "docente", Icon: ClipboardList, label: "Docente", desc: "Portal Docente / Bienestar" },
  { u: "director", Icon: LayoutDashboard, label: "Direccion", desc: "Dashboard Directivo" },
];

const BRAND_HIGHLIGHTS = [
  { Icon: ShieldCheck, text: "Autenticacion centralizada por rol" },
  { Icon: Activity, text: "Datos en tiempo real entre portales" },
  { Icon: Radar, text: "Trazabilidad completa de eventos" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("secretaria");
  const [password, setPassword] = useState("campus123");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const u = await login(username, password);
      navigate(ROLE_HOME[u.role] || "/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-panel">
        <div className="login-brand">
          <span className="login-brand-logo">
            <School size={22} strokeWidth={2} />
          </span>
          <h1>CampusConnect 360</h1>
          <p>
            Ecosistema integrado para la gestion de una red de colegios:
            academico, pagos, asistencia y analitica en un solo lugar.
          </p>
          <ul className="login-brand-list">
            {BRAND_HIGHLIGHTS.map(({ Icon, text }) => (
              <li key={text}>
                <Icon size={16} strokeWidth={2} />
                {text}
              </li>
            ))}
          </ul>
        </div>

        <div className="login-form-side">
          <h2>Inicia sesion</h2>
          <p className="muted">Selecciona tu perfil para acceder a tu portal.</p>

          <div className="role-picker" role="radiogroup" aria-label="Perfil">
            {DEMO_USERS.map((d) => (
              <button
                type="button"
                key={d.u}
                role="radio"
                aria-checked={username === d.u}
                className={`role-option ${username === d.u ? "active" : ""}`}
                onClick={() => setUsername(d.u)}
              >
                <span className="role-icon">
                  <d.Icon size={18} strokeWidth={2} />
                </span>
                <span className="role-text">
                  <strong>{d.label}</strong>
                  <small>{d.desc}</small>
                </span>
              </button>
            ))}
          </div>

          {error && <div className="alert error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <label htmlFor="password">Contrasena</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Ingresa tu contrasena"
              autoFocus
            />
            <button type="submit" className="login-submit" disabled={loading}>
              {loading ? (
                "Ingresando..."
              ) : (
                <>
                  <LogIn size={17} strokeWidth={2} />
                  Ingresar
                </>
              )}
            </button>
          </form>

          <p className="muted login-hint">
            Entorno de demostracion &middot; contrasena para todos los usuarios:{" "}
            <code>campus123</code>
          </p>
        </div>
      </div>
    </div>
  );
}
