# import os
# import ast

# def parse_python_project(path):
#     modules = []
#     edges = []

#     for root, _, files in os.walk(path):
#         for file in files:
#             if file.endswith(".py"):
#                 file_path = os.path.join(root, file)

#                 with open(file_path, "r", encoding="utf-8") as f:
#                     tree = ast.parse(f.read())

#                 module_name = file
#                 modules.append(module_name)

#                 for node in ast.walk(tree):
#                     if isinstance(node, ast.Import):
#                         for alias in node.names:
#                             edges.append((module_name, alias.name))

#     return modules, edges


import os
import ast

def parse_python_project(root_dir):
    modules = set()
    edges = []

    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".py"):

                file_path = os.path.join(dirpath, file)

                # ✅ Better module name (relative path)
                module_name = os.path.relpath(file_path, root_dir)

                modules.add(module_name)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    for node in ast.walk(tree):

                        # 🔹 IMPORT
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                edges.append((module_name, alias.name, "import"))

                        # 🔹 FROM IMPORT
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                edges.append((module_name, node.module, "import"))

                        # 🔹 FUNCTION CALLS 🔥
                        elif isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name):
                                edges.append((module_name, node.func.id, "call"))

                            elif isinstance(node.func, ast.Attribute):
                                edges.append((module_name, node.func.attr, "call"))

                        # 🔹 CLASS DEFINITIONS
                        elif isinstance(node, ast.ClassDef):
                            edges.append((module_name, node.name, "class"))

                        # 🔹 FUNCTION DEFINITIONS
                        elif isinstance(node, ast.FunctionDef):
                            edges.append((module_name, node.name, "function"))

                except Exception as e:
                    print(f"⚠️ Error parsing {file_path}: {e}")

    return list(modules), edges