import { useState } from "react";
import axios from "axios";

export const useAnalyze = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async (data) => {
    setLoading(true);

    try {
      const response = await axios.post(
        "http://localhost:8000/analyze",
        data,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("✅ API SUCCESS:", response.data);

      setResult(response.data);

    } catch (error) {
      // 🔥 SHOW REAL BACKEND ERROR
      if (error.response) {
        console.error("❌ BACKEND ERROR:", error.response.data);
      } else {
        console.error("❌ NETWORK ERROR:", error.message);
      }

    } finally {
      setLoading(false);
    }
  };

  return { result, loading, runAnalysis };
};