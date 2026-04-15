# import os
# import stat
# import shutil
# import subprocess
# from fastapi import APIRouter, Body
# from fastapi import HTTPException
# from pydantic import BaseModel

# from app.utils.diagram_html import generate_html
# from app.parsers.python_parser import parse_python_project
# from app.parsers.docker_parser import parse_docker_compose
# from app.parsers.service_mapper import map_services_to_code
# from app.graph.graph_builder import build_full_graph
# from app.agents.architecture_agent import generate_architecture_description
# from app.agents.risk_agent import detect_risks
# from app.services.diagram_service import generate_mermaid
# from app.agents.diagram_agent import enhance_diagram
# from app.graph.runtime_graph import build_runtime_graph
# from app.agents.comparison_agent import compare_graphs
# from app.agents.insight_agent import generate_insights
# from app.scripts.run_with_trace import run_script

# router = APIRouter()

# # Base directory (project root)
# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


# # Define request model for frontend compatibility
# class AnalyzeRequest(BaseModel):
#     github_url: str
#     docker_path: str = None


# @router.post("/analyze")
# def analyze(request: AnalyzeRequest):
#     github_url = request.github_url
#     docker_path = request.docker_path

#     # Clone repo if github_url is a link
#     if github_url.startswith("http://") or github_url.startswith("https://"):
#         repo_name = github_url.rstrip(".git").split("/")[-1]
#         clone_dir = os.path.join(BASE_DIR, "data", "cloned_repos", repo_name)

#         def on_rm_error(func, path, exc_info):
#             # Change the file to be writable and try again
#             os.chmod(path, stat.S_IWRITE)
#             func(path)

#         if os.path.exists(clone_dir):
#             shutil.rmtree(clone_dir, onerror=on_rm_error)
#         try:
#             subprocess.run(["git", "clone", github_url, clone_dir], check=True)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Failed to clone repo: {e}")
#         path = clone_dir
#         if docker_path is None:
#             docker_path = os.path.join(clone_dir, "docker-compose.yml")
#         elif not os.path.isabs(docker_path):
#             docker_path = os.path.join(clone_dir, docker_path)
#     elif github_url.endswith("sample_project"):
#         path = os.path.join("data", "sample_project")
#         if docker_path is None:
#             docker_path = os.path.join(path, "docker-compose.yml")
#         elif not os.path.isabs(docker_path):
#             docker_path = os.path.join(path, docker_path)
#     else:
#         raise HTTPException(status_code=400, detail="Invalid github_url or not supported.")

#     full_path = os.path.abspath(path)
#     full_docker_path = os.path.abspath(docker_path)

#     print("Project path:", full_path)
#     print("Docker path:", full_docker_path)

#     # Check if main script exists for runtime tracing
#     main_script = None
#     for candidate in ["app.py", "main.py"]:
#         candidate_path = os.path.join(full_path, candidate)
#         if os.path.isfile(candidate_path):
#             main_script = candidate_path
#             break

#     # Parsing

#     if not os.path.exists(full_path):
#         raise HTTPException(status_code=400, detail=f"Project path not found: {full_path}")

#     modules, edges = parse_python_project(full_path)

#     # If docker-compose.yml exists, parse services, else use empty
#     if os.path.exists(full_docker_path):
#         services = parse_docker_compose(full_docker_path)
#         mapping = map_services_to_code(services, modules)
#     else:
#         services = {}
#         mapping = {}

#     graph = build_full_graph(modules, edges, services, mapping)

#     description = generate_architecture_description(graph)
#     risks = detect_risks(graph)
#     mermaid = generate_mermaid(graph)
#     enhanced = enhance_diagram(mermaid)

#     # Runtime tracing (optional)
#     if main_script:
#         trace = run_script(main_script)
#         runtime_graph = build_runtime_graph(trace)
#         comparison = compare_graphs(graph, runtime_graph)
#         insights = generate_insights(graph, runtime_graph, risks)
#     else:
#         runtime_graph = None
#         comparison = None
#         insights = None

#     return {
#         "modules": modules,
#         "services": services,
#         "mapping": mapping,
#         "description": description,
#         "risks": risks,
#         "diagram_raw": mermaid,
#         "diagram_ai": enhanced,
#         "comparison": comparison,
#         "insights": insights
#     }


# @router.post("/diagram")
# def get_diagram(path: str, docker_path: str):

#     full_path = os.path.join(BASE_DIR, path)
#     full_docker_path = os.path.join(BASE_DIR, docker_path)

#     modules, edges = parse_python_project(full_path)
#     services = parse_docker_compose(full_docker_path)

#     mapping = map_services_to_code(services, modules)
#     graph = build_full_graph(modules, edges, services, mapping)

#     mermaid = generate_mermaid(graph)
#     enhanced = enhance_diagram(mermaid)

#     html = generate_html(enhanced)

#     return {"html": html}


import os
import stat
import shutil
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.diagram_html import generate_html
from app.parsers.python_parser import parse_python_project
from app.parsers.docker_parser import parse_docker_compose
from app.parsers.service_mapper import map_services_to_code
from app.graph.graph_builder import build_full_graph
from app.agents.architecture_agent import generate_architecture_description
from app.agents.risk_agent import detect_risks
from app.services.diagram_service import generate_mermaid
from app.agents.diagram_agent import enhance_diagram
from app.parsers.js_parser import parse_js_project

router = APIRouter()

# Base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


# Request model
class AnalyzeRequest(BaseModel):
    github_url: str
    docker_path: str = None


# =========================
# 🔥 ANALYZE API (FIXED)
# =========================
@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        github_url = request.github_url
        docker_path = request.docker_path

        # -------------------------
        # 1. CLONE REPO
        # -------------------------
        if github_url.startswith("http://") or github_url.startswith("https://"):
            repo_name = github_url.rstrip(".git").split("/")[-1]
            clone_dir = os.path.join(BASE_DIR, "data", "cloned_repos", repo_name)

            def on_rm_error(func, path, exc_info):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir, onerror=on_rm_error)

            subprocess.run(["git", "clone", github_url, clone_dir], check=True)
            path = clone_dir

            # docker path
            if docker_path is None:
                docker_path = os.path.join(clone_dir, "docker-compose.yml")
            elif not os.path.isabs(docker_path):
                docker_path = os.path.join(clone_dir, docker_path)

        else:
            raise HTTPException(status_code=400, detail="Invalid github_url")

        full_path = os.path.abspath(path)
        full_docker_path = os.path.abspath(docker_path)

        print("📁 Project path:", full_path)

        # -------------------------
        # 2. PARSE PYTHON
        # -------------------------
        if not os.path.exists(full_path):
            raise HTTPException(status_code=400, detail="Project path not found")

        modules_py, edges_py = parse_python_project(full_path)
        modules_js, edges_js = parse_js_project(full_path)
        modules = modules_py + modules_js
        edges = edges_py + edges_js

        print("✅ Modules:", len(modules))
        print("✅ Edges:", len(edges))
        print("🐍 Python Modules:", len(modules_py))
        print("🟨 JS Modules:", len(modules_js))

        # -------------------------
        # 3. SAFE DOCKER PARSE
        # -------------------------
        if os.path.exists(full_docker_path):
            try:
                services = parse_docker_compose(full_docker_path)
                mapping = map_services_to_code(services, modules)
            except Exception as e:
                print("⚠️ Docker parse error:", e)
                services = {}
                mapping = {}
        else:
            print("⚠️ No docker-compose.yml found")
            services = {}
            mapping = {}

        # -------------------------
        # 4. BUILD GRAPH
        # -------------------------
        graph = build_full_graph(modules, edges, services, mapping)

        print("📊 Nodes:", len(graph.nodes))
        print("📊 Edges:", len(graph.edges))

        # -------------------------
        # 5. AI ANALYSIS
        # -------------------------
        description = generate_architecture_description(graph)
        risks = detect_risks(graph)

        # -------------------------
        # 6. DIAGRAM
        # -------------------------
        mermaid = generate_mermaid(graph)
        enhanced = enhance_diagram(mermaid)

        # -------------------------
        # ❌ DISABLED (for stability)
        # -------------------------
        runtime_graph = None
        comparison = None
        insights = None

        # -------------------------
        # RESPONSE
        # -------------------------
        return {
            "modules": modules,
            "services": services,
            "mapping": mapping,
            "description": description,
            "risks": risks,
            "diagram_raw": mermaid,
            "diagram_ai": enhanced,
            "comparison": comparison,
            "insights": insights
        }

    except Exception as e:
        print("🔥 BACKEND ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# DIAGRAM API
# =========================
@router.post("/diagram")
def get_diagram(path: str, docker_path: str):
    try:
        full_path = os.path.join(BASE_DIR, path)
        full_docker_path = os.path.join(BASE_DIR, docker_path)

        modules, edges = parse_python_project(full_path)

        if os.path.exists(full_docker_path):
            try:
                services = parse_docker_compose(full_docker_path)
            except:
                services = {}
        else:
            services = {}

        mapping = map_services_to_code(services, modules)
        graph = build_full_graph(modules, edges, services, mapping)

        mermaid = generate_mermaid(graph)
        enhanced = enhance_diagram(mermaid)

        html = generate_html(enhanced)

        return {"html": html}

    except Exception as e:
        print("🔥 DIAGRAM ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))