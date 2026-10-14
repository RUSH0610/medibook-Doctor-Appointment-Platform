import { BASE_URL } from "./apiClient.js";

export const serviceResult = (response, data, message = "Success") => ({
  ...response,
  data: { success: true, data, message },
});

export function normalizeDoctor(doctor = {}) {
  const image = doctor.avatar_url ? (doctor.avatar_url.startsWith("http") ? doctor.avatar_url : `${BASE_URL}${doctor.avatar_url}`) : "/doctor-placeholder.svg";
  return {
    ...doctor,
    _id: doctor.id,
    name: doctor.full_name,
    speciality: doctor.specialization,
    specialityName: doctor.specialization,
    degree: doctor.qualification,
    experience: `${doctor.experience_years || 0} years`,
    experienceYears: doctor.experience_years || 0,
    fees: Number(doctor.consultation_fee || 0),
    about: doctor.bio || "",
    image,
    isVerified: Boolean(doctor.is_approved),
    available: Boolean(doctor.is_available),
    avgRating: Number(doctor.avg_rating || 0),
    totalReviews: Number(doctor.total_reviews || 0),
  };
}

export function normalizeUser(user = {}) {
  return {
    ...user,
    _id: user.id,
    name: user.full_name,
    image: user.avatar_url,
    dob: user.date_of_birth,
    bloodGroup: user.blood_group,
    insurancePolicyNo: user.insurance_policy_no,
    insuranceProvider: user.insurance_provider,
    emergencyContact: user.emergency_contact_name,
  };
}

export function normalizeAppointment(appointment = {}) {
  const start = appointment.slot?.starts_at ? new Date(appointment.slot.starts_at) : null;
  const doctor = appointment.doctor || appointment.slot?.doctor || (appointment.doctor_name ? { full_name: appointment.doctor_name } : null);
  return {
    ...appointment,
    _id: appointment.id,
    docId: doctor?.id || appointment.slot?.doctor_id,
    docData: doctor ? normalizeDoctor(doctor) : {},
    userData: appointment.patient_name ? { name: appointment.patient_name, email: appointment.patient_email, dob: appointment.patient_dob } : undefined,
    slotDate: start ? `${start.getFullYear()}_${String(start.getMonth() + 1).padStart(2, "0")}_${String(start.getDate()).padStart(2, "0")}` : "",
    slotTime: start ? start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "",
    type: appointment.appointment_type || "in-person",
    amount: Number(appointment.consultation_fee || 0),
    cancelled: appointment.status === "CANCELLED",
    isCompleted: appointment.status === "COMPLETED",
    doctorName: doctor?.full_name,
  };
}

export function normalizePrescription(item = {}) {
  const appt = item.appointment || {};
  const doctor = appt.slot?.doctor;
  const patient = appt.patient;
  return {
    ...item,
    _id: item.id,
    createdAt: item.created_at || item.createdAt,
    doctorName: item.doctor_name || doctor?.user?.full_name,
    doctorSpeciality: item.doctor_speciality || doctor?.specialization,
    patientName: item.patient_name || patient?.user?.full_name,
    appointmentId: item.appointment_id,
    medicines: (item.items || []).map((medicine) => ({ ...medicine, name: medicine.medicine_name, quantity: medicine.quantity || 1 })),
  };
}
