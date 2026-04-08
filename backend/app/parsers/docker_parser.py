import yaml
import os

def parse_docker_compose(file_path):
    print("DOCKER PATH:", file_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Docker file not found:{file_path}")

    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Invalid YAML: {str(e)}")

    services = {}

    for name, config in data.get("services", {}).items():
        services[name] = {
            "image": config.get("image"),
            "build": config.get("build"),
            "ports": config.get("ports", []),
            "depends_on": config.get("depends_on", []),
            "environment": config.get("environment", {})
        }

    return services