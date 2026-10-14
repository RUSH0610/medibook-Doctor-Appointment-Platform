import apiClient from "./apiClient.js";
import { getCachedSlotId } from "./doctor.service.js";
import { normalizeAppointment, serviceResult } from "./normalizers.js";

const patient = { role: "patient" };
const doctor = { role: "doctor" };

// Patient
export const bookAppointment = (data) => {
  const date = data.appointmentDate || data.slotDate;
  const slotId = data.slot_id || getCachedSlotId(data.doctorId || data.docId, date, data.startTime || data.slotTime);
  if (!slotId) return Promise.reject(new Error("That availability slot expired. Select the time again."));
  return apiClient.post("/api/v1/appointments", { slot_id: slotId, reason: data.reason || "", appointment_type: data.appointmentType || data.type || "in-person", phone: data.phone || null }, patient).then((response) => serviceResult(response, { appointment: normalizeAppointment(response.data) }, "Appointment booked"));
};
export const getMyAppointments = () => apiClient.get("/api/v1/appointments/my", patient).then((response) => serviceResult(response, { appointments: response.data.map((item) => normalizeAppointment(item)) }));
export const rescheduleAppointment = (id, data) => {
  const date = data.appointmentDate || data.slotDate;
  const slotId = data.slot_id || getCachedSlotId(data.doctorId || data.docId, date, data.startTime || data.slotTime);
  if (!slotId) return Promise.reject(new Error("That availability slot expired. Select the time again."));
  return apiClient.post(`/api/v1/appointments/${id}/reschedule`, { slot_id: slotId, reason: data.reason || "", appointment_type: data.appointmentType || "in-person" }, patient).then((response) => serviceResult(response, { appointment: normalizeAppointment(response.data) }));
};

// Doctor
export const getDoctorAppointments = () => apiClient.get("/api/v1/appointments/doctor", doctor).then((response) => serviceResult(response, { appointments: response.data.map((item) => normalizeAppointment(item)) }));
export const completeAppointment = (id) => apiClient.post(`/api/v1/appointments/${id}/complete`, {}, doctor).then((response) => serviceResult(response, { appointment: normalizeAppointment(response.data) }));

// Shared: patient owner, treating doctor or admin. `role` selects which session to use.
export const cancelAppointment = (id, role = "patient") =>
  apiClient.post(`/api/v1/appointments/${id}/cancel`, {}, { role }).then((response) => serviceResult(response, { appointment: normalizeAppointment(response.data) }));
