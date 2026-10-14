import apiClient from "./apiClient.js";
import { normalizeUser, serviceResult } from "./normalizers.js";

const patient = { role: "patient" };

export const getUserProfile = () => apiClient.get("/api/v1/users/profile", patient).then((response) => serviceResult(response, { user: normalizeUser(response.data.user) }));
export const updateUserProfile = (data) => apiClient.put("/api/v1/users/profile", {
  full_name: data.name ?? data.full_name,
  phone: data.phone,
  gender: data.gender,
  date_of_birth: data.dob ?? data.date_of_birth,
  blood_group: data.bloodGroup ?? data.blood_group,
  insurance_provider: data.insuranceProvider ?? data.insurance_provider,
  insurance_policy_no: data.insurancePolicyNo ?? data.insurance_policy_no,
}, patient).then((response) => serviceResult(response, { user: normalizeUser(response.data.user) }));
