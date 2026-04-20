import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAnalyze } from "../hooks/useAnalyze";
import MermaidRenderer from "../components/visualization/MermaidRenderer";

const TreeNode = ({ node, depth = 0 }) => {
  const paddingLeft = `${depth * 16}px`;

  if (node.type === "folder") {
    return (
      <div>
        <div style={{ paddingLeft }} className="text-yellow-300 font-semibold">
          {node.name}/
        </div>
        <div>
          {node.children?.map((child, index) => (
            <TreeNode key={`${node.name}-${index}`} node={child} depth={depth + 1} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ paddingLeft }} className="text-gray-300">
      {node.name}
    </div>
  );
};

const Results = () => {
  const { state } = useLocation();
  const { result, loading, runAnalysis } = useAnalyze();

  useEffect(() => {
    if (!state || !state.github_url) {
      return;
    }

    runAnalysis(state);
  }, [state]);

  if (loading) {
    return <p className="text-white p-6">Analyzing project...</p>;
  }

  if (!result) {
    return <p className="text-white p-6">No data available</p>;
  }

  const riskList = Array.isArray(result.risks) ? result.risks : [];
  const fileTree = Array.isArray(result.file_tree) ? result.file_tree : [];

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-6">Repository Analysis</h1>

      <div className="mb-8">
        <h2 className="text-2xl mb-4">Architecture Diagram</h2>
        {result.diagram_ai ? (
          <MermaidRenderer chart={result.diagram_ai} />
        ) : (
          <p>No diagram available</p>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-950 border border-gray-800 rounded-xl p-5">
          <h2 className="text-xl font-semibold mb-4">Repository Tree</h2>
          {fileTree.length > 0 ? (
            <div className="space-y-1">
              {fileTree.map((node, index) => (
                <TreeNode key={`${node.name}-${index}`} node={node} />
              ))}
            </div>
          ) : (
            <p className="text-gray-400">No file tree available</p>
          )}
        </div>

        <div className="bg-gray-950 border border-gray-800 rounded-xl p-5">
          <h2 className="text-xl font-semibold mb-4">Analysis Summary</h2>
          <p className="text-gray-300 mb-4">
            {result.description || "No description available"}
          </p>

          <div className="space-y-2 text-sm text-gray-400">
            <p>Total Files: {result.module_count ?? 0}</p>
            <p>Total Dependencies: {result.edge_count ?? 0}</p>
            <p>Total Services: {result.services_count ?? 0}</p>
            <p>Graph Nodes: {result.graph_nodes ?? 0}</p>
            <p>Graph Edges: {result.graph_edges ?? 0}</p>
          </div>

          <h3 className="text-lg font-semibold mt-6 mb-3">Risks</h3>
          {riskList.length > 0 ? (
            <ul className="list-disc list-inside text-gray-300">
              {riskList.map((risk, index) => (
                <li key={index}>{typeof risk === "string" ? risk : JSON.stringify(risk)}</li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-400">No risks detected</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Results;