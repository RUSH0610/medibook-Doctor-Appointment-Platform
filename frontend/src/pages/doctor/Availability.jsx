import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import DoctorSidebar from "../../components/DoctorSidebar";
import { AppContext } from "../../context/AppContext";
import { createAvailability, deleteAvailability, getMyAvailability } from "../../services/doctor.service.js";

export default function Availability() {
  const { dToken } = useContext(AppContext);
  const navigate = useNavigate();
  const [slots, setSlots] = useState([]);
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = async () => { const response = await getMyAvailability(); setSlots(response.data); };
  useEffect(() => { if (!dToken) navigate("/login"); else refresh().catch((e) => toast.error(e.message)); }, [dToken]);
  const add = async (event) => {
    event.preventDefault(); setBusy(true);
    try { await createAvailability(new Date(startsAt).toISOString(), new Date(endsAt).toISOString()); await refresh(); setStartsAt(""); setEndsAt(""); toast.success("Availability added"); }
    catch (e) { toast.error(e.response?.data?.detail || e.message); }
    finally { setBusy(false); }
  };
  const remove = async (id) => { try { await deleteAvailability(id); await refresh(); } catch (e) { toast.error(e.response?.data?.detail || e.message); } };
  return <div className="flex min-h-screen bg-surface"><DoctorSidebar /><main className="flex-1 p-6 md:p-10"><div className="max-w-4xl mx-auto"><h1 className="text-2xl font-bold text-dark">Manage availability</h1><p className="text-muted mt-1 mb-6">Add dated appointment windows for patients to book.</p>
    <form onSubmit={add} className="bg-white rounded-xl p-5 shadow-sm grid md:grid-cols-3 gap-4 items-end"><label className="text-sm">Starts at<input required type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} className="input-field mt-1" /></label><label className="text-sm">Ends at<input required type="datetime-local" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} className="input-field mt-1" /></label><button disabled={busy} className="bg-primary text-white rounded-lg py-3 disabled:opacity-60">{busy ? "Saving…" : "Add availability"}</button></form>
    <section className="mt-8 bg-white rounded-xl shadow-sm divide-y">{slots.length ? slots.map((slot) => <div key={slot.id} className="p-4 flex justify-between items-center"><span>{new Date(slot.starts_at).toLocaleString()} – {new Date(slot.ends_at).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})} <small className="text-muted">{slot.is_booked ? "Booked" : "Available"}</small></span>{!slot.is_booked && <button onClick={() => remove(slot.id)} className="text-red-600 text-sm">Remove</button>}</div>) : <p className="p-5 text-muted">No availability added yet.</p>}</section>
  </div></main></div>;
}
