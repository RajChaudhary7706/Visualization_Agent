import os
import stat
import shutil
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.diagram_html import generate_html
from app.parsers.docker_parser import parse_docker_compose
from app.parsers.service_mapper import map_services_to_code
from app.graph.graph_builder import build_full_graph
from app.agents.architecture_agent import generate_architecture_description
from app.agents.risk_agent import detect_risks
from app.services.diagram_service import generate_mermaid
from app.agents.diagram_agent import enhance_diagram

# ✅ NEW CORE SYSTEM
from app.services.file_scanner import scan_project
from app.services.edge_extractor import extract_edges

router = APIRouter()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


class AnalyzeRequest(BaseModel):
    github_url: str
    docker_path: str = None


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

            try:
                subprocess.run(["git", "clone", github_url, clone_dir], check=True)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Git clone failed: {str(e)}")

            path = clone_dir

            if docker_path is None:
                docker_path = os.path.join(clone_dir, "docker-compose.yml")
            elif not os.path.isabs(docker_path):
                docker_path = os.path.join(clone_dir, docker_path)

        else:
            raise HTTPException(status_code=400, detail="Invalid github_url")

        full_path = os.path.abspath(path)
        full_docker_path = os.path.abspath(docker_path)

        print("📁 Project path:", full_path)

        if not os.path.exists(full_path):
            raise HTTPException(status_code=400, detail="Project path not found")

        # -------------------------
        # 2. 🔥 NEW CORE PARSING (FIXED)
        # -------------------------
        try:
            file_map = scan_project(full_path)

            if not file_map:
                raise HTTPException(
                    status_code=400,
                    detail="No supported files found in repo"
                )

            modules = list(file_map.keys())
            edges = extract_edges(file_map)

            print("📁 Sample Modules:", modules[:5])
            print("🔗 Sample Edges:", edges[:5])

        except Exception as e:
            print("⚠️ Parsing error:", e)
            raise HTTPException(status_code=500, detail="Parsing failed")

        print("✅ Total Modules:", len(modules))
        print("✅ Total Edges:", len(edges))

        # -------------------------
        # 3. DOCKER PARSE
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
        try:
            graph = build_full_graph(modules, edges, services, mapping)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Graph build failed: {str(e)}")

        if not graph or len(graph.nodes) == 0:
            raise HTTPException(status_code=400, detail="Graph is empty")

        print("📊 Nodes:", len(graph.nodes))
        print("📊 Edges:", len(graph.edges))

        # -------------------------
        # 5. AI ANALYSIS
        # -------------------------
        try:
            description = generate_architecture_description(graph)
        except Exception as e:
            print("⚠️ Description error:", e)
            description = "Failed to generate description"

        try:
            risks = detect_risks(graph)
        except Exception as e:
            print("⚠️ Risk detection error:", e)
            risks = []

        # -------------------------
        # 6. DIAGRAM
        # -------------------------
        try:
            mermaid = generate_mermaid(graph)
        except Exception as e:
            print("⚠️ Mermaid error:", e)
            mermaid = "graph TD\n  Error --> Diagram"

        try:
            enhanced = enhance_diagram(mermaid)
        except Exception as e:
            print("⚠️ Diagram AI error:", e)
            enhanced = mermaid

        # -------------------------
        # FINAL RESPONSE
        # -------------------------
        return {
            "modules": modules,
            "services": services,
            "mapping": mapping,
            "description": description,
            "risks": risks,
            "diagram_raw": mermaid,
            "diagram_ai": enhanced
        }

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        print("🔥 BACKEND ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# DIAGRAM ENDPOINT
# -------------------------
@router.post("/diagram")
def get_diagram(path: str, docker_path: str):
    try:
        full_path = os.path.join(BASE_DIR, path)

        # ✅ USE NEW CORE HERE ALSO
        file_map = scan_project(full_path)
        modules = list(file_map.keys())
        edges = extract_edges(file_map)

        graph = build_full_graph(modules, edges, {}, {})

        try:
            mermaid = generate_mermaid(graph)
        except:
            mermaid = "graph TD\n  Error --> Diagram"

        try:
            enhanced = enhance_diagram(mermaid)
        except:
            enhanced = mermaid

        html = generate_html(enhanced)

        return {"html": html}

    except Exception as e:
        print("🔥 DIAGRAM ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))