from app.services.llm_service import call_llm

def enhance_diagram(mermaid_code):
    prompt = f"""
    Improve this architecture diagram:

    {mermaid_code}

    Make it:
    - clean
    - grouped logically
    - readable

    Return only Mermaid code.
    """

    return call_llm(prompt)