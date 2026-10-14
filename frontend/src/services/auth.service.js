import apiClient from "./apiClient.js";
import { normalizeUser, serviceResult } from "./normalizers.js";

const adaptAuth = (promise) => promise.then((response) => serviceResult(response, {
  accessToken: response.data.access_token,
  user: normalizeUser(response.data.user),
}));

export const login = (data) => adaptAuth(apiClient.post("/api/v1/auth/login", data));
export const register = (data) => adaptAuth(apiClient.post("/api/v1/auth/register", {
  full_name: data.full_name || data.name,
  email: data.email,
  password: data.password,
}));
export const forgotPassword = async () => { throw new Error("Password reset is not configured in this local build."); };
export const resetPassword = async () => { throw new Error("Password reset is not configured in this local build."); };
export const logout = () => apiClient.post("/api/v1/auth/logout");
