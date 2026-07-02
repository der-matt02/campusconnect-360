// Dashboard Directivo: indicadores consolidados (CQRS), salud y resiliencia.
import { useEffect, useState } from "react";
import { api } from "../api";

function Metric({ label, value }) {
  return (
    <div className="metric">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [events, setEvents] = useState([]);
  const [msg, setMsg] = useState(null);

  async function load() {
    try {
      setData(await api.dashboard());
      setStats(await api.notifStats());
      setHealth(await api.health());
      setEvents(await api.recentEvents());
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
      <h2>Dashboard Directivo</h2>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      {data && (
        <div className="grid">
          <Metric label="Estudiantes matriculados" value={data.matriculados} />
          <Metric label="Pagos confirmados" value={data.pagosConfirmados} />
          <Metric label="Pagos pendientes" value={data.pagosPendientes} />
          <Metric label="Monto confirmado" value={`$${data.montoConfirmado}`} />
          <Metric label="Asistencias registradas" value={data.asistencias} />
          <Metric label="Incidentes reportados" value={data.incidentes} />
          <Metric label="Eventos procesados" value={data.eventosProcesados} />
          <Metric label="Notificaciones enviadas" value={stats?.enviadas ?? "-"} />
          <Metric label="Mensajes fallidos (DLQ)" value={stats?.fallidas ?? "-"} />
        </div>
      )}

      <div className="row" style={{ marginTop: "1.25rem" }}>
        <div className="card">
          <h3>Estado del ecosistema</h3>
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
          <h3>Resiliencia (demostracion)</h3>
          <p className="muted">
            Activa el fallo simulado, genera eventos y observa como caen a la DLQ;
            luego reprocesa.
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button className="danger" onClick={() => toggleChaos(true)}>Activar fallo</button>
            <button className="green" onClick={() => toggleChaos(false)}>Desactivar fallo</button>
            <button className="secondary" onClick={reprocess}>Reprocesar DLQ</button>
          </div>
          <p className="muted" style={{ marginTop: "0.75rem" }}>
            Modo de fallo actual:{" "}
            <strong>{stats?.chaos ? "ACTIVADO" : "desactivado"}</strong>
          </p>
        </div>
      </div>

      <div className="card">
        <h3>Eventos recientes (trazabilidad)</h3>
        <table>
          <thead><tr><th>Tipo</th><th>Estudiante</th><th>Correlacion</th><th>Fecha</th></tr></thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.eventId}>
                <td>{e.eventType}</td>
                <td>{e.studentId}</td>
                <td className="muted">{e.correlationId}</td>
                <td className="muted">{new Date(e.occurredAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
