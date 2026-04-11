import { useEffect, useRef } from "react";
import mermaid from "mermaid";

const MermaidRenderer = ({ chart }) => {
    const ref = useRef(null);
    useEffect(() => {
        mermaid.initialize({ startOnLoad: true });
        if (ref.current) {
            ref.current.innerHTML = chart;
            mermaid.contentLoaded();
        }
    }, [chart]);
    
    return <div ref={ref} className="bg-white p-4 rounded"></div>;
}

export default MermaidRenderer;
