def generate_html(mermaid_code):
    return f"""
    <html>
    <body>
    <div class="mermaid">
    {mermaid_code}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true}});</script>
    </body>
    </html>
    """