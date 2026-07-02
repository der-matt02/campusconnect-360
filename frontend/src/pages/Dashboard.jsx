// Dashboard Directivo: indicadores consolidados (CQRS), salud y resiliencia.
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Users,
  CheckCircle2,
  Clock,
  DollarSign,
  CalendarCheck,
  AlertTriangle,
  Activity,
  Bell,
  MailWarning,
  HeartPulse,
  ShieldAlert,
  History,
  Zap,
  ShieldCheck,
  RotateCw,
} from "lucide-react";
import { api } from "../api";

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="metric">
      <div className="metric-head">
        <Icon size={15} strokeWidth={2} />
        {label}
      </div>
      <div className="value">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [events, setEvents] = useState([]);
  const [students, setStudents] = useState([]);
  const [msg, setMsg] = useState(null);

  async function load() {
    try {
      setData(await api.dashboard());
      setStats(await api.notifStats());
      setHealth(await api.health());
      setEvents(await api.recentEvents());
      try {
        setStudents(await api.listStudents());
      } catch (err) {
        console.warn("No se pudo cargar estudiantes en dashboard:", err);
      }
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 5000); // refresco automatico
    return () => clearInterval(id);
  }, []);

  async function toggleChaos(enabled) {
    setMsg(null);
    try {
      await api.setChaos(enabled);
      setMsg({ type: "success", text: `Modo de fallo ${enabled ? "ACTIVADO" : "DESACTIVADO"}.` });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  async function reprocess() {
    setMsg(null);
    try {
      const r = await api.reprocessDlq();
      setMsg({ type: "success", text: `Reprocesados: ${r.reprocessed}, aun fallidos: ${r.still_failed}.` });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  return (
    <div>
      <div className="page-title">
        <span className="page-title-icon">
          <LayoutDashboard size={20} strokeWidth={2} />
        </span>
        <h2>Dashboard Directivo</h2>
      </div>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {data && (
        <div className="grid">
          <Metric icon={Users} label="Estudiantes matriculados" value={data.matriculados} />
          <Metric icon={CheckCircle2} label="Pagos confirmados" value={data.pagosConfirmados} />
          <Metric icon={Clock} label="Pagos pendientes" value={data.pagosPendientes} />
          <Metric icon={DollarSign} label="Monto confirmado" value={`$${data.montoConfirmado}`} />
          <Metric icon={CalendarCheck} label="Asistencias registradas" value={data.asistencias} />
          <Metric icon={AlertTriangle} label="Incidentes reportados" value={data.incidentes} />
          <Metric icon={Activity} label="Eventos procesados" value={data.eventosProcesados} />
          <Metric icon={Bell} label="Notificaciones enviadas" value={stats?.enviadas ?? "-"} />
          <Metric icon={MailWarning} label="Mensajes fallidos (DLQ)" value={stats?.fallidas ?? "-"} />
        </div>
      )}

      <div className="row" style={{ marginTop: "1.25rem" }}>
        <div className="card">
          <div className="section-title">
            <HeartPulse size={17} strokeWidth={2} />
            <h3>Estado del ecosistema</h3>
          </div>
          {health && (
            <table>
              <tbody>
                <tr>
                  <td>Gateway</td>
                  <td><span className="badge ok">{health.gateway}</span></td>
                </tr>
                {Object.entries(health.services ?? {}).map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ textTransform: "capitalize" }}>{k}</td>
                    <td>
                      <span className={`badge ${v === "ok" ? "ok" : "bad"}`}>{v}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <div className="section-title">
            <ShieldAlert size={17} strokeWidth={2} />
            <h3>Resiliencia (demostracion)</h3>
          </div>
          <p className="muted">
            Activa el fallo simulado, genera eventos y observa como caen a la DLQ;
            luego reprocesa.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button className="danger icon-btn" onClick={() => toggleChaos(true)}>
              <Zap size={14} strokeWidth={2} />
              Activar fallo
            </button>
            <button className="green icon-btn" onClick={() => toggleChaos(false)}>
              <ShieldCheck size={14} strokeWidth={2} />
              Desactivar fallo
            </button>
            <button className="secondary icon-btn" onClick={reprocess}>
              <RotateCw size={14} strokeWidth={2} />
              Reprocesar DLQ
            </button>
          </div>
          <p className="muted" style={{ marginTop: "0.75rem" }}>
            Modo de fallo actual:{" "}
            <strong>{stats?.chaos ? "ACTIVADO" : "desactivado"}</strong>
          </p>
        </div>
      </div>

      <div className="card">
        <div className="section-title">
          <History size={17} strokeWidth={2} />
          <h3>Eventos recientes (trazabilidad)</h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Nombre del estudiante</th>
              <th>ID Estudiante</th>
              <th>Correlacion</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => {
              const student = students.find((s) => s.id === e.studentId);
              return (
                <tr key={e.eventId}>
                  <td>{e.eventType}</td>
                  <td>{student ? student.full_name : "Desconocido"}</td>
                  <td>{e.studentId || "-"}</td>
                  <td className="muted">{e.correlationId}</td>
                  <td className="muted">{new Date(e.occurredAt).toLocaleString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
