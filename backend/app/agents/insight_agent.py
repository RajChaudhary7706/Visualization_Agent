from app.services.llm_service import call_llm

def generate_insights(static_graph, runtime_graph, risks):
    prompt = f"""
    Analyze system deeply:

    Static Graph: {list(static_graph.edges)}
    Runtime Graph: {list(runtime_graph.edges)}
    Risks: {risks}

    Give:
    - hidden dependencies
    - performance issues
    - architecture improvements
    """

    return call_llm(prompt)