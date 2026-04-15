import os
import re

def parse_js_project(root_dir):
    modules = set()
    edges = []

    import_pattern = re.compile(r'import .* from [\'"](.*)[\'"]')
    require_pattern = re.compile(r'require\([\'"](.*)[\'"]\)')

    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".js"):
                file_path = os.path.join(dirpath, file)
                module_name = os.path.relpath(file_path, root_dir)

                modules.add(module_name)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                        imports = import_pattern.findall(content)
                        requires = require_pattern.findall(content)

                        for imp in imports + requires:
                            edges.append((module_name, imp, "import"))

                except Exception as e:
                    print(f"⚠️ JS parse error {file_path}: {e}")

    return list(modules), edges