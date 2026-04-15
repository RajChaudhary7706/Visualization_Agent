import networkx as nx

def build_full_graph(modules, edges, services, mapping):
    G = nx.DiGraph()

    #  Add code nodes
    for m in modules:
        G.add_node(m, type="code")

    # Add service nodes
    for s in services:
        G.add_node(s, type="service")

    #  Handle edges with type + weight
    for edge in edges:
        if len(edge) == 3:
            src, dst, edge_type = edge
        else:
            src, dst = edge
            edge_type = "import"

        #FILTER NOISE (VERY IMPORTANT)
        if dst.startswith(("os", "sys", "json", "re")):
            continue

        # Assign weights
        if edge_type == "call":
            weight = 3
        elif edge_type == "import":
            weight = 1
        elif edge_type == "class":
            weight = 2
        else:
            weight = 1

        G.add_edge(src, dst, type=edge_type, weight=weight)

    #Service dependencies
    for s, config in services.items():
        for dep in config.get("depends_on", []):
            G.add_edge(s, dep, type="service", weight=2)

    #Mapping edges
    for service, mods in mapping.items():
        for m in mods:
            G.add_edge(service, m, type="mapping", weight=3)

    return G