// import { useEffect } from "react";
// import { useLocation } from "react-router-dom";
// import { useAnalyze } from "../hooks/useAnalyze";
// import MermaidRenderer from "../components/visualization/MermaidRenderer";

// const Results = () => {
//   const { state } = useLocation();
//   const { result, loading, runAnalysis } = useAnalyze();

//   useEffect(() => {
//     console.log("STATE:", state);

//     // ✅ ONLY run if valid data exists
//     if (!state || !state.github_url) {
//       console.warn("❌ No valid GitHub URL provided");
//       return;
//     }

//     runAnalysis(state);

//   }, [state]);

//   // ✅ Loading state
//   if (loading) {
//     return <p className="text-white p-6">Analyzing project...</p>;
//   }

//   // ✅ No result fallback
//   if (!result) {
//     return <p className="text-white p-6">No data available</p>;
//   }

//   return (
//     <div className="p-6 bg-black text-white min-h-screen">
//       <h1 className="text-2xl mb-4">Architecture Diagram</h1>

//       {/* ✅ Safe rendering */}
//       {result.diagram_ai ? (
//         <MermaidRenderer chart={result.diagram_ai} />
//       ) : (
//         <p>No diagram available</p>
//       )}

//       <div className="mt-6">
//         <h2 className="text-xl">Analysis</h2>

//         {/* ✅ Safe description */}
//         <p>{result.description || "No description available"}</p>

//         <h3 className="mt-4">Risks</h3>

//         {/* ✅ Safe risks */}
//         <ul>
//           {result.risks && result.risks.length > 0 ? (
//             result.risks.map((r, i) => (
//               <li key={i}>⚠️ {r}</li>
//             ))
//           ) : (
//             <li>No risks detected</li>
//           )}
//         </ul>
//       </div>
//     </div>
//   );
// };

// export default Results;


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

const StructureCard = ({ fileName, structure }) => {
  const renderList = (label, items) => (
    <div className="mb-3">
      <h4 className="text-sm font-semibold text-cyan-300">{label}</h4>
      {items && items.length > 0 ? (
        <ul className="list-disc list-inside text-gray-300">
          {items.map((item, index) => (
            <li key={`${label}-${item}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-gray-500 text-sm">None</p>
      )}
    </div>
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-4">
      <h3 className="text-lg font-semibold text-white mb-2">{fileName}</h3>
      <p className="text-sm text-gray-400 mb-4">
        Language: {structure.language || "unknown"}
      </p>

      {renderList("Classes", structure.classes || [])}
      {renderList("Functions", structure.functions || [])}
      {renderList("Async Functions", structure.async_functions || [])}
      {renderList("Methods", structure.methods || [])}
      {renderList("Arrow Functions", structure.arrow_functions || [])}
      {renderList("Exports", structure.exports || [])}
      {renderList("Interfaces", structure.interfaces || [])}
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
  const fileStructures = result.file_structures || {};

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

      <div>
        <h2 className="text-2xl font-semibold mb-4">File Code Structures</h2>
        {Object.keys(fileStructures).length > 0 ? (
          Object.entries(fileStructures).map(([fileName, structure]) => (
            <StructureCard key={fileName} fileName={fileName} structure={structure} />
          ))
        ) : (
          <p className="text-gray-400">No file structure data available</p>
        )}
      </div>
    </div>
  );
};

export default Results;
