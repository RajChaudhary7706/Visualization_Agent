# import re
# from app.services.resolver import resolve_import

# def extract_edges(file_map):
#     edges = []

#     for module, full_path in file_map.items():

#         try:
#             with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
#                 code = f.read()

#             # Python imports
#             imports = re.findall(r'import (\w+)', code)
#             imports += re.findall(r'from (\w+)', code)

#             for imp in imports:
#                 target = resolve_import(imp, file_map)

#                 if target:
#                     edges.append((module, target, "import"))

#         except Exception as e:
#             print("Error:", e)

#     return edges


"""
Improved Edge Extractor using AST parsing
Features:
- AST-based parsing for Python (more accurate than regex)
- Support for different import types (import X, from X import Y, etc.)
- Function call detection
- Class dependency detection
- Language-specific parsers for JS/TS
"""

import ast
import re
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

SOURCE_EXTENSIONS = [".py", ".js", ".jsx", ".ts", ".tsx", ".java"]


def _module_name_from_key(module_key: str) -> str:
    normalized = module_key.replace("\\", "/")
    root, _ext = str(Path(normalized)).rsplit(".", 1) if "." in Path(normalized).name else (normalized, "")
    return root.replace("\\", "/")


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def _candidate_module_keys(import_name: str, current_module: Optional[str] = None) -> List[str]:
    normalized = _normalize_path(import_name)
    candidates = []

    if normalized.startswith(".") and current_module:
        current_path = Path(_normalize_path(current_module))
        current_dir = current_path.parent
        resolved = (current_dir / normalized).resolve().as_posix()
        # Rebuild relative-like paths without requiring filesystem existence.
        parts = []
        for part in (current_dir / normalized).parts:
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        relative_target = "/".join(parts)
        candidates.append(relative_target)
    else:
        candidates.append(normalized)

    expanded = []
    for candidate in candidates:
        candidate = candidate.strip("/")
        if not candidate:
            continue
        expanded.append(candidate)
        for ext in SOURCE_EXTENSIONS:
            expanded.append(candidate + ext)
            expanded.append(candidate + "/index" + ext)

        basename = candidate.split("/")[-1]
        expanded.append(basename)
        for ext in SOURCE_EXTENSIONS:
            expanded.append(basename + ext)
            expanded.append(basename + "/index" + ext)

    seen = []
    for item in expanded:
        normalized_item = _normalize_path(item)
        if normalized_item not in seen:
            seen.append(normalized_item)
    return seen


class PythonImportExtractor(ast.NodeVisitor):
    """AST visitor to extract imports and dependencies"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.imports = set()
        self.function_calls = set()
        self.class_bases = set()
    
    def visit_Import(self, node):
        """Handle: import x, y, z"""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Handle: from x import y, z"""
        if node.module:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Detect function calls to other modules"""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                self.function_calls.add(node.func.value.id)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Extract base classes"""
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.class_bases.add(base.id)
        self.generic_visit(node)

def extract_python_imports(
    file_path: str,
    file_map: Dict[str, str],
    module_key: Optional[str] = None
) -> List[Tuple[str, str, str]]:
    """
    Extract imports from Python file using AST
    Returns: [(source, target, edge_type), ...]
    """
    edges = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        tree = ast.parse(code)
        extractor = PythonImportExtractor(file_path)
        extractor.visit(tree)
        
        module_name = _module_name_from_key(module_key) if module_key else Path(file_path).stem
        
        # Process imports
        for imp in extractor.imports:
            target = _resolve_import(imp, file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "import"))
        
        # Process function calls
        for func in extractor.function_calls:
            target = _resolve_import(func, file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "call"))
        
        # Process class bases
        for base in extractor.class_bases:
            target = _resolve_import(base, file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "class"))
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error extracting imports from {file_path}: {e}")
    
    return edges

def extract_js_imports(
    file_path: str,
    file_map: Dict[str, str],
    module_key: Optional[str] = None
) -> List[Tuple[str, str, str]]:
    """
    Extract imports from JavaScript/TypeScript files
    Handles: import X from 'module', require('module'), etc.
    """
    edges = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        module_name = _module_name_from_key(module_key) if module_key else Path(file_path).stem
        
        # ES6 imports: import x from 'module'
        es6_pattern = r"import\s+(?:{[^}]*}|[\w*\s,]+)\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(es6_pattern, code):
            target = _resolve_import(match.group(1), file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "import"))
        
        # CommonJS: require('module')
        cjs_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        for match in re.finditer(cjs_pattern, code):
            target = _resolve_import(match.group(1), file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "import"))
        
        # Dynamic imports: import('module')
        dynamic_pattern = r"import\(['\"]([^'\"]+)['\"]\)"
        for match in re.finditer(dynamic_pattern, code):
            target = _resolve_import(match.group(1), file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "dynamic_import"))
        
    except Exception as e:
        logger.error(f"Error extracting JS imports from {file_path}: {e}")
    
    return edges

def extract_java_imports(
    file_path: str,
    file_map: Dict[str, str],
    module_key: Optional[str] = None
) -> List[Tuple[str, str, str]]:
    """
    Extract imports from Java files
    Handles: import package.Class, import package.*
    """
    edges = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Extract class name
        class_pattern = r"public\s+class\s+(\w+)"
        class_match = re.search(class_pattern, code)
        module_name = class_match.group(1) if class_match else Path(file_path).stem
        
        # Java imports: import package.Class
        import_pattern = r"import\s+([\w.]+)"
        for match in re.finditer(import_pattern, code):
            import_name = match.group(1).split('.')[-1]  # Get class name
            target = _resolve_import(import_name, file_map, current_module=module_key)
            if target:
                edges.append((module_name, target, "import"))
    
    except Exception as e:
        logger.error(f"Error extracting Java imports from {file_path}: {e}")
    
    return edges

def _resolve_import(
    import_name: str,
    file_map: Dict[str, str],
    current_module: Optional[str] = None
) -> str:
    """
    Resolve import name to actual module in file_map
    Returns module name if found, None otherwise
    """
    normalized_map = {
        _normalize_path(module): _module_name_from_key(_normalize_path(module))
        for module in file_map.keys()
    }

    direct_candidates = _candidate_module_keys(import_name, current_module=current_module)

    for candidate in direct_candidates:
        candidate = _normalize_path(candidate)
        if candidate in normalized_map:
            return normalized_map[candidate]

    import_name = _normalize_path(import_name.replace(".", "/"))
    for module, normalized_module in normalized_map.items():
        if module.endswith("/" + import_name) or module == import_name:
            return normalized_module

    basename = import_name.split("/")[-1]
    for module, normalized_module in normalized_map.items():
        if module.endswith("/" + basename) or f"/{basename}." in module or module.startswith(basename + "."):
            return normalized_module
    
    return None

def extract_edges(file_map: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """
    Extract all edges from project files
    Automatically detects file type and uses appropriate parser
    
    Args:
        file_map: {module_name: full_path}
    
    Returns:
        List of (source, target, edge_type) tuples
    """
    edges = []
    
    for module, full_path in file_map.items():
        file_ext = Path(full_path).suffix.lower()
        
        try:
            if file_ext == ".py":
                edges.extend(extract_python_imports(full_path, file_map, module))
            elif file_ext in [".js", ".jsx"]:
                edges.extend(extract_js_imports(full_path, file_map, module))
            elif file_ext in [".ts", ".tsx"]:
                edges.extend(extract_js_imports(full_path, file_map, module))  # TS similar to JS
            elif file_ext == ".java":
                edges.extend(extract_java_imports(full_path, file_map, module))
            else:
                logger.debug(f"Unsupported file type: {file_ext}")
        
        except Exception as e:
            logger.error(f"Error processing {module}: {e}")
            continue
    
    # Remove duplicates
    unique_edges = list(set(edges))
    logger.info(f"Extracted {len(unique_edges)} unique edges from {len(file_map)} files")
    
    return unique_edges
