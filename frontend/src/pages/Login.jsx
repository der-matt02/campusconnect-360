import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const DEMO_USERS = [
  { u: "secretaria", label: "Secretaria (Academico)" },
  { u: "finanzas", label: "Finanzas (Pagos)" },
  { u: "docente", label: "Docente (Bienestar)" },
  { u: "director", label: "Direccion (Dashboard)" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("secretaria");
  const [password, setPassword] = useState("campus123");
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="login-wrap">
      <div className="card login-box">
        <h2 style={{ color: "var(--naranja)" }}>CampusConnect 360</h2>
        <p className="muted">Inicia sesion para acceder al ecosistema.</p>
        {error && <div className="alert error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label>Usuario</label>
          <select value={username} onChange={(e) => setUsername(e.target.value)}>
            {DEMO_USERS.map((d) => (
              <option key={d.u} value={d.u}>
                {d.label}
              </option>
            ))}
          </select>
          <label>Contrasena</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit">Ingresar</button>
        </form>
        <p className="muted" style={{ marginTop: "1rem" }}>
          Usuarios de prueba: secretaria / finanzas / docente / director.
          Contrasena: <code>campus123</code>
        </p>
      </div>
    </div>
  );
}
