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