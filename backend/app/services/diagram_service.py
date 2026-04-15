import re

def clean(node):
    # Replace all invalid characters with underscore
    return re.sub(r'[^a-zA-Z0-9_]', '_', node)


def generate_mermaid(graph):
    lines = ["graph TD"]

    for src, dst, data in graph.edges(data=True):
        src_clean = clean(src)
        dst_clean = clean(dst)

        # 🔥 Keep original name as label
        lines.append(f'  {src_clean}["{src}"] --> {dst_clean}["{dst}"]')

    return "\n".join(lines)