import networkx as nx
from collections import defaultdict

def build_runtime_graph(trace_data):
    G = nx.DiGraph()
    
    call_stack = []
    call_count = defaultdict(int)

    for event in trace_data:
        file, func, action = event   # 👈 assume: ('file.py', 'func', 'call'/'return')

        node = f"{file}:{func}"
        G.add_node(node)

        if action == "call":
            if call_stack:
                caller = call_stack[-1]
                G.add_edge(caller, node)
                call_count[(caller, node)] += 1

            call_stack.append(node)

        elif action == "return":
            if call_stack:
                call_stack.pop()

    # 🔥 add weights (important!)
    for (u, v), count in call_count.items():
        G[u][v]["weight"] = count

    return G