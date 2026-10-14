import apiClient from "./apiClient.js";

const patient = { role: "patient" };

export const uploadMedicalRecord = (formData) =>
  apiClient.post("/api/v1/medical-records/", (() => {
    const converted = new FormData();
    converted.append("file", formData.get("file"));
    converted.append("title", formData.get("title") || "Medical document");
    converted.append("record_type", formData.get("category") || "Other");
    converted.append("description", formData.get("notes") || "");
    return converted;
  })(), { ...patient, headers: { "Content-Type": "multipart/form-data" } }).then((response) => ({ ...response, data: { success: true, data: { record: response.data }, message: "Record uploaded" } }));
export const getMyMedicalRecords = () => apiClient.get("/api/v1/medical-records/my", patient).then((response) => ({ ...response, data: { success: true, data: response.data, message: "Records loaded" } }));
export const shareRecordWithDoctor = (recordId, doctorId) =>
  apiClient.post("/api/v1/medical-records/share", { recordId, doctorId }, patient).then((response) => ({ ...response, data: { success: true, data: { record: response.data }, message: "Record shared" } }));
export const deleteMedicalRecord = (recordId) =>
  apiClient.delete(`/api/v1/medical-records/${recordId}`, patient).then((response) => ({
    ...response,
    data: { success: true, message: "Record deleted" },
  }));

export const getDoctorSharedRecords = () =>
  apiClient.get("/api/v1/medical-records/shared-with-me", { role: "doctor" }).then((response) => ({ ...response, data: { success: true, data: response.data, message: "Records loaded" } }));

export const viewMedicalRecordFile = async (recordId, role = "patient") => {
  const response = await apiClient.get(`/api/v1/medical-records/${recordId}/file`, {
    role,
    responseType: "blob",
  });
  const blobUrl = window.URL.createObjectURL(new Blob([response.data], { type: response.headers["content-type"] || "application/pdf" }));
  window.open(blobUrl, "_blank");
  setTimeout(() => window.URL.revokeObjectURL(blobUrl), 60000);
  return blobUrl;
};
