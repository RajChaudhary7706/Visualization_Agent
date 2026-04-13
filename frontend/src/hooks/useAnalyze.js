import { useState } from "react";
import axios from "axios";

export const useAnalyze = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async (data) => {
    try {
      setLoading(true);

      const response = await axios.post(
        "http://localhost:8000/analyze",
        data,
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      console.log("API RESPONSE:", response.data);

      setResult(response.data);
    } catch (error) {
      console.error("Error analyzing project:", error);
    } finally {
      setLoading(false);
    }
  };

  return { result, loading, runAnalysis };
};