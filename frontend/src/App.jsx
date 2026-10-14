import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useContext } from "react";
import { AppContext } from "./context/AppContext";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

// Layout
import Navbar from "./components/Navbar.jsx";
import Footer from "./components/Footer.jsx";
import PatientMenu from "./components/PatientMenu.jsx";

// User pages
import Home from "./pages/public/Home.jsx";
import Login from "./pages/public/Login.jsx";
import Doctors from "./pages/public/Doctors.jsx";
import DoctorDetail from "./pages/public/DoctorDetail.jsx";
import Appointment from "./pages/patient/Appointment.jsx";
import MyAppointments from "./pages/patient/MyAppointments.jsx";
import MyProfile from "./pages/patient/MyProfile.jsx";
import MyRecords from "./pages/patient/MyRecords.jsx";
import MyPrescriptions from "./pages/patient/MyPrescriptions.jsx";
import SymptomChecker from "./pages/public/SymptomChecker.jsx";

// Admin pages
import AdminDashboard from "./pages/admin/Dashboard.jsx";
import AdminDoctors from "./pages/admin/Doctors.jsx";
import AdminAddDoctor from "./pages/admin/AddDoctor.jsx";
import AdminAppointments from "./pages/admin/Appointments.jsx";
import AdminReviews from "./pages/admin/Reviews.jsx";

// Doctor pages
import DoctorDashboard from "./pages/doctor/Dashboard.jsx";
import DoctorAppointments from "./pages/doctor/Appointments.jsx";
import DoctorProfile from "./pages/doctor/Profile.jsx";
import DoctorPrescriptions from "./pages/doctor/Prescriptions.jsx";
import DoctorPatientRecords from "./pages/doctor/PatientRecords.jsx";
import DoctorAvailability from "./pages/doctor/Availability.jsx";

const RequireRole = ({ role, children }) => {
  const { token, aToken, dToken } = useContext(AppContext);
  const valid = role === "patient" ? token : role === "admin" ? aToken : dToken;
  return valid ? children : <Navigate to="/login" replace />;
};

const UserLayout = ({ children }) => (
  <>
    <Navbar />
    <PatientMenu />
    <main className="min-h-screen">{children}</main>
    <Footer />
  </>
);

function App() {
  return (
    <BrowserRouter>
      <ToastContainer position="top-right" autoClose={3000} />
      <Routes>
        {/* ── User Routes ── */}
        <Route
          path="/"
          element={
            <UserLayout>
              <Home />
            </UserLayout>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/" replace />} />
        <Route
          path="/doctors"
          element={
            <UserLayout>
              <Doctors />
            </UserLayout>
          }
        />
        <Route
          path="/doctors/:speciality"
          element={
            <UserLayout>
              <Doctors />
            </UserLayout>
          }
        />
        <Route
          path="/doctor/:docId"
          element={
            <UserLayout>
              <DoctorDetail />
            </UserLayout>
          }
        />
        <Route
          path="/appointment/:docId"
          element={
            <UserLayout>
              <Appointment />
            </UserLayout>
          }
        />
        <Route
          path="/my-appointments"
          element={<RequireRole role="patient"><UserLayout>
              <MyAppointments />
            </UserLayout></RequireRole>}
        />
        <Route
          path="/my-profile"
          element={<RequireRole role="patient"><UserLayout>
              <MyProfile />
            </UserLayout></RequireRole>}
        />
        <Route
          path="/my-records"
          element={<RequireRole role="patient"><UserLayout>
              <MyRecords />
            </UserLayout></RequireRole>}
        />
        <Route
          path="/my-prescriptions"
          element={<RequireRole role="patient"><UserLayout>
              <MyPrescriptions />
            </UserLayout></RequireRole>}
        />
        <Route
          path="/symptom-checker"
          element={
            <UserLayout>
              <SymptomChecker />
            </UserLayout>
          }
        />

        {/* ── Admin Routes ── */}
        <Route path="/admin" element={<RequireRole role="admin"><AdminDashboard /></RequireRole>} />
        <Route path="/admin/doctors" element={<RequireRole role="admin"><AdminDoctors /></RequireRole>} />
        <Route path="/admin/add-doctor" element={<RequireRole role="admin"><AdminAddDoctor /></RequireRole>} />
        <Route path="/admin/appointments" element={<RequireRole role="admin"><AdminAppointments /></RequireRole>} />
        <Route path="/admin/reviews" element={<RequireRole role="admin"><AdminReviews /></RequireRole>} />

        {/* ── Doctor Routes ── */}
        <Route path="/doctor/dashboard" element={<RequireRole role="doctor"><DoctorDashboard /></RequireRole>} />
        <Route path="/doctor/appointments" element={<RequireRole role="doctor"><DoctorAppointments /></RequireRole>} />
        <Route path="/doctor/availability" element={<RequireRole role="doctor"><DoctorAvailability /></RequireRole>} />
        <Route path="/doctor/profile" element={<RequireRole role="doctor"><DoctorProfile /></RequireRole>} />
        <Route path="/doctor/prescriptions" element={<RequireRole role="doctor"><DoctorPrescriptions /></RequireRole>} />
        <Route
          path="/doctor/patient-records"
          element={<RequireRole role="doctor"><DoctorPatientRecords /></RequireRole>}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
