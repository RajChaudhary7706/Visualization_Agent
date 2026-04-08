import yaml

def parse_docker(file_path):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    services = list(data.get("services", {}).keys())
    return services