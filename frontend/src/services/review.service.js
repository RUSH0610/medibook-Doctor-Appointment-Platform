import apiClient from "./apiClient.js";
import { serviceResult } from "./normalizers.js";

export const submitReview = (data) => apiClient.post("/api/v1/reviews/", { appointment_id: data.appointmentId, rating: data.rating, comment: data.comment, is_anonymous: data.isAnonymous }, { role: "patient" }).then((response) => serviceResult(response, { review: response.data }));
export const getDoctorReviews = (doctorId) => apiClient.get(`/api/v1/reviews/doctor/${doctorId}`).then((response) => serviceResult(response, response.data));
export const getAllReviews = () => apiClient.get("/api/v1/reviews/", { role: "admin" }).then((response) => serviceResult(response, response.data));
export const toggleReviewApproval = (reviewId) =>
  apiClient.put(`/api/v1/reviews/${reviewId}/approval`, {}, { role: "admin" }).then((response) => serviceResult(response, { review: response.data }));
