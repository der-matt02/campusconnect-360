// Barra de navegacion y contenedor comun de los portales.
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const LINKS = [
  { to: "/academico", label: "Portal Academico" },
  { to: "/pagos", label: "Portal Financiero" },
  { to: "/docente", label: "Portal Docente" },
  { to: "/dashboard", label: "Dashboard" },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div>
      <nav className="navbar">
        <span className="brand">CampusConnect 360</span>
        {LINKS.map((l) => (
          <NavLink key={l.to} to={l.to}>
            {l.label}
          </NavLink>
        ))}
        <span className="spacer" />
        <span className="user">
          {user?.name} ({user?.role})
        </span>
        <button className="secondary" onClick={handleLogout}>
          Salir
        </button>
      </nav>
      <div className="container">{children}</div>
    </div>
  );
}
