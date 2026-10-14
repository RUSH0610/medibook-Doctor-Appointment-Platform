import apiClient from "./apiClient.js";
import { serviceResult } from "./normalizers.js";

export const checkSymptoms = (symptoms) =>
  apiClient.post("/api/v1/ai/symptom-check", { symptoms }, { role: "patient" }).then((response) => serviceResult(response, { guidance: response.data.guidance, disclaimer: response.data.disclaimer }));
