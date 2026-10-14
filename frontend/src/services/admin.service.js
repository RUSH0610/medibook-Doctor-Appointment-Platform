import apiClient from "./apiClient.js";
import { normalizeAppointment, normalizeDoctor, serviceResult } from "./normalizers.js";

const admin = { role: "admin" };

export const getAdminDashboard = () => Promise.all([
  apiClient.get("/api/v1/admin/dashboard", admin),
  apiClient.get("/api/v1/admin/appointments", admin),
]).then(([stats, appointments]) => {
  const recent = (appointments.data.appointments || []).slice(0, 5).map(normalizeAppointment);
  return serviceResult(stats, { dashData: { ...stats.data.dashData, latestAppointments: recent } });
});
export const getAllDoctors = () => apiClient.get("/api/v1/admin/doctors", admin).then((response) => serviceResult(response, { doctors: (response.data.doctors || []).map(normalizeDoctor) }));
export const addDoctor = (formData) => {
  const experience = String(formData.get("experience") || "0").match(/\d+/)?.[0] || "0";
  const body = {
    full_name: formData.get("name"), email: formData.get("email"), password: formData.get("password"),
    specialization: formData.get("speciality"), qualification: formData.get("degree"),
    experience_years: Number(experience), consultation_fee: Number(formData.get("fees")),
    bio: formData.get("about") || "", license_number: formData.get("licenseNumber") || null,
  };
  return apiClient.post("/api/v1/admin/doctors", body, admin).then((response) => serviceResult(response, { doctor: normalizeDoctor(response.data) }, "Doctor created; approval is pending"));
};
export const toggleDoctorAvailability = (doctorId) => apiClient.put(`/api/v1/admin/doctors/${doctorId}/availability`, {}, admin);
export const toggleDoctorApproval = (doctorId) => apiClient.put(`/api/v1/admin/doctors/${doctorId}/approval`, {}, admin).then((response) => serviceResult(response, { doctor: normalizeDoctor(response.data) }));
export const getAdminAppointments = () => apiClient.get("/api/v1/admin/appointments", admin).then((response) => serviceResult(response, { appointments: (response.data.appointments || []).map(normalizeAppointment) }));
