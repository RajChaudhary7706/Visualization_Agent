def detect_risks(graph):
    risks = []

    for node in graph.nodes:
        if graph.in_degree(node) > 3:
            risks.append(f"{node} may be a bottleneck")

        if graph.out_degree(node) == 0:
            risks.append(f"{node} might be unused or isolated")

    return risks