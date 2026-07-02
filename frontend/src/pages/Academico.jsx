// Portal Academico / Secretaria: registrar estudiantes, matricular y ver ficha.
import { useEffect, useState } from "react";
import { GraduationCap, UserPlus, BookPlus, Users, Eye, BadgeCheck, History, X } from "lucide-react";
import { api } from "../api";

function validateStudentForm(f) {
  const errors = {};
  if (!f.full_name.trim()) {
    errors.full_name = "El nombre completo es obligatorio.";
  } else if (f.full_name.trim().length > 100) {
    errors.full_name = "El nombre completo no puede exceder los 100 caracteres.";
  }

  if (!f.document_id.trim()) {
    errors.document_id = "El documento es obligatorio.";
  } else if (!/^\d{6,15}$/.test(f.document_id.trim())) {
    errors.document_id = "Debe tener entre 6 y 15 digitos numericos.";
  }

  if (f.email.trim()) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) {
      errors.email = "Ingresa un email valido.";
    } else if (f.email.trim().length > 100) {
      errors.email = "El email no puede exceder los 100 caracteres.";
    }
  }

  if (!f.school_id.trim()) {
    errors.school_id = "El colegio es obligatorio.";
  } else if (f.school_id.trim().length > 50) {
    errors.school_id = "El ID del colegio no puede exceder los 50 caracteres.";
  }

  if (!f.grade.trim()) {
    errors.grade = "El grado es obligatorio.";
  } else if (f.grade.trim().length > 50) {
    errors.grade = "El grado no puede exceder los 50 caracteres.";
  }

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

  // Catalogo de periodos que persiste en localStorage
  const [periods, setPeriods] = useState(() => {
    const saved = localStorage.getItem("cc_periods");
    return saved ? JSON.parse(saved) : ["2026-1", "2026-2"];
  });
  const [period, setPeriod] = useState(periods[0] || "2026-1");
  const [newPeriod, setNewPeriod] = useState("");
  const [initialPeriod, setInitialPeriod] = useState("");

  useEffect(() => {
    localStorage.setItem("cc_periods", JSON.stringify(periods));
  }, [periods]);

  function addPeriod() {
    setMsg(null);
    const val = newPeriod.trim();
    if (!val) return;
    if (periods.includes(val)) {
      setMsg({ type: "error", text: `El periodo "${val}" ya existe en el catalogo.` });
      return;
    }
    setPeriods([...periods, val]);
    setNewPeriod("");
  }

  function removePeriod(p) {
    setMsg(null);
    if (periods.length <= 1) return;
    const filtered = periods.filter((item) => item !== p);
    setPeriods(filtered);
    if (period === p) {
      setPeriod(filtered[0] || "");
    }
    if (initialPeriod === p) {
      setInitialPeriod("");
    }
  }

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
      const student = await api.createStudent(form);
      let enrollMsg = "";
      if (initialPeriod) {
        await api.createEnrollment({ student_id: student.id, period: initialPeriod });
        enrollMsg = ` y matriculado en el periodo ${initialPeriod} (evento StudentEnrolled publicado)`;
      }
      setMsg({ type: "success", text: `Estudiante "${form.full_name}" registrado correctamente${enrollMsg}.` });
      setForm({ ...form, full_name: "", document_id: "", email: "" });
      setInitialPeriod("");
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
              maxLength={100}
              onChange={(e) => updateField("full_name", e.target.value)}
            />
            {errors.full_name && <p className="field-error">{errors.full_name}</p>}

            <label>Documento</label>
            <input
              value={form.document_id}
              className={errors.document_id ? "input-error" : ""}
              maxLength={15}
              onChange={(e) => updateField("document_id", e.target.value)}
            />
            {errors.document_id && <p className="field-error">{errors.document_id}</p>}

            <label>Email</label>
            <input
              value={form.email}
              className={errors.email ? "input-error" : ""}
              maxLength={100}
              onChange={(e) => updateField("email", e.target.value)}
            />
            {errors.email && <p className="field-error">{errors.email}</p>}

            <div className="row">
              <div>
                <label>Colegio</label>
                <input
                  value={form.school_id}
                  className={errors.school_id ? "input-error" : ""}
                  maxLength={50}
                  onChange={(e) => updateField("school_id", e.target.value)}
                />
                {errors.school_id && <p className="field-error">{errors.school_id}</p>}
              </div>
              <div>
                <label>Grado</label>
                <input
                  value={form.grade}
                  className={errors.grade ? "input-error" : ""}
                  maxLength={50}
                  onChange={(e) => updateField("grade", e.target.value)}
                />
                {errors.grade && <p className="field-error">{errors.grade}</p>}
              </div>
            </div>

            <label>Matricula Inicial (Opcional)</label>
            <select
              value={initialPeriod}
              onChange={(e) => setInitialPeriod(e.target.value)}
              style={{ marginBottom: "1rem" }}
            >
              <option value="">Ninguna (Solo registrar)</option>
              {periods.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>

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
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            {periods.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <p className="muted" style={{ marginTop: "0.75rem" }}>Usa el boton "Matricular" en cada estudiante.</p>
        </div>

        <div className="card">
          <div className="section-title">
            <GraduationCap size={17} strokeWidth={2} />
            <h3>Catalogo de periodos</h3>
          </div>
          <p className="muted">Gestiona los periodos escolares validos para matricula.</p>
          
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
            <input 
              value={newPeriod} 
              placeholder="Ej: 2026-2" 
              maxLength={20}
              onChange={(e) => setNewPeriod(e.target.value)} 
            />
            <button 
              type="button" 
              onClick={addPeriod}
              style={{ marginTop: 0 }}
            >
              Agregar
            </button>
          </div>

          <div style={{ marginTop: "1rem" }}>
            <label>Periodos activos</label>
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {periods.map((p) => (
                <li key={p} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.4rem 0", borderBottom: "1px solid var(--borde)" }}>
                  <span>{p}</span>
                  {periods.length > 1 && (
                    <button 
                      className="danger icon-btn" 
                      style={{ padding: "0.2rem 0.5rem", fontSize: "0.75rem", marginTop: 0 }}
                      onClick={() => removePeriod(p)}
                    >
                      Eliminar
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
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
