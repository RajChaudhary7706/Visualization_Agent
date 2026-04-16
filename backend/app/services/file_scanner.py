import os

SUPPORTED_EXT = {
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"
}

def scan_project(root_path):
    file_map = {}

    for root, dirs, files in os.walk(root_path):
        for file in files:
            ext = os.path.splitext(file)[1]

            if ext in SUPPORTED_EXT:
                full_path = os.path.join(root, file)

                # 👇 KEY: store relative path
                rel_path = os.path.relpath(full_path, root_path)

                module_name = rel_path.replace("\\", "/")

                file_map[module_name] = full_path

    return file_map


IGNORED_DIRS = {
    ".git",
    ".github",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".turbo",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
    ".venv",
}

IGNORED_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".lock",
}

IGNORED_FILE_NAMES = {
    ".ds_store",
}


def _should_include_file(filename):
    lower_name = filename.lower()
    if lower_name in IGNORED_FILE_NAMES:
        return False

    return not any(lower_name.endswith(suffix) for suffix in IGNORED_FILE_SUFFIXES)


def scan_project(root_path):
    file_map = {}

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [directory for directory in dirs if directory not in IGNORED_DIRS]

        for file in files:
            if not _should_include_file(file):
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, root_path)
            module_name = rel_path.replace("\\", "/")
            file_map[module_name] = full_path

    return file_map
