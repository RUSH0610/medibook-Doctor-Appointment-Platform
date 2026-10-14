import apiClient from "./apiClient.js";
import { normalizeDoctor, serviceResult } from "./normalizers.js";

const doctor = { role: "doctor" };
const slotCache = new Map();

const displayTime = (value) => new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const key = (doctorId, date, time) => `${doctorId}|${date}|${time}`;

// Public
export const getDoctors = () => apiClient.get("/api/v1/doctors").then((response) => serviceResult(response, { doctors: response.data.map(normalizeDoctor) }));
export const getDoctorById = (doctorId) => apiClient.get(`/api/v1/doctors/${doctorId}`).then((response) => serviceResult(response, { doctor: normalizeDoctor(response.data) }));
export const getDoctorSlots = (doctorId, date) => apiClient.get(`/api/v1/doctors/${doctorId}/availability`, { params: { date } }).then((response) => {
  const slots = response.data.map((slot) => {
    const startTime = displayTime(slot.starts_at);
    slotCache.set(key(doctorId, date, startTime), slot.id);
    return { ...slot, startTime, available: true };
  });
  return serviceResult(response, { slots });
});
export const getCachedSlotId = (doctorId, date, time) => slotCache.get(key(doctorId, date, time));

// Doctor panel
export const getDoctorProfile = () => apiClient.get("/api/v1/doctors/me/profile", doctor).then((response) => serviceResult(response, { profileData: normalizeDoctor(response.data) }));
export const updateDoctorProfile = (data) => {
  const payload = {};
  if (data.fees !== undefined || data.consultation_fee !== undefined) {
    payload.consultation_fee = data.fees ?? data.consultation_fee;
  }
  if (data.available !== undefined || data.is_available !== undefined) {
    payload.is_available = data.available ?? data.is_available;
  }
  if (data.bio !== undefined && data.bio !== null) payload.bio = data.bio;
  if (data.hospital_affiliation !== undefined && data.hospital_affiliation !== null) {
    payload.hospital_affiliation = data.hospital_affiliation;
  }
  if (data.consultation_room !== undefined && data.consultation_room !== null) {
    payload.consultation_room = data.consultation_room;
  }
  return apiClient.put("/api/v1/doctors/me/profile", payload, doctor).then((response) => serviceResult(response, { profileData: normalizeDoctor(response.data) }));
};
export const getDoctorDashboard = () => apiClient.get("/api/v1/doctors/me/analytics", doctor).then((response) => serviceResult(response, response.data));
export const getMyAvailability = () => apiClient.get("/api/v1/doctors/me/availability", doctor);
export const createAvailability = (startsAt, endsAt) => apiClient.post("/api/v1/availability", { starts_at: startsAt, ends_at: endsAt }, doctor);
export const deleteAvailability = (slotId) => apiClient.delete(`/api/v1/availability/${slotId}`, doctor).then((response) => ({ ...response, data: { success: true, message: "Slot removed" } }));
