def compare_graphs(static_graph, runtime_graph):
    static_nodes = set(static_graph.nodes)
    runtime_nodes = set(runtime_graph.nodes)

    missing = runtime_nodes - static_nodes
    unused = static_nodes - runtime_nodes

    return {
        "runtime_only": list(missing),
        "unused_code": list(unused)
    }