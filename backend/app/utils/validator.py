def validate_services(services):
    if not services:
        raise ValueError("No services found in docker-compose")

    for name, config in services.items():
        if not config.get("image") and not config.get("build"):
            raise ValueError(f"Service {name} missing image/build")