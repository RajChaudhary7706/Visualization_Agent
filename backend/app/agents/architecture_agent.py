from collections import Counter

from app.services.llm_service import call_llm


def _top_connections(graph, limit=20):
    ranked = sorted(
        graph.nodes(),
        key=lambda node: (
            graph.in_degree(node) + graph.out_degree(node),
            graph.out_degree(node),
            graph.in_degree(node),
            str(node),
        ),
        reverse=True,
    )
    return [
        {
            "node": node,
            "type": graph.nodes[node].get("type", "unknown"),
            "in_degree": graph.in_degree(node),
            "out_degree": graph.out_degree(node),
        }
        for node in ranked[:limit]
    ]


def _sample_edges(graph, limit=50):
    edge_rows = []
    for src, dst, data in graph.edges(data=True):
        edge_rows.append(
            {
                "source": src,
                "target": dst,
                "type": data.get("type", "unknown"),
                "weight": data.get("weight", 1),
            }
        )
    edge_rows.sort(
        key=lambda row: (row["weight"], row["type"], row["source"], row["target"]),
        reverse=True,
    )
    return edge_rows[:limit]


def _top_folders(graph, limit=15):
    folders = [
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "folder"
    ]
    folders.sort(key=lambda node: (graph.out_degree(node), graph.in_degree(node), str(node)), reverse=True)
    return folders[:limit]


def generate_architecture_description(graph):
    node_types = Counter(data.get("type", "unknown") for _, data in graph.nodes(data=True))
    edge_types = Counter(data.get("type", "unknown") for _, _, data in graph.edges(data=True))

    prompt = f"""
Explain this repository architecture in very simple language for a person who is not deeply technical.

Write the explanation in short sections with these headings:
1. What this project is
2. How the project is organized
3. Main folders and what they do
4. Important files and how they connect
5. How data or requests likely move through the app
6. What a new developer should look at first

Rules:
- Be concrete and easy to understand
- Mention real folder names and file names from the graph
- Prefer short paragraphs or bullets
- Avoid jargon when possible
- If something is uncertain, say "likely" instead of pretending it is certain

Repository graph summary:
- total_nodes: {graph.number_of_nodes()}
- total_edges: {graph.number_of_edges()}
- node_types: {dict(node_types)}
- edge_types: {dict(edge_types)}

Top folders:
{_top_folders(graph)}

Most connected nodes:
{_top_connections(graph)}

Representative edges:
{_sample_edges(graph)}
"""

    return call_llm(prompt)
