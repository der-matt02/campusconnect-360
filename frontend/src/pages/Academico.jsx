// Portal Academico / Secretaria: registrar estudiantes, matricular y ver ficha.
import { useEffect, useState } from "react";
import { GraduationCap, UserPlus, BookPlus, Users, Eye, BadgeCheck, History, X } from "lucide-react";
import { api } from "../api";

function validateStudentForm(f) {
  const errors = {};
  if (!f.full_name.trim()) errors.full_name = "El nombre completo es obligatorio.";
  if (!f.document_id.trim()) errors.document_id = "El documento es obligatorio.";
  else if (!/^\d{6,15}$/.test(f.document_id.trim())) errors.document_id = "Debe tener entre 6 y 15 digitos numericos.";
  if (f.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) errors.email = "Ingresa un email valido.";
  if (!f.school_id.trim()) errors.school_id = "El colegio es obligatorio.";
  if (!f.grade.trim()) errors.grade = "El grado es obligatorio.";
  return errors;
}

export default function Academico() {
  const [students, setStudents] = useState([]);
  const [detail, setDetail] = useState(null);
  const [msg, setMsg] = useState(null);
  const [form, setForm] = useState({
    full_name: "", document_id: "", email: "", school_id: "SCH-001", grade: "8vo EGB",
  });
  const [errors, setErrors] = useState({});
  const [period, setPeriod] = useState("2026-1");

  async function load() {
    try {
      setStudents(await api.listStudents());
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }
  useEffect(() => { load(); }, []);

  function updateField(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
    setErrors((er) => ({ ...er, [field]: undefined }));
  }

  async function registerStudent(e) {
    e.preventDefault();
    setMsg(null);
    const validation = validateStudentForm(form);
    if (Object.keys(validation).length > 0) {
      setErrors(validation);
      return;
    }
    setErrors({});
    try {
      await api.createStudent(form);
      setMsg({ type: "success", text: `Estudiante "${form.full_name}" registrado correctamente.` });
      setForm({ ...form, full_name: "", document_id: "", email: "" });
      load();
    } catch (e) {
      if (/documento/i.test(e.message)) {
        setErrors({ document_id: e.message });
      } else {
        setMsg({ type: "error", text: e.message });
      }
    }
  }

  async function viewDetail(id) {
    setDetail(await api.getStudent(id));
  }

  function isEnrolledInPeriod(student) {
    return (student.enrollments || []).some((en) => en.period === period);
  }

  async function enroll(id, name) {
    setMsg(null);
    try {
      await api.createEnrollment({ student_id: id, period });
      setMsg({ type: "success", text: `${name} matriculado en el periodo ${period} (evento StudentEnrolled publicado).` });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  return (
    <div>
      <div className="page-title">
        <span className="page-title-icon">
          <GraduationCap size={20} strokeWidth={2} />
        </span>
        <h2>Portal Academico / Secretaria</h2>
      </div>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="row">
        <div className="card">
          <div className="section-title">
            <UserPlus size={17} strokeWidth={2} />
            <h3>Registrar estudiante</h3>
          </div>
          <form onSubmit={registerStudent} noValidate>
            <label>Nombre completo</label>
            <input
              value={form.full_name}
              className={errors.full_name ? "input-error" : ""}
              onChange={(e) => updateField("full_name", e.target.value)}
            />
            {errors.full_name && <p className="field-error">{errors.full_name}</p>}

            <label>Documento</label>
            <input
              value={form.document_id}
              className={errors.document_id ? "input-error" : ""}
              onChange={(e) => updateField("document_id", e.target.value)}
            />
            {errors.document_id && <p className="field-error">{errors.document_id}</p>}

            <label>Email</label>
            <input
              value={form.email}
              className={errors.email ? "input-error" : ""}
              onChange={(e) => updateField("email", e.target.value)}
            />
            {errors.email && <p className="field-error">{errors.email}</p>}

            <div className="row">
              <div>
                <label>Colegio</label>
                <input
                  value={form.school_id}
                  className={errors.school_id ? "input-error" : ""}
                  onChange={(e) => updateField("school_id", e.target.value)}
                />
                {errors.school_id && <p className="field-error">{errors.school_id}</p>}
              </div>
              <div>
                <label>Grado</label>
                <input
                  value={form.grade}
                  className={errors.grade ? "input-error" : ""}
                  onChange={(e) => updateField("grade", e.target.value)}
                />
                {errors.grade && <p className="field-error">{errors.grade}</p>}
              </div>
            </div>
            <button type="submit" className="icon-btn">
              <UserPlus size={15} strokeWidth={2} />
              Registrar
            </button>
          </form>
        </div>

        <div className="card">
          <div className="section-title">
            <BookPlus size={17} strokeWidth={2} />
            <h3>Crear matricula</h3>
          </div>
          <p className="muted">Selecciona un estudiante de la lista y define el periodo.</p>
          <label>Periodo</label>
          <input value={period} onChange={(e) => setPeriod(e.target.value)} />
          <p className="muted">Usa el boton "Matricular" en cada estudiante.</p>
        </div>
      </div>

      <div className="card">
        <div className="section-title">
          <Users size={17} strokeWidth={2} />
          <h3>Estudiantes</h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Nombre</th><th>Grado</th><th>Estado financiero</th>
              <th>Matricula ({period || "-"})</th><th></th>
            </tr>
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
                  <span className={`badge icon-btn ${isEnrolledInPeriod(s) ? "ok" : "warn"}`}>
                    <BadgeCheck size={13} strokeWidth={2} />
                    {isEnrolledInPeriod(s) ? "Matriculado" : "No matriculado"}
                  </span>
                </td>
                <td>
                  <button className="secondary icon-btn" onClick={() => viewDetail(s.id)}>
                    <Eye size={14} strokeWidth={2} />
                    Ver ficha
                  </button>{" "}
                  {!isEnrolledInPeriod(s) && (
                    <button className="green icon-btn" onClick={() => enroll(s.id, s.full_name)}>
                      <BadgeCheck size={14} strokeWidth={2} />
                      Matricular
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {detail && (
        <div className="modal-overlay" onClick={() => setDetail(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setDetail(null)}>
              <X size={20} strokeWidth={2} />
            </button>
            <h3 style={{ marginTop: 0 }}>Ficha: {detail.full_name}</h3>
            <p className="muted">
              {detail.id} · {detail.grade} · Colegio {detail.school_id} <br/>
              Estado financiero: <span className={`badge ${detail.financial_status === "AL_DIA" ? "ok" : "warn"}`}>{detail.financial_status}</span>
            </p>
            <h4 className="section-title"><BookPlus size={15} strokeWidth={2} />Matriculas</h4>
            <table>
              <thead><tr><th>ID</th><th>Periodo</th><th>Estado</th></tr></thead>
              <tbody>
                {detail.enrollments?.map((en) => (
                  <tr key={en.id}><td>{en.id}</td><td>{en.period}</td><td>{en.status}</td></tr>
                ))}
              </tbody>
            </table>
            <h4 className="section-title"><History size={15} strokeWidth={2} />Historial de eventos</h4>
            <table>
              <thead><tr><th>Evento</th><th>Resumen</th><th>Correlacion</th></tr></thead>
              <tbody>
                {detail.events?.map((ev, i) => (
                  <tr key={i}><td>{ev.event_type}</td><td>{ev.summary}</td><td className="muted">{ev.correlation_id}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
