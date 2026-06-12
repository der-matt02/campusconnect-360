// Portal Academico / Secretaria: registrar estudiantes, matricular y ver ficha.
import { useEffect, useState } from "react";
import { api } from "../api";

export default function Academico() {
  const [students, setStudents] = useState([]);
  const [detail, setDetail] = useState(null);
  const [msg, setMsg] = useState(null);
  const [form, setForm] = useState({
    full_name: "", document_id: "", email: "", school_id: "SCH-001", grade: "8vo EGB",
  });
  const [period, setPeriod] = useState("2026-1");

  async function load() {
    try {
      setStudents(await api.listStudents());
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }
  useEffect(() => { load(); }, []);

  async function registerStudent(e) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.createStudent(form);
      setMsg({ type: "success", text: "Estudiante registrado." });
      setForm({ ...form, full_name: "", document_id: "", email: "" });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  async function viewDetail(id) {
    setDetail(await api.getStudent(id));
  }

  async function enroll(id) {
    setMsg(null);
    try {
      await api.createEnrollment({ student_id: id, period });
      setMsg({ type: "success", text: `Matricula creada (evento StudentEnrolled publicado).` });
      viewDetail(id);
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  return (
    <div>
      <h2>Portal Academico / Secretaria</h2>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="row">
        <div className="card">
          <h3>Registrar estudiante</h3>
          <form onSubmit={registerStudent}>
            <label>Nombre completo</label>
            <input value={form.full_name} required
              onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <label>Documento</label>
            <input value={form.document_id} required
              onChange={(e) => setForm({ ...form, document_id: e.target.value })} />
            <label>Email</label>
            <input value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <div className="row">
              <div>
                <label>Colegio</label>
                <input value={form.school_id}
                  onChange={(e) => setForm({ ...form, school_id: e.target.value })} />
              </div>
              <div>
                <label>Grado</label>
                <input value={form.grade}
                  onChange={(e) => setForm({ ...form, grade: e.target.value })} />
              </div>
            </div>
            <button type="submit">Registrar</button>
          </form>
        </div>

        <div className="card">
          <h3>Crear matricula</h3>
          <p className="muted">Selecciona un estudiante de la lista y define el periodo.</p>
          <label>Periodo</label>
          <input value={period} onChange={(e) => setPeriod(e.target.value)} />
          <p className="muted">Usa el boton "Matricular" en cada estudiante.</p>
        </div>
      </div>

      <div className="card">
        <h3>Estudiantes</h3>
        <table>
          <thead>
            <tr><th>ID</th><th>Nombre</th><th>Grado</th><th>Estado financiero</th><th></th></tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id}>
                <td>{s.id}</td>
                <td>{s.full_name}</td>
                <td>{s.grade}</td>
                <td>
                  <span className={`badge ${s.financial_status === "AL_DIA" ? "ok" : "warn"}`}>
                    {s.financial_status}
                  </span>
                </td>
                <td>
                  <button className="secondary" onClick={() => viewDetail(s.id)}>Ver ficha</button>{" "}
                  <button className="green" onClick={() => enroll(s.id)}>Matricular</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {detail && (
        <div className="card">
          <h3>Ficha: {detail.full_name}</h3>
          <p className="muted">
            {detail.id} · {detail.grade} · Colegio {detail.school_id} ·
            Estado financiero: <strong>{detail.financial_status}</strong>
          </p>
          <h4>Matriculas</h4>
          <table>
            <thead><tr><th>ID</th><th>Periodo</th><th>Estado</th></tr></thead>
            <tbody>
              {detail.enrollments?.map((en) => (
                <tr key={en.id}><td>{en.id}</td><td>{en.period}</td><td>{en.status}</td></tr>
              ))}
            </tbody>
          </table>
          <h4>Historial de eventos</h4>
          <table>
            <thead><tr><th>Evento</th><th>Resumen</th><th>Correlacion</th></tr></thead>
            <tbody>
              {detail.events?.map((ev, i) => (
                <tr key={i}><td>{ev.event_type}</td><td>{ev.summary}</td><td className="muted">{ev.correlation_id}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
