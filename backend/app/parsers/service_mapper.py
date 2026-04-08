def map_services_to_code(services, modules):
    mapping = {}

    for service in services:
        mapping[service] = []

        for module in modules:
            # simple logic: match by name
            if service in module.lower():
                mapping[service].append(module)

    return mapping