import os

def map_services_to_code(services, modules):
    mapping = {}

    for service, config in services.items():
        mapping[service] = []

        # Try to get build/context path from docker-compose
        service_path = None

        if isinstance(config, dict):
            service_path = config.get("build") or config.get("context")

        for module in modules:
            # Normalize paths
            module_path = module.replace("\\", "/")

            if service_path:
                service_path = service_path.replace("\\", "/")

                # Check if module belongs to service directory
                if module_path.startswith(service_path):
                    mapping[service].append(module)
            else:
                # fallback (less reliable)
                if service.lower() in module_path.lower():
                    mapping[service].append(module)

    return mapping