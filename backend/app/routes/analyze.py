import os
from app.utils.diagram_html import generate_html
from fastapi import APIRouter
from app.parsers.python_parser import parse_python_project
from app.parsers.docker_parser import parse_docker_compose
from app.parsers.service_mapper import map_services_to_code
from app.graph.graph_builder import build_full_graph
from app.agents.architecture_agent import generate_architecture_description
from app.agents.risk_agent import detect_risks
from app.services.diagram_service import generate_mermaid
from app.agents.diagram_agent import enhance_diagram
from app.graph.runtime_graph import build_runtime_graph
from app.agents.comparison_agent import compare_graphs
from app.agents.insight_agent import generate_insights
from backend.app.graph import runtime_graph
from scripts.run_with_trace import run_script

router = APIRouter()

# 👇 THIS IS THE MAIN FIX
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

@router.post("/analyze")
def analyze(path: str, docker_path: str):

    # Convert to absolute paths
    full_path = os.path.join(BASE_DIR, path)
    full_docker_path = os.path.join(BASE_DIR, docker_path)

    print("Project path:", full_path)
    print("Docker path:", full_docker_path)

    modules, edges = parse_python_project(full_path)
    services = parse_docker_compose(full_docker_path)

    mapping = map_services_to_code(services, modules)
    graph = build_full_graph(modules, edges, services, mapping)

    description = generate_architecture_description(graph)
    risks = detect_risks(graph)
    
    mermaid = generate_mermaid(graph)
    enhanced = enhance_diagram(mermaid)
    
    trace = run_script("data/sample_project/app.py")

    runtime_graph = build_runtime_graph(trace)

    comparison = compare_graphs(graph, runtime_graph)

    insights = generate_insights(graph, runtime_graph, risks)

    return {
        "modules": modules,
        "services": services,
        "mapping": mapping,
        "description": description,
        "risks": risks,
        "diagram_raw": mermaid,
        "diagram_ai": enhanced,
        "insights": generate_insights(graph, runtime_graph, risks)
    }
    
@router.post("/diagram")
def get_diagram(path: str, docker_path: str):
    modules, edges = parse_python_project(path)
    services = parse_docker_compose(docker_path)

    mapping = map_services_to_code(services, modules)
    graph = build_full_graph(modules, edges, services, mapping)

    mermaid = generate_mermaid(graph)
    enhanced = enhance_diagram(mermaid)

    html = generate_html(enhanced)

    return {"html": html}
    
