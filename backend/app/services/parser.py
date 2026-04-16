import re

def extract_imports(file_path):
    imports = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Python
        imports += re.findall(r'import (\w+)', content)
        imports += re.findall(r'from (\w+)', content)

        # JS/TS
        imports += re.findall(r'import .* from [\'"](.*?)[\'"]', content)
        imports += re.findall(r'require\([\'"](.*?)[\'"]\)', content)

        # Java
        imports += re.findall(r'import (.*?);', content)

    except:
        pass

    return imports