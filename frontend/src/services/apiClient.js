import axios from "axios";

const configured = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
export const BASE_URL = configured.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
export const TOKEN_KEYS = { patient: "token", doctor: "dToken", admin: "aToken" };

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: false,
});

const storage = typeof window === "undefined" ? null : window.sessionStorage;
const readToken = (role) => {
  try {
    if (role) return storage?.getItem(TOKEN_KEYS[role]);
    return storage?.getItem(TOKEN_KEYS.admin) || storage?.getItem(TOKEN_KEYS.doctor) || storage?.getItem(TOKEN_KEYS.patient);
  } catch {
    return null;
  }
};

apiClient.interceptors.request.use((config) => {
  const token = readToken(config.role);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const payload = error?.response?.data;
    if (error.response && payload && typeof payload === "object" && !payload.message) {
      const detail = payload.detail;
      error.response.data.message = Array.isArray(detail)
        ? detail.map((item) => item.msg).join(". ")
        : detail || `Request failed (${status})`;
    }
    if (status === 401) {
      Object.values(TOKEN_KEYS).forEach((key) => storage?.removeItem(key));
      if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent("medibook:unauthorized"));
    }
    return Promise.reject(error);
  },
);

export default apiClient;
