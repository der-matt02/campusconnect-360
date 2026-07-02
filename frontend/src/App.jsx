import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Academico from "./pages/Academico";
import Pagos from "./pages/Pagos";
import Docente from "./pages/Docente";
import Dashboard from "./pages/Dashboard";
import { ROLE_HOME } from "./roles";

// Cada portal exige un rol especifico, en espejo de ROLE_PERMISSIONS
// del Gateway: un usuario autenticado con un rol distinto es redirigido
// a su propio portal en vez de ver el contenido ajeno.
function Protected({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role] || "/login"} replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  const { user } = useAuth();
  const fallback = user ? ROLE_HOME[user.role] || "/login" : "/login";

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/academico" element={<Protected role="academico"><Academico /></Protected>} />
      <Route path="/pagos" element={<Protected role="pagos"><Pagos /></Protected>} />
      <Route path="/docente" element={<Protected role="docente"><Docente /></Protected>} />
      <Route path="/dashboard" element={<Protected role="director"><Dashboard /></Protected>} />
      <Route path="*" element={<Navigate to={fallback} replace />} />
    </Routes>
  );
}
