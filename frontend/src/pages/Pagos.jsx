// Portal Financiero / Pagos: consultar deudas, registrar y confirmar pagos.
import { useEffect, useState } from "react";
import { Wallet, Users, FilePlus, Receipt, CheckCircle2 } from "lucide-react";
import { api } from "../api";

export default function Pagos() {
  const [students, setStudents] = useState([]);
  const [payments, setPayments] = useState([]);
  const [filter, setFilter] = useState("");
  const [msg, setMsg] = useState(null);
  const [debt, setDebt] = useState({ student_id: "", concept: "", amount: 100 });

  async function load() {
    try {
      setStudents(await api.pagosStudents());
      setPayments(await api.payments(filter));
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }
  useEffect(() => { load(); }, [filter]);

  async function confirm(id) {
    setMsg(null);
    try {
      await api.confirmPayment(id);
      setMsg({ type: "success", text: "Pago confirmado (evento PaymentConfirmed publicado)." });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  async function createDebt(e) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.createDebt({ ...debt, amount: Number(debt.amount) });
      setMsg({ type: "success", text: "Obligacion de pago registrada." });
      load();
    } catch (e) {
      setMsg({ type: "error", text: e.message });
    }
  }

  return (
    <div>
      <div className="page-title">
        <span className="page-title-icon">
          <Wallet size={20} strokeWidth={2} />
        </span>
        <h2>Portal Financiero / Pagos</h2>
      </div>
      {msg && <div className={`alert ${msg.type}`}>{msg.text}</div>}

      <div className="row">
        <div className="card">
          <div className="section-title">
            <Users size={17} strokeWidth={2} />
            <h3>Estudiantes matriculados</h3>
          </div>
          <table>
            <thead><tr><th>ID</th><th>Nombre</th><th>Pagos</th></tr></thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.full_name}</td>
                  <td>{s.payments?.length || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="section-title">
            <FilePlus size={17} strokeWidth={2} />
            <h3>Registrar deuda / simular obligacion</h3>
          </div>
          <form onSubmit={createDebt}>
            <label>Estudiante</label>
            <select value={debt.student_id} required onChange={(e) => setDebt({ ...debt, student_id: e.target.value })}>
              <option value="">Seleccione un estudiante...</option>
              {students.map(s => <option key={s.id} value={s.id}>{s.full_name} ({s.id})</option>)}
            </select>
            <label>Concepto</label>
            <input value={debt.concept} required maxLength={150}
              onChange={(e) => setDebt({ ...debt, concept: e.target.value })} />
            <label>Monto</label>
            <input type="number" value={debt.amount}
              onChange={(e) => setDebt({ ...debt, amount: e.target.value })} />
            <button type="submit" className="icon-btn">
              <FilePlus size={15} strokeWidth={2} />
              Registrar deuda
            </button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="section-title">
          <Receipt size={17} strokeWidth={2} />
          <h3>Pagos</h3>
        </div>
        <label>Filtrar por estado</label>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ maxWidth: 240 }}>
          <option value="">Todos</option>
          <option value="PENDIENTE">Pendientes</option>
          <option value="CONFIRMADO">Confirmados</option>
        </select>
        <table style={{ marginTop: "1rem" }}>
          <thead>
            <tr><th>ID Pago</th><th>Nombre Estudiante</th><th>ID Estudiante</th><th>Concepto</th><th>Monto</th><th>Estado</th><th></th></tr>
          </thead>
          <tbody>
            {payments.map((p) => {
              const student = students.find((s) => s.id === p.student_id);
              return (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{student ? student.full_name : "Desconocido"}</td>
                  <td>{p.student_id}</td>
                  <td>{p.concept}</td>
                  <td>${p.amount}</td>
                  <td>
                    <span className={`badge ${p.status === "CONFIRMADO" ? "ok" : "warn"}`}>{p.status}</span>
                  </td>
                  <td>
                    {p.status === "PENDIENTE" && (
                      <button className="green icon-btn" onClick={() => confirm(p.id)}>
                        <CheckCircle2 size={14} strokeWidth={2} />
                        Confirmar pago
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
