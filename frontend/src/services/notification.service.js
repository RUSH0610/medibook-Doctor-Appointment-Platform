import apiClient from "./apiClient.js";
import { serviceResult } from "./normalizers.js";

const patient = { role: "patient" };

export const getNotifications = () => apiClient.get("/api/v1/notifications/", patient).then((response) => serviceResult(response, response.data));
export const getUnreadCount = () => apiClient.get("/api/v1/notifications/unread-count", patient).then((response) => serviceResult(response, response.data));
export const markNotificationRead = (id) => apiClient.post(`/api/v1/notifications/${id}/read`, {}, patient).then((response) => serviceResult(response, response.data));
export const markAllNotificationsRead = () => apiClient.post("/api/v1/notifications/read-all", {}, patient).then((response) => serviceResult(response, response.data));
