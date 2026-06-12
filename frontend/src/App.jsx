import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Academico from "./pages/Academico";
import Pagos from "./pages/Pagos";
import Docente from "./pages/Docente";
import Dashboard from "./pages/Dashboard";

function Protected({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/academico" element={<Protected><Academico /></Protected>} />
      <Route path="/pagos" element={<Protected><Pagos /></Protected>} />
      <Route path="/docente" element={<Protected><Docente /></Protected>} />
      <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
