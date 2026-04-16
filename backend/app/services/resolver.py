import os

def resolve_import(import_name, file_map):
    import_name = import_name.replace(".", "/")

    for module in file_map.keys():
        if module.endswith(import_name + ".py") or module.endswith(import_name):
            return module

    return None