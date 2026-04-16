import networkx as nx
import os

# 🔥 Strong noise filter
IGNORE_LIBS = {
    "os", "sys", "json", "re", "math", "datetime",
    "numpy", "pandas", "logging", "collections"
}

def clean_name(name):
    return os.path.basename(name).replace(".py", "")

def build_full_graph(modules, edges, services, mapping):
    G = nx.DiGraph()

    # ✅ Add code nodes
    for m in modules:
        clean = clean_name(m)
        G.add_node(clean, type="code")

    # ✅ Add service nodes
    for s in services:
        G.add_node(s, type="service")

    # ✅ Add edges (IMPROVED)
    for edge in edges:
        if len(edge) == 3:
            src, dst, edge_type = edge
        else:
            src, dst = edge
            edge_type = "import"

        src = clean_name(src)
        dst = clean_name(dst)

        # 🚫 Strong noise filtering
        if dst in IGNORE_LIBS or dst == "":
            continue

        # 🎯 Smart weights
        weight_map = {
            "call": 4,
            "class": 3,
            "import": 1,
            "api": 5,
            "db": 5
        }

        weight = weight_map.get(edge_type, 1)

        G.add_edge(src, dst, type=edge_type, weight=weight)

    # ✅ Service dependencies
    for s, config in services.items():
        for dep in config.get("depends_on", []):
            G.add_edge(s, dep, type="service", weight=3)

    # ✅ Mapping (service → modules)
    for service, mods in mapping.items():
        for m in mods:
            G.add_edge(service, clean_name(m), type="mapping", weight=4)

    return G