import os

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
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".exe",
    ".dll",
}

IGNORED_FILE_NAMES = {
    ".ds_store",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java",
    ".json", ".yml", ".yaml", ".toml", ".md", ".txt",
    ".html", ".css", ".scss", ".env", ".xml", ".sql",
    ".sh", ".bat", ".ps1", ".go", ".rs", ".c", ".cpp",
}


def _should_include_file(filename: str) -> bool:
    lower_name = filename.lower()

    if lower_name in IGNORED_FILE_NAMES:
        return False

    if any(lower_name.endswith(suffix) for suffix in IGNORED_FILE_SUFFIXES):
        return False

    ext = os.path.splitext(lower_name)[1]
    return ext in TEXT_EXTENSIONS or "." not in filename


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
