import { useState } from "react";
import { analyzeProject } from "../api/analyze";

export const useAnalyze = () => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const runAnalysis = async (data) => {
        setLoading(true);
        try {
            const response = await analyzeProject(data);
            setResult(response.data);
        } catch (error) {
            console.error("Error analyzing project:", error);
        } finally {
            setLoading(false);
        }
    };

    return { result, loading, runAnalysis };
}