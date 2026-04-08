import os
import ast

def parse_python_project(path):
    modules = []
    edges = []

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                module_name = file
                modules.append(module_name)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            edges.append((module_name, alias.name))

    return modules, edges