import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAnalyze } from "../hooks/useAnalyze";
import MermaidRenderer from "../components/visualization/MermaidRenderer";

const Results = () => {
  const { state } = useLocation();
  const { result, loading, runAnalysis } = useAnalyze();

  useEffect(() => {
    console.log("STATE:", state);

    // ✅ ONLY run if valid data exists
    if (!state || !state.github_url) {
      console.warn("❌ No valid GitHub URL provided");
      return;
    }

    runAnalysis(state);

  }, [state]);

  // ✅ Loading state
  if (loading) {
    return <p className="text-white p-6">Analyzing project...</p>;
  }

  // ✅ No result fallback
  if (!result) {
    return <p className="text-white p-6">No data available</p>;
  }

  return (
    <div className="p-6 bg-black text-white min-h-screen">
      <h1 className="text-2xl mb-4">Architecture Diagram</h1>

      {/* ✅ Safe rendering */}
      {result.diagram_ai ? (
        <MermaidRenderer chart={result.diagram_ai} />
      ) : (
        <p>No diagram available</p>
      )}

      <div className="mt-6">
        <h2 className="text-xl">Analysis</h2>

        {/* ✅ Safe description */}
        <p>{result.description || "No description available"}</p>

        <h3 className="mt-4">Risks</h3>

        {/* ✅ Safe risks */}
        <ul>
          {result.risks && result.risks.length > 0 ? (
            result.risks.map((r, i) => (
              <li key={i}>⚠️ {r}</li>
            ))
          ) : (
            <li>No risks detected</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default Results;