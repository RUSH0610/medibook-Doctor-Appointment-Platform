import { useState } from "react";
import { checkSymptoms } from "../../services/ai.service.js";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";


const SymptomChecker = () => {
  const [symptoms, setSymptoms] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleCheckSymptoms = async () => {
    if (!symptoms.trim()) {
      toast.error("Please describe your symptoms");
      return;
    }
    if (symptoms.trim().length < 10) {
      toast.error("Please describe your symptoms in more detail");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await checkSymptoms(symptoms);
      const data = response.data?.data || response.data || {};
      setResult(data);
    } catch (error) {
      const msg = error?.response?.data?.message || error?.response?.data?.detail || error?.message || "Failed to analyze symptoms";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency) => {
    if (urgency === "High") return "text-red-500 bg-red-50 border-red-200";
    if (urgency === "Medium") return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-green-600 bg-green-50 border-green-200";
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-semibold text-gray-800">AI Symptom Checker</h1>
        <p className="text-gray-500 mt-2">Describe your symptoms and get an instant speciality recommendation</p>
      </div>

      <div className="bg-white border rounded-xl p-6 shadow-sm">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe your symptoms
        </label>
        <textarea
          rows={5}
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="e.g. I have been experiencing severe headaches for 3 days, along with blurred vision and nausea..."
          className="w-full border border-gray-300 rounded-lg px-4 py-3 text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
        />
        <button
          onClick={handleCheckSymptoms}
          disabled={loading}
          className="mt-4 w-full bg-primary text-white py-3 rounded-lg font-medium hover:bg-primary/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Analyzing symptoms..." : "Check Symptoms"}
        </button>
      </div>

      {result && (
        <div className="mt-6 bg-white border rounded-xl p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">AI Recommendation & Guidance</h2>

          {result.speciality && (
            <div className="flex items-center gap-3">
              <span className="text-gray-500 text-sm">Suggested Speciality:</span>
              <span className="font-semibold text-primary text-lg">{result.speciality}</span>
            </div>
          )}

          {result.reason && (
            <div>
              <p className="text-sm text-gray-500 mb-1">Reason</p>
              <p className="text-gray-700">{result.reason}</p>
            </div>
          )}

          {result.urgency && (
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium ${getUrgencyColor(result.urgency)}`}>
              Urgency: {result.urgency} {result.urgency_reason ? `— ${result.urgency_reason}` : ""}
            </div>
          )}

          {result.guidance && (
            <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100">
              <p className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Health Guidance</p>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{result.guidance}</p>
            </div>
          )}

          <div className="pt-2">
            <p className="text-xs text-gray-400 mb-3">
              ⚠️ {result.disclaimer || "This is general information, not a diagnosis or a substitute for professional medical care."}
            </p>
            <button
              onClick={() => navigate(result.speciality ? `/doctors/${result.speciality}` : "/doctors")}
              className="w-full bg-primary text-white py-3 rounded-lg font-medium hover:bg-primary/90 transition"
            >
              {result.speciality ? `Find ${result.speciality} Doctors →` : "Find Available Doctors →"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SymptomChecker;
