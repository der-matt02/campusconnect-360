// Barra de navegacion y contenedor comun de los portales.
import { useNavigate } from "react-router-dom";
import { School, LogOut } from "lucide-react";
import { useAuth } from "../auth";
import { ROLE_LABELS } from "../roles";

function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
}

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
        <span className="brand">
          <span className="brand-mark">
            <School size={16} strokeWidth={2} />
          </span>
          CampusConnect 360
        </span>
        {/* Cada rol solo tiene acceso a su propio portal (ver ROLE_PERMISSIONS
            en el Gateway), asi que se muestra como una etiqueta fija en vez
            de un menu de navegacion con links a portales ajenos. */}
        <span className="portal-badge">{ROLE_LABELS[user?.role] || user?.role}</span>
        <span className="spacer" />
        <span className="user-chip">
          <span className="avatar">{initials(user?.name)}</span>
          <span className="user-info">
            <strong>{user?.name}</strong>
            <small>{ROLE_LABELS[user?.role] || user?.role}</small>
          </span>
        </span>
        <button className="secondary icon-btn" onClick={handleLogout}>
          <LogOut size={15} strokeWidth={2} />
          Salir
        </button>
      </nav>
      <div className="container">{children}</div>
    </div>
  );
}
