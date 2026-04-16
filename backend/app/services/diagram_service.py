import re

def clean(node):
    return re.sub(r'[^a-zA-Z0-9_]', '_', node)


def is_noise(node):
    noise_keywords = [
        "node_modules", "react", "redux", "lodash",
        "__pycache__", ".test", ".spec", "utils"
    ]
    return any(k in node.lower() for k in noise_keywords)


def generate_mermaid(graph):
    lines = ["graph TD"]

    for src, dst, data in graph.edges(data=True):

        # ❌ remove noise
        if is_noise(src) or is_noise(dst):
            continue

        # 🔥 remove weak edges
        if data.get("weight", 1) < 2:
            continue

        src_clean = clean(src)
        dst_clean = clean(dst)

        # ✅ readable labels
        lines.append(f'  {src_clean}["{src}"] --> {dst_clean}["{dst}"]')

    return "\n".join(lines)