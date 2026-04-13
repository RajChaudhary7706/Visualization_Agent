import { useEffect, useRef } from "react";
import mermaid from "mermaid";

const MermaidRenderer = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (!chart) return;

    // 🔥 CLEAN the chart (IMPORTANT FIX)
    const cleanChart = chart
      .replace(/```mermaid/g, "")
      .replace(/```/g, "")
      .trim();

    mermaid.initialize({ startOnLoad: false });

    const renderDiagram = async () => {
      try {
        const id = "graph-" + Math.random().toString(36).substr(2, 9);

        const { svg } = await mermaid.render(id, cleanChart);

        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (err) {
        console.error("Mermaid render error:", err);
      }
    };

    renderDiagram();
  }, [chart]);

  return <div ref={ref} />;
};

export default MermaidRenderer;