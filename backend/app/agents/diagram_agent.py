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

    try:
        response = call_llm(prompt)

        # 🔥 Extra safety (sometimes LLM returns empty)
        if not response or not isinstance(response, str):
            print("⚠️ Invalid LLM response")
            return mermaid_code

        return response

    except Exception as e:
        print("🔥 LLM ERROR (diagram):", e)

        # ✅ fallback → return original diagram
        return mermaid_code