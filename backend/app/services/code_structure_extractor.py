import ast
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()

    if ext == ".py":
        return "python"
    if ext in {".js", ".jsx"}:
        return "javascript"
    if ext in {".ts", ".tsx"}:
        return "typescript"
    if ext == ".java":
        return "java"

    return "unknown"


class PythonStructureExtractor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []
        self.async_functions = []
        self.methods = []
        self._class_stack = []

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node):
        if self._class_stack:
            self.methods.append(node.name)
        else:
            self.functions.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self._class_stack:
            self.methods.append(node.name)
        else:
            self.async_functions.append(node.name)
        self.generic_visit(node)


def extract_python_structure(code: str) -> dict:
    try:
        tree = ast.parse(code)
        extractor = PythonStructureExtractor()
        extractor.visit(tree)

        return {
            "language": "python",
            "classes": sorted(set(extractor.classes)),
            "functions": sorted(set(extractor.functions)),
            "async_functions": sorted(set(extractor.async_functions)),
            "methods": sorted(set(extractor.methods)),
        }
    except SyntaxError as e:
        logger.warning(f"Python syntax error while extracting structure: {e}")
        return {
            "language": "python",
            "classes": [],
            "functions": [],
            "async_functions": [],
            "methods": [],
        }


def extract_js_ts_structure(code: str, language: str) -> dict:
    class_pattern = r"class\s+([A-Za-z_]\w*)"
    function_pattern = r"function\s+([A-Za-z_]\w*)\s*\("
    arrow_pattern = r"const\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"
    export_pattern = r"export\s+(?:default\s+)?(?:class|function|const|let|var)?\s*([A-Za-z_]\w*)?"
    method_pattern = r"\n\s{2,}([A-Za-z_]\w*)\s*\([^)]*\)\s*\{"

    classes = re.findall(class_pattern, code)
    functions = re.findall(function_pattern, code)
    arrow_functions = re.findall(arrow_pattern, code)
    methods = re.findall(method_pattern, code)

    exports = []
    for match in re.finditer(export_pattern, code):
        name = match.group(1)
        if name:
            exports.append(name)

    filtered_methods = [
        name for name in methods
        if name not in classes and name not in functions and name not in arrow_functions
    ]

    return {
        "language": language,
        "classes": sorted(set(classes)),
        "functions": sorted(set(functions)),
        "arrow_functions": sorted(set(arrow_functions)),
        "methods": sorted(set(filtered_methods)),
        "exports": sorted(set(exports)),
    }


def extract_java_structure(code: str) -> dict:
    class_pattern = r"\bclass\s+([A-Za-z_]\w*)"
    interface_pattern = r"\binterface\s+([A-Za-z_]\w*)"
    method_pattern = r"(?:public|private|protected)?\s*(?:static\s+)?[A-Za-z_<>\[\]]+\s+([A-Za-z_]\w*)\s*\("

    classes = re.findall(class_pattern, code)
    interfaces = re.findall(interface_pattern, code)
    methods = re.findall(method_pattern, code)

    filtered_methods = [name for name in methods if name not in classes]

    return {
        "language": "java",
        "classes": sorted(set(classes)),
        "interfaces": sorted(set(interfaces)),
        "methods": sorted(set(filtered_methods)),
    }


def extract_file_structure(file_path: str) -> dict:
    language = detect_language(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return {
            "language": language,
            "classes": [],
            "functions": [],
            "async_functions": [],
            "methods": [],
        }

    if language == "python":
        return extract_python_structure(code)

    if language in {"javascript", "typescript"}:
        return extract_js_ts_structure(code, language)

    if language == "java":
        return extract_java_structure(code)

    return {
        "language": language,
        "classes": [],
        "functions": [],
        "async_functions": [],
        "methods": [],
    }


def extract_code_structures(file_map: dict) -> dict:
    structures = {}

    for module_name, file_path in file_map.items():
        structures[module_name] = extract_file_structure(file_path)

    return structures
