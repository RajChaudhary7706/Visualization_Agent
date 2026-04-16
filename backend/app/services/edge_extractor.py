import re
from app.services.resolver import resolve_import

def extract_edges(file_map):
    edges = []

    for module, full_path in file_map.items():

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()

            # Python imports
            imports = re.findall(r'import (\w+)', code)
            imports += re.findall(r'from (\w+)', code)

            for imp in imports:
                target = resolve_import(imp, file_map)

                if target:
                    edges.append((module, target, "import"))

        except Exception as e:
            print("Error:", e)

    return edges