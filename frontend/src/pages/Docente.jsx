// Portal Docente / Bienestar: registrar asistencia e incidentes.
import { useEffect, useState } from "react";
import { ClipboardList, CalendarCheck, AlertTriangle, Users, History, X } from "lucide-react";
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
      <div className="page-title">
        <span className="page-title-icon">
          <ClipboardList size={20} strokeWidth={2} />
        </span>
        <h2>Portal Docente / Bienestar</h2>
      </div>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="row">
        <div className="card">
          <div className="section-title">
            <CalendarCheck size={17} strokeWidth={2} />
            <h3>Registrar asistencia</h3>
          </div>
          <form onSubmit={registerAtt}>
            <label>Estudiante</label>
            <select value={att.student_id} required onChange={(e) => setAtt({ ...att, student_id: e.target.value })}>
              <option value="">Seleccione un estudiante...</option>
              {students.map(s => <option key={s.id} value={s.id}>{s.full_name} ({s.id})</option>)}
            </select>
            <label>Fecha</label>
            <input value={att.date} onChange={(e) => setAtt({ ...att, date: e.target.value })} />
            <label>Estado</label>
            <select value={att.status} onChange={(e) => setAtt({ ...att, status: e.target.value })}>
              <option>PRESENTE</option><option>AUSENTE</option><option>TARDE</option>
            </select>
            <button type="submit" className="icon-btn">
              <CalendarCheck size={15} strokeWidth={2} />
              Registrar asistencia
            </button>
          </form>
        </div>

        <div className="card">
          <div className="section-title">
            <AlertTriangle size={17} strokeWidth={2} />
            <h3>Registrar incidente / novedad</h3>
          </div>
          <form onSubmit={registerInc}>
            <label>Estudiante</label>
            <select value={inc.student_id} required onChange={(e) => setInc({ ...inc, student_id: e.target.value })}>
              <option value="">Seleccione un estudiante...</option>
              {students.map(s => <option key={s.id} value={s.id}>{s.full_name} ({s.id})</option>)}
            </select>
            <label>Severidad</label>
            <select value={inc.severity} onChange={(e) => setInc({ ...inc, severity: e.target.value })}>
              <option>BAJA</option><option>MEDIA</option><option>ALTA</option>
            </select>
            <label>Descripcion</label>
            <input value={inc.description} required
              onChange={(e) => setInc({ ...inc, description: e.target.value })} />
            <button type="submit" className="icon-btn">
              <AlertTriangle size={15} strokeWidth={2} />
              Registrar incidente
            </button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="section-title">
          <Users size={17} strokeWidth={2} />
          <h3>Estudiantes</h3>
        </div>
        <table>
          <thead><tr><th>ID</th><th>Nombre</th><th>Grado</th><th></th></tr></thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td><td>{s.full_name}</td><td>{s.grade}</td>
                <td>
                  <button className="secondary icon-btn" onClick={() => viewHistory(s.id)}>
                    <History size={14} strokeWidth={2} />
                    Ver historial
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {history && (
        <div className="modal-overlay" onClick={() => setHistory(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setHistory(null)}>
              <X size={20} strokeWidth={2} />
            </button>
            <h3 style={{ marginTop: 0 }}>Historial de {history.id}</h3>
            <h4 className="section-title"><CalendarCheck size={15} strokeWidth={2} />Asistencia</h4>
            <table>
              <thead><tr><th>Fecha</th><th>Estado</th></tr></thead>
              <tbody>
                {history.attendance.map((a) => (
                  <tr key={a.id}><td>{a.date}</td><td>{a.status}</td></tr>
                ))}
              </tbody>
            </table>
            <h4 className="section-title"><AlertTriangle size={15} strokeWidth={2} />Incidentes</h4>
            <table>
              <thead><tr><th>Severidad</th><th>Descripcion</th></tr></thead>
              <tbody>
                {history.incidents.map((i) => (
                  <tr key={i.id}><td>{i.severity}</td><td>{i.description}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
