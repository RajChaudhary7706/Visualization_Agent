import networkx as nx

def build_runtime_graph(trace_data):
    G = nx.DiGraph()

    prev = None

    for file, func in trace_data:
        node = f"{file}:{func}"
        G.add_node(node)

        if prev:
            G.add_edge(prev, node)

        prev = node

    return G