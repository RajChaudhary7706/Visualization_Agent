def generate_mermaid(graph):
    lines = ["graph TD"]
    
    for src, dst, data in graph.edges(data=True):
        lines.append(f"  {src} --> {dst}")
        
    return "\n" .join(lines)