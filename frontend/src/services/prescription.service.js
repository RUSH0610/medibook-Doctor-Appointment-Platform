import apiClient from "./apiClient.js";
import { normalizePrescription, serviceResult } from "./normalizers.js";

const patient = { role: "patient" };
const doctor = { role: "doctor" };

export const issuePrescription = (data) => apiClient.post("/api/v1/prescriptions/", {
  diagnosis: data.diagnosis,
  doctor_notes: data.notes || "",
  advice: data.advice || "",
  follow_up_date: data.followUpDate || null,
  lab_tests: Array.isArray(data.labTests) ? data.labTests.join(", ") : (data.labTests || ""),
  next_visit_in: data.nextVisitIn || "",
  notes: data.notes || "",
  items: (data.medicines || []).map((item) => ({ medicine_name: item.name || item.medicine_name, dosage: item.dosage, frequency: item.frequency, duration: item.duration, instructions: item.instructions || "", quantity: item.quantity || 1 })),
}, { ...doctor, params: { appointment_id: data.appointmentId } }).then((response) => serviceResult(response, { prescription: normalizePrescription(response.data) }));
export const getDoctorPrescriptions = () => apiClient.get("/api/v1/prescriptions/doctor", doctor).then((response) => serviceResult(response, { prescriptions: response.data.map(normalizePrescription) }));
export const getMyPrescriptions = () => apiClient.get("/api/v1/prescriptions/my", patient).then((response) => serviceResult(response, { prescriptions: response.data.map(normalizePrescription) }));
