import networkx as nx
import os

# 🔥 Strong noise filter
IGNORE_LIBS = {
    "os", "sys", "json", "re", "math", "datetime",
    "numpy", "pandas", "logging", "collections"
}

def clean_name(name):
    normalized = str(name).replace("\\", "/")
    root, _ext = os.path.splitext(normalized)
    return root

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


def folder_name(name):
    return str(name).replace("\\", "/").strip("/")


def _parent_folders(module):
    normalized = str(module).replace("\\", "/").strip("/")
    parts = normalized.split("/")
    return ["/".join(parts[:index]) for index in range(1, len(parts))]


def _module_node_name(module):
    return str(module).replace("\\", "/").strip("/")


def build_full_graph(modules, edges, services, mapping):
    G = nx.DiGraph()
    module_lookup = {
        clean_name(module): _module_node_name(module)
        for module in modules
    }

    for module in modules:
        clean_module = clean_name(module)
        module_node = _module_node_name(module)
        G.add_node(module_node, type="code", label=module_node)

        folders = _parent_folders(module)
        for folder in folders:
            folder_node = folder_name(folder)
            G.add_node(folder_node, type="folder", label=folder_node)

        for index in range(len(folders) - 1):
            G.add_edge(
                folder_name(folders[index]),
                folder_name(folders[index + 1]),
                type="contains",
                weight=1,
            )

        if folders:
            G.add_edge(folder_name(folders[-1]), module_node, type="contains", weight=1)

    for service in services:
        G.add_node(service, type="service", label=service)

    weight_map = {
        "call": 4,
        "class": 3,
        "import": 1,
        "api": 5,
        "db": 5,
        "contains": 1,
        "mapping": 4,
        "service": 3,
    }

    for edge in edges:
        if len(edge) == 3:
            src, dst, edge_type = edge
        else:
            src, dst = edge
            edge_type = "import"

        src = module_lookup.get(clean_name(src), clean_name(src))
        dst = module_lookup.get(clean_name(dst), clean_name(dst))

        if dst in IGNORE_LIBS or dst == "":
            continue

        G.add_edge(src, dst, type=edge_type, weight=weight_map.get(edge_type, 1))

    for service, config in services.items():
        for dep in config.get("depends_on", []):
            G.add_edge(service, dep, type="service", weight=weight_map["service"])

    for service, mods in mapping.items():
        for module in mods:
            G.add_edge(
                service,
                module_lookup.get(clean_name(module), clean_name(module)),
                type="mapping",
                weight=weight_map["mapping"],
            )

    return G
