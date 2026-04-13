import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAnalyze } from "../hooks/useAnalyze";
import MermaidRenderer from "../components/visualization/MermaidRenderer";

const Results = () => {
  const { state } = useLocation();
  const { result, loading, runAnalysis } = useAnalyze();

  useEffect(() => {
    console.log("STATE:", state);

    const payload = state || {
      github_url: "https://github.com/your-test-repo",
      docker_path: "docker-compose.yml",
    };

    runAnalysis(payload);
  }, []);

  if (loading) return <p className="text-white">Loading...</p>;

  if (!result) return null;

  return (
    <div className="p-6 bg-black text-white min-h-screen">
      <h1 className="text-2xl mb-4">Architecture Diagram</h1>

      {/* ✅ FIXED */}
      <MermaidRenderer chart={result.diagram_ai} />

      <div className="mt-6">
        <h2 className="text-xl">Analysis</h2>

        {/* ✅ FIXED */}
        <p>{result.description}</p>

        <h3 className="mt-4">Risks</h3>

        {/* ✅ FIXED */}
        <ul>
          {result.risks?.map((r, i) => (
            <li key={i}>⚠️ {r}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Results;