from pathlib import Path


def build_file_tree(modules: list[str]) -> list[dict]:
    tree = {}

    for module in sorted(modules):
        parts = Path(module).parts
        current = tree

        for index, part in enumerate(parts):
            is_file = index == len(parts) - 1

            if part not in current:
                current[part] = {
                    "name": part,
                    "type": "file" if is_file else "folder",
                    "children": {} if not is_file else None,
                }

            if not is_file:
                current = current[part]["children"]

    return _serialize_tree(tree)


def _serialize_tree(node: dict) -> list[dict]:
    items = []

    for name in sorted(node.keys()):
        entry = node[name]

        if entry["type"] == "folder":
            items.append(
                {
                    "name": entry["name"],
                    "type": entry["type"],
                    "children": _serialize_tree(entry["children"]),
                }
            )
        else:
            items.append(
                {
                    "name": entry["name"],
                    "type": entry["type"],
                }
            )

    return items
