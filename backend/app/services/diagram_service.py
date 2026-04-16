import re

def clean(node):
    return re.sub(r'[^a-zA-Z0-9_]', '_', node)


def is_noise(node):
    noise_keywords = [
        "node_modules", "react", "redux", "lodash",
        "__pycache__", ".test", ".spec"
    ]
    return any(k in node.lower() for k in noise_keywords)


def generate_mermaid(graph):
    lines = ["graph TD"]

    for src, dst, data in graph.edges(data=True):

        # ❌ remove noise
        if is_noise(src) or is_noise(dst):
            continue

        src_clean = clean(src)
        dst_clean = clean(dst)

        # ✅ readable labels
        lines.append(f'  {src_clean}["{src}"] --> {dst_clean}["{dst}"]')

    return "\n".join(lines)


def _node_label(graph, node):
    return graph.nodes[node].get("label", str(node))


def generate_mermaid(graph):
    lines = ["graph TD"]

    folder_nodes = sorted(
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "folder" and not is_noise(str(node))
    )
    file_nodes = sorted(
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "code" and not is_noise(str(node))
    )
    service_nodes = sorted(
        node for node, data in graph.nodes(data=True)
        if data.get("type") == "service" and not is_noise(str(node))
    )

    for folder in folder_nodes:
        folder_clean = clean(folder)
        lines.append(f'  subgraph {folder_clean}_group["{_node_label(graph, folder)}"]')

        child_files = sorted(
            target for source, target, data in graph.edges(data=True)
            if source == folder and data.get("type") == "contains" and graph.nodes[target].get("type") == "code"
        )
        child_folders = sorted(
            target for source, target, data in graph.edges(data=True)
            if source == folder and data.get("type") == "contains" and graph.nodes[target].get("type") == "folder"
        )

        for child in child_folders + child_files:
            if is_noise(str(child)):
                continue
            child_clean = clean(child)
            lines.append(f'    {child_clean}["{_node_label(graph, child)}"]')

        lines.append("  end")

    standalone_files = [
        node for node in file_nodes
        if graph.in_degree(node) == 0 and graph.out_degree(node) == 0
    ]
    for node in standalone_files:
        node_clean = clean(node)
        lines.append(f'  {node_clean}["{_node_label(graph, node)}"]')

    for service in service_nodes:
        service_clean = clean(service)
        lines.append(f'  {service_clean}["{_node_label(graph, service)}"]')

    for src, dst, data in graph.edges(data=True):
        if is_noise(str(src)) or is_noise(str(dst)):
            continue
        if data.get("type") == "contains":
            continue

        src_clean = clean(src)
        dst_clean = clean(dst)
        lines.append(f'  {src_clean} --> {dst_clean}')

    return "\n".join(lines)


def generate_mermaid(graph):
    lines = ["graph TD"]

    for node, _data in graph.nodes(data=True):
        if is_noise(node):
            continue

        node_clean = clean(node)
        lines.append(f'  {node_clean}["{node}"]')

    for src, dst, _data in graph.edges(data=True):
        if is_noise(src) or is_noise(dst):
            continue

        src_clean = clean(src)
        dst_clean = clean(dst)
        lines.append(f'  {src_clean}["{src}"] --> {dst_clean}["{dst}"]')

    return "\n".join(lines)
