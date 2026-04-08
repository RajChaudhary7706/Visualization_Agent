import networkx as nx

def build_full_graph(modules, edges, services, mapping):
    G = nx.DiGraph()

    # Add code nodes
    for m in modules:
        G.add_node(m, type="code")

    # Add service nodes
    for s in services:
        G.add_node(s, type="service")

    # Code dependencies
    for src, dst in edges:
        G.add_edge(src, dst, type="code")

    # Service dependencies
    for s, config in services.items():
        for dep in config["depends_on"]:
            G.add_edge(s, dep, type="service")

    # Mapping edges
    for service, mods in mapping.items():
        for m in mods:
            G.add_edge(service, m, type="mapping")

    return G