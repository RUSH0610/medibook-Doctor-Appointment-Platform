import { createContext, useState, useEffect } from "react";
import { toast } from "react-toastify";
import { getUserProfile } from "../services/user.service.js";
import { getDoctors } from "../services/doctor.service.js";
import { getNotifications } from "../services/notification.service.js";

export const AppContext = createContext();

const AppContextProvider = ({ children }) => {
  const [token, setToken] = useState(sessionStorage.getItem("token") || "");
  const [userData, setUserData] = useState(null);
  const [aToken, setAToken] = useState(sessionStorage.getItem("aToken") || "");
  const [dToken, setDToken] = useState(sessionStorage.getItem("dToken") || "");
  const [doctors, setDoctors] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // ── Fetch doctors ──────────────────────────────────────────
  const fetchDoctors = async () => {
    try {
      const { data } = await getDoctors();
      if (data.success) setDoctors(data.data?.doctors || []);
    } catch (err) {
      console.error("fetchDoctors error:", err.message);
    }
  };

  // ── Fetch user profile ─────────────────────────────────────
  const loadUserData = async () => {
    try {
      const { data } = await getUserProfile();
      if (data.success) {
        setUserData(data.data.user);
      } else {
        // Only clear token if it's explicitly invalid (not just a server error)
        console.warn("Profile fetch failed:", data.message);
      }
    } catch (err) {
      // Only logout on 401 Unauthorized (token expired/invalid)
      if (err?.response?.status === 401) {
        console.warn("Token invalid, logging out...");
        logout();
      } else {
        console.error("loadUserData error:", err.message);
      }
    }
  };

  // ── Fetch notifications ────────────────────────────────────
  const loadNotifications = async () => {
    if (!token || !userData) return;
    try {
      const { data } = await getNotifications();
      if (data.success) {
        setNotifications(data.data.notifications);
        setUnreadCount(data.data.notifications.filter((n) => !n.isRead).length);
      }
    } catch (err) {
      console.error("loadNotifications error:", err.message);
    }
  };

  // ── Logout helpers ─────────────────────────────────────────
  const logout = () => {
    setToken("");
    setUserData(null);
    sessionStorage.removeItem("token");
  };

  const adminLogout = () => {
    setAToken("");
    sessionStorage.removeItem("aToken");
  };

  const doctorLogout = () => {
    setDToken("");
    sessionStorage.removeItem("dToken");
  };

  // ── Sync session tokens ───────────────────────────────────
  useEffect(() => {
    if (token) {
      sessionStorage.setItem("token", token);
      loadUserData();
    } else {
      sessionStorage.removeItem("token");
      setUserData(null);
    }
  }, [token]);

  useEffect(() => {
    if (aToken) sessionStorage.setItem("aToken", aToken);
    else sessionStorage.removeItem("aToken");
  }, [aToken]);

  useEffect(() => {
    if (dToken) sessionStorage.setItem("dToken", dToken);
    else sessionStorage.removeItem("dToken");
  }, [dToken]);

  useEffect(() => {
    const onUnauthorized = () => {
      setToken(""); setAToken(""); setDToken(""); setUserData(null);
    };
    window.addEventListener("medibook:unauthorized", onUnauthorized);
    return () => window.removeEventListener("medibook:unauthorized", onUnauthorized);
  }, []);

  // ── Load notifications when userData ready ─────────────────
  useEffect(() => {
    if (userData) loadNotifications();
  }, [userData]);

  // ── Initial doctor load ────────────────────────────────────
  useEffect(() => {
    fetchDoctors();
  }, []);

  const value = {
    token,
    setToken,
    aToken,
    setAToken,
    dToken,
    setDToken,
    userData,
    setUserData,
    doctors,
    getDoctors: fetchDoctors,
    notifications,
    unreadCount,
    loadNotifications,
    logout,
    adminLogout,
    doctorLogout,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContextProvider;
