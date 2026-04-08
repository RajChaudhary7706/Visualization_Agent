from app.services.llm_service import call_llm

def generate_architecture_description(graph):
    nodes = list(graph.nodes(data=True))
    edges = list(graph.edges(data=True))
    
    prompt = f"""
    Analyze this system:

    Nodes: {nodes}
    Edges: {edges}

    Explain:
    - system architecture
    - service interactions
    - data flow
    - interactions between code and services
    """

    return call_llm(prompt)