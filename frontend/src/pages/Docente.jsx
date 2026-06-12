// Portal Docente / Bienestar: registrar asistencia e incidentes.
import { useEffect, useState } from "react";
import { api } from "../api";

export default function Docente() {
  const [students, setStudents] = useState([]);
  const [msg, setMsg] = useState(null);
  const [history, setHistory] = useState(null);
  const [att, setAtt] = useState({ student_id: "", date: "2026-06-12", status: "PRESENTE" });
  const [inc, setInc] = useState({ student_id: "", severity: "BAJA", description: "" });

  async function load() {
    try {
      setStudents(await api.asistenciaStudents());
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }
  useEffect(() => { load(); }, []);

  async function registerAtt(e) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.registerAttendance(att);
      setMsg({ type: "success", text: "Asistencia registrada (evento AttendanceRecorded)." });
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  async function registerInc(e) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.registerIncident(inc);
      setMsg({ type: "success", text: "Incidente registrado (evento IncidentReported)." });
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  async function viewHistory(id) {
    const attendance = await api.studentAttendance(id);
    const incidents = await api.studentIncidents(id);
    setHistory({ id, attendance, incidents });
  }

  return (
    <div>
      <h2>Portal Docente / Bienestar</h2>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="row">
        <div className="card">
          <h3>Registrar asistencia</h3>
          <form onSubmit={registerAtt}>
            <label>ID del estudiante</label>
            <input value={att.student_id} required
              onChange={(e) => setAtt({ ...att, student_id: e.target.value })} />
            <label>Fecha</label>
            <input value={att.date} onChange={(e) => setAtt({ ...att, date: e.target.value })} />
            <label>Estado</label>
            <select value={att.status} onChange={(e) => setAtt({ ...att, status: e.target.value })}>
              <option>PRESENTE</option><option>AUSENTE</option><option>TARDE</option>
            </select>
            <button type="submit">Registrar asistencia</button>
          </form>
        </div>

        <div className="card">
          <h3>Registrar incidente / novedad</h3>
          <form onSubmit={registerInc}>
            <label>ID del estudiante</label>
            <input value={inc.student_id} required
              onChange={(e) => setInc({ ...inc, student_id: e.target.value })} />
            <label>Severidad</label>
            <select value={inc.severity} onChange={(e) => setInc({ ...inc, severity: e.target.value })}>
              <option>BAJA</option><option>MEDIA</option><option>ALTA</option>
            </select>
            <label>Descripcion</label>
            <input value={inc.description} required
              onChange={(e) => setInc({ ...inc, description: e.target.value })} />
            <button type="submit">Registrar incidente</button>
          </form>
        </div>
      </div>

      <div className="card">
        <h3>Estudiantes</h3>
        <table>
          <thead><tr><th>ID</th><th>Nombre</th><th>Grado</th><th></th></tr></thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td><td>{s.full_name}</td><td>{s.grade}</td>
                <td><button className="secondary" onClick={() => viewHistory(s.id)}>Ver historial</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {history && (
        <div className="card">
          <h3>Historial de {history.id}</h3>
          <h4>Asistencia</h4>
          <table>
            <thead><tr><th>Fecha</th><th>Estado</th></tr></thead>
            <tbody>
              {history.attendance.map((a) => (
                <tr key={a.id}><td>{a.date}</td><td>{a.status}</td></tr>
              ))}
            </tbody>
          </table>
          <h4>Incidentes</h4>
          <table>
            <thead><tr><th>Severidad</th><th>Descripcion</th></tr></thead>
            <tbody>
              {history.incidents.map((i) => (
                <tr key={i.id}><td>{i.severity}</td><td>{i.description}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
