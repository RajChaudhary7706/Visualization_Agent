
# """
# Improved Analyze Endpoint
# Features:
# - Comprehensive input validation
# - Proper error handling
# - Timeout and size limits
# - Request logging
# - Graceful degradation
# """

# import os
# import stat
# import shutil
# import subprocess
# import logging
# from pathlib import Path
# from typing import Optional
# from fastapi import APIRouter, HTTPException, BackgroundTasks
# from pydantic import BaseModel, Field, field_validator

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# router = APIRouter()
# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# # Constants
# MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", 500))
# GIT_CLONE_TIMEOUT = int(os.getenv("GIT_CLONE_TIMEOUT", 300))

# class AnalyzeRequest(BaseModel):
#     """Validated request model with comprehensive checks"""
#     github_url: str = Field(..., description="GitHub repository URL")
#     docker_path: Optional[str] = Field(None, description="Relative path to docker-compose.yml")
    
#     @field_validator("github_url")
#     @classmethod
#     def validate_github_url(cls, v):
#         """Validate GitHub URL format"""
#         if not v:
#             raise ValueError("github_url cannot be empty")
        
#         if not (v.startswith("http://") or v.startswith("https://")):
#             raise ValueError("URL must start with http:// or https://")
        
#         if not ("github.com" in v or "gitlab.com" in v or "gitea" in v.lower()):
#             raise ValueError("Only GitHub, GitLab, and Gitea URLs are supported")
        
#         if len(v) > 500:
#             raise ValueError("URL is too long")
        
#         return v
    
#     @field_validator("docker_path")
#     @classmethod
#     def validate_docker_path(cls, v):
#         """Prevent path traversal attacks"""
#         if v:
#             if v.startswith("/") or v.startswith("\\"):
#                 raise ValueError("docker_path must be relative (not absolute)")
#             if ".." in v:
#                 raise ValueError("docker_path cannot contain '..'")
#             if "~" in v:
#                 raise ValueError("docker_path cannot contain '~'")
#         return v

# def handle_remove_error(func, path, exc_info):
#     """Error handler for directory deletion"""
#     try:
#         os.chmod(path, stat.S_IWRITE)
#         func(path)
#     except Exception as e:
#         logger.error(f"Failed to remove {path}: {e}")

# def get_dir_size(path: str) -> float:
#     """Get directory size in MB"""
#     total = 0
#     try:
#         for dirpath, dirnames, filenames in os.walk(path):
#             for f in filenames:
#                 total += os.path.getsize(os.path.join(dirpath, f))
#     except Exception as e:
#         logger.error(f"Error calculating directory size: {e}")
    
#     return total / (1024 * 1024)

# def safe_git_clone(url: str, dest: str) -> bool:
#     """
#     Safely clone a git repository with timeout and validation
    
#     Args:
#         url: Repository URL
#         dest: Destination directory
        
#     Returns:
#         True if successful, False otherwise
        
#     Raises:
#         HTTPException: On validation failures
#     """
#     try:
#         # Create destination directory
#         os.makedirs(os.path.dirname(dest), exist_ok=True)
        
#         logger.info(f"Cloning {url} to {dest}")
        
#         # Clone with timeout
#         result = subprocess.run(
#             ["git", "clone", url, dest],
#             timeout=GIT_CLONE_TIMEOUT,
#             capture_output=True,
#             text=True
#         )
        
#         if result.returncode != 0:
#             error_msg = result.stderr or result.stdout or "Unknown git error"
#             logger.error(f"Git clone failed: {error_msg}")
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Failed to clone repository: {error_msg[:100]}"
#             )
        
#         # Check repository size
#         size_mb = get_dir_size(dest)
#         logger.info(f"Repository size: {size_mb:.2f} MB")
        
#         if size_mb > MAX_REPO_SIZE_MB:
#             raise HTTPException(
#                 status_code=413,
#                 detail=f"Repository too large ({size_mb:.2f}MB > {MAX_REPO_SIZE_MB}MB)"
#             )
        
#         # Validate repository structure
#         if not os.path.isdir(os.path.join(dest, ".git")):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid or corrupted repository"
#             )
        
#         return True
    
#     except subprocess.TimeoutExpired:
#         logger.error(f"Git clone timed out after {GIT_CLONE_TIMEOUT}s")
#         raise HTTPException(
#             status_code=504,
#             detail=f"Repository clone timed out (>{GIT_CLONE_TIMEOUT}s)"
#         )
    
#     except HTTPException:
#         raise
    
#     except Exception as e:
#         logger.error(f"Unexpected error during clone: {type(e).__name__}: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error cloning repository: {str(e)[:100]}"
#         )

# @router.post("/analyze")
# def analyze(
#     request: AnalyzeRequest,
#     background_tasks: BackgroundTasks
# ):
#     """
#     Analyze a GitHub repository
    
#     Input validation, parsing, graph building, and AI analysis
#     """
#     clone_dir = None
    
#     try:
#         logger.info(f"Starting analysis for {request.github_url}")
        
#         # 1. CLONE REPOSITORY
#         repo_name = request.github_url.rstrip(".git").split("/")[-1]
#         clone_dir = os.path.join(BASE_DIR, "data", "cloned_repos", repo_name)
        
#         # Clean up existing clone
#         if os.path.exists(clone_dir):
#             logger.info(f"Removing existing clone: {clone_dir}")
#             shutil.rmtree(clone_dir, onerror=handle_remove_error)
        
#         # Clone repository
#         safe_git_clone(request.github_url, clone_dir)
        
#         # 2. DETERMINE DOCKER COMPOSE PATH
#         if request.docker_path:
#             docker_path = os.path.join(clone_dir, request.docker_path)
#         else:
#             docker_path = os.path.join(clone_dir, "docker-compose.yml")
        
#         logger.info(f"Looking for docker-compose at {docker_path}")
        
#         # 3. PARSE PROJECT
#         try:
#             from app.services.file_scanner import scan_project
#             from app.services.edge_extractor import extract_edges
            
#             file_map = scan_project(clone_dir)
            
#             if not file_map:
#                 logger.warning("No supported files found")
#                 raise HTTPException(
#                     status_code=400,
#                     detail="No supported source files found in repository"
#                 )
            
#             logger.info(f"Found {len(file_map)} source files")
            
#             # Extract edges with error handling
#             try:
#                 edges = extract_edges(file_map)
#                 logger.info(f"Extracted {len(edges)} dependencies")
#             except Exception as e:
#                 logger.error(f"Edge extraction error: {e}", exc_info=True)
#                 edges = []
            
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Parsing error: {type(e).__name__}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Failed to parse project: {str(e)[:100]}"
#             )
        
#         # 4. PARSE DOCKER COMPOSE
#         services = {}
#         mapping = {}
        
#         if os.path.exists(docker_path):
#             try:
#                 from app.parsers.docker_parser import parse_docker_compose
#                 from app.parsers.service_mapper import map_services_to_code
                
#                 services = parse_docker_compose(docker_path)
#                 mapping = map_services_to_code(services, list(file_map.keys()))
#                 logger.info(f"Found {len(services)} Docker services")
            
#             except Exception as e:
#                 logger.warning(f"Docker parsing error (non-critical): {e}")
#                 # Don't fail - docker is optional
#         else:
#             logger.info("No docker-compose.yml found (optional)")
        
#         # 5. BUILD GRAPH
#         try:
#             from app.graph.graph_builder import build_full_graph
            
#             graph = build_full_graph(list(file_map.keys()), edges, services, mapping)
            
#             if not graph or len(graph.nodes) == 0:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Failed to build system graph"
#                 )
            
#             logger.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        
#         except HTTPException:
#             raise
#         except Exception as e:
#             logger.error(f"Graph building error: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Failed to build graph: {str(e)[:100]}"
#             )
        
#         # 6. AI ANALYSIS (with graceful fallback)
#         description = None
#         risks = None
#         mermaid = None
#         enhanced = None
        
#         # Architecture description
#         try:
#             from app.agents.architecture_agent import generate_architecture_description
#             description = generate_architecture_description(graph)
#             logger.info("Generated architecture description")
#         except Exception as e:
#             logger.error(f"Architecture generation error: {e}", exc_info=True)
#             description = f"Failed to generate description: {str(e)[:50]}"
        
#         # Risk detection
#         try:
#             from app.agents.risk_agent import detect_risks
#             risks = detect_risks(graph)
#             logger.info("Completed risk analysis")
#         except Exception as e:
#             logger.error(f"Risk detection error: {e}", exc_info=True)
#             risks = {"error": f"Risk detection failed: {str(e)[:50]}"}
        
#         # Diagram generation
#         try:
#             from app.services.diagram_service import generate_mermaid
#             mermaid = generate_mermaid(graph)
#             logger.info("Generated Mermaid diagram")
#         except Exception as e:
#             logger.error(f"Diagram generation error: {e}", exc_info=True)
#             mermaid = "graph TD\n  Error --> CouldNotGenerateDiagram"
        
#         # Preserve the full raw graph instead of letting an LLM compress it.
#         enhanced = mermaid
        
#         # 7. RETURN RESULTS
#         response = {
#             "status": "success",
#             "repo_path": clone_dir,
#             "modules": list(file_map.keys()),
#             "module_count": len(file_map),
#             "edges": edges,
#             "edge_count": len(edges),
#             "services": services,
#             "services_count": len(services),
#             "mapping": mapping,
#             "graph_nodes": len(graph.nodes),
#             "graph_edges": len(graph.edges),
#             "graph_data": {
#                 "nodes": [
#                     {"id": node, **data}
#                     for node, data in graph.nodes(data=True)
#                 ],
#                 "edges": [
#                     {"source": src, "target": dst, **data}
#                     for src, dst, data in graph.edges(data=True)
#                 ],
#             },
#             "description": description,
#             "risks": risks,
#             "diagram_raw": mermaid,
#             "diagram_ai": enhanced
#         }
        
#         logger.info(f"Analysis completed successfully for {repo_name}")
        
#         # Schedule cleanup in background
#         background_tasks.add_task(lambda: _cleanup_repo(clone_dir))
        
#         return response
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Unexpected error: {str(e)[:100]}"
#         )

# def _cleanup_repo(clone_dir: str):
#     """Clean up cloned repository (run in background)"""
#     try:
#         if os.path.exists(clone_dir):
#             logger.info(f"Cleaning up {clone_dir}")
#             shutil.rmtree(clone_dir, onerror=handle_remove_error)
#     except Exception as e:
#         logger.error(f"Cleanup error: {e}")

# @router.post("/analyze/dry-run")
# def analyze_dry_run(request: AnalyzeRequest):
#     """
#     Validate request without running full analysis
#     Useful for testing before actual analysis
#     """
#     try:
#         logger.info(f"Dry run for {request.github_url}")
#         return {
#             "status": "valid",
#             "message": "Request is valid and ready for analysis",
#             "github_url": request.github_url,
#             "docker_path": request.docker_path or "docker-compose.yml"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


"""
Improved Analyze Endpoint
Features:
- Comprehensive input validation
- Proper error handling
- Timeout and size limits
- Request logging
- Graceful degradation
"""

import os
import stat
import shutil
import subprocess
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Constants
MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", 500))
GIT_CLONE_TIMEOUT = int(os.getenv("GIT_CLONE_TIMEOUT", 300))


class AnalyzeRequest(BaseModel):
    """Validated request model with comprehensive checks"""
    github_url: str = Field(..., description="GitHub repository URL")
    docker_path: Optional[str] = Field(None, description="Relative path to docker-compose.yml")

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v):
        """Validate GitHub URL format"""
        if not v:
            raise ValueError("github_url cannot be empty")

        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")

        if not ("github.com" in v or "gitlab.com" in v or "gitea" in v.lower()):
            raise ValueError("Only GitHub, GitLab, and Gitea URLs are supported")

        if len(v) > 500:
            raise ValueError("URL is too long")

        return v

    @field_validator("docker_path")
    @classmethod
    def validate_docker_path(cls, v):
        """Prevent path traversal attacks"""
        if v:
            if v.startswith("/") or v.startswith("\\"):
                raise ValueError("docker_path must be relative (not absolute)")
            if ".." in v:
                raise ValueError("docker_path cannot contain '..'")
            if "~" in v:
                raise ValueError("docker_path cannot contain '~'")
        return v


def handle_remove_error(func, path, exc_info):
    """Error handler for directory deletion"""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        logger.error(f"Failed to remove {path}: {e}")


def get_dir_size(path: str) -> float:
    """Get directory size in MB"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                total += os.path.getsize(os.path.join(dirpath, f))
    except Exception as e:
        logger.error(f"Error calculating directory size: {e}")

    return total / (1024 * 1024)


def safe_git_clone(url: str, dest: str) -> bool:
    """
    Safely clone a git repository with timeout and validation
    """
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        logger.info(f"Cloning {url} to {dest}")

        result = subprocess.run(
            ["git", "clone", url, dest],
            timeout=GIT_CLONE_TIMEOUT,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown git error"
            logger.error(f"Git clone failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to clone repository: {error_msg[:100]}"
            )

        size_mb = get_dir_size(dest)
        logger.info(f"Repository size: {size_mb:.2f} MB")

        if size_mb > MAX_REPO_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"Repository too large ({size_mb:.2f}MB > {MAX_REPO_SIZE_MB}MB)"
            )

        if not os.path.isdir(os.path.join(dest, ".git")):
            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted repository"
            )

        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Git clone timed out after {GIT_CLONE_TIMEOUT}s")
        raise HTTPException(
            status_code=504,
            detail=f"Repository clone timed out (>{GIT_CLONE_TIMEOUT}s)"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error during clone: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cloning repository: {str(e)[:100]}"
        )


@router.post("/analyze")
def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze a GitHub repository
    """
    clone_dir = None

    try:
        logger.info(f"Starting analysis for {request.github_url}")

        # 1. CLONE REPOSITORY
        repo_name = request.github_url.rstrip(".git").split("/")[-1]
        clone_dir = os.path.join(BASE_DIR, "data", "cloned_repos", repo_name)

        if os.path.exists(clone_dir):
            logger.info(f"Removing existing clone: {clone_dir}")
            shutil.rmtree(clone_dir, onerror=handle_remove_error)

        safe_git_clone(request.github_url, clone_dir)

        # 2. DETERMINE DOCKER COMPOSE PATH
        if request.docker_path:
            docker_path = os.path.join(clone_dir, request.docker_path)
        else:
            docker_path = os.path.join(clone_dir, "docker-compose.yml")

        logger.info(f"Looking for docker-compose at {docker_path}")

        # 3. PARSE PROJECT
        try:
            from app.services.file_scanner import scan_project
            from app.services.edge_extractor import extract_edges
            from app.services.code_structure_extractor import extract_code_structures
            from app.services.tree_builder import build_file_tree

            file_map = scan_project(clone_dir)

            if not file_map:
                logger.warning("No supported files found")
                raise HTTPException(
                    status_code=400,
                    detail="No supported source files found in repository"
                )

            logger.info(f"Found {len(file_map)} source files")

            try:
                file_structures = extract_code_structures(file_map)
                logger.info(f"Extracted code structures for {len(file_structures)} files")
            except Exception as e:
                logger.error(f"Code structure extraction error: {e}", exc_info=True)
                file_structures = {}

            try:
                file_tree = build_file_tree(list(file_map.keys()))
                logger.info("Built file tree successfully")
            except Exception as e:
                logger.error(f"File tree build error: {e}", exc_info=True)
                file_tree = []

            try:
                edges = extract_edges(file_map)
                logger.info(f"Extracted {len(edges)} dependencies")
            except Exception as e:
                logger.error(f"Edge extraction error: {e}", exc_info=True)
                edges = []

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Parsing error: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse project: {str(e)[:100]}"
            )

        # 4. PARSE DOCKER COMPOSE
        services = {}
        mapping = {}

        if os.path.exists(docker_path):
            try:
                from app.parsers.docker_parser import parse_docker_compose
                from app.parsers.service_mapper import map_services_to_code

                services = parse_docker_compose(docker_path)
                mapping = map_services_to_code(services, list(file_map.keys()))
                logger.info(f"Found {len(services)} Docker services")

            except Exception as e:
                logger.warning(f"Docker parsing error (non-critical): {e}")
        else:
            logger.info("No docker-compose.yml found (optional)")

        # 5. BUILD GRAPH
        try:
            from app.graph.graph_builder import build_full_graph

            graph = build_full_graph(list(file_map.keys()), edges, services, mapping)

            if not graph or len(graph.nodes) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to build system graph"
                )

            logger.info(f"Built graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Graph building error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to build graph: {str(e)[:100]}"
            )

        # 6. AI ANALYSIS
        description = None
        risks = None
        mermaid = None
        enhanced = None

        try:
            from app.agents.architecture_agent import generate_architecture_description
            description = generate_architecture_description(graph)
            logger.info("Generated architecture description")
        except Exception as e:
            logger.error(f"Architecture generation error: {e}", exc_info=True)
            description = f"Failed to generate description: {str(e)[:50]}"

        try:
            from app.agents.risk_agent import detect_risks
            risks = detect_risks(graph)
            logger.info("Completed risk analysis")
        except Exception as e:
            logger.error(f"Risk detection error: {e}", exc_info=True)
            risks = {"error": f"Risk detection failed: {str(e)[:50]}"}

        try:
            from app.services.diagram_service import generate_mermaid
            mermaid = generate_mermaid(graph)
            logger.info("Generated Mermaid diagram")
        except Exception as e:
            logger.error(f"Diagram generation error: {e}", exc_info=True)
            mermaid = "graph TD\n  Error --> CouldNotGenerateDiagram"

        enhanced = mermaid

        # 7. RETURN RESULTS
        response = {
            "status": "success",
            "repo_path": clone_dir,
            "modules": list(file_map.keys()),
            "module_count": len(file_map),
            "file_tree": file_tree,
            "file_structures": file_structures,
            "edges": edges,
            "edge_count": len(edges),
            "services": services,
            "services_count": len(services),
            "mapping": mapping,
            "graph_nodes": len(graph.nodes),
            "graph_edges": len(graph.edges),
            "graph_data": {
                "nodes": [
                    {"id": node, **data}
                    for node, data in graph.nodes(data=True)
                ],
                "edges": [
                    {"source": src, "target": dst, **data}
                    for src, dst, data in graph.edges(data=True)
                ],
            },
            "description": description,
            "risks": risks,
            "diagram_raw": mermaid,
            "diagram_ai": enhanced
        }

        logger.info(f"Analysis completed successfully for {repo_name}")

        background_tasks.add_task(lambda: _cleanup_repo(clone_dir))

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)[:100]}"
        )


def _cleanup_repo(clone_dir: str):
    """Clean up cloned repository (run in background)"""
    try:
        if os.path.exists(clone_dir):
            logger.info(f"Cleaning up {clone_dir}")
            shutil.rmtree(clone_dir, onerror=handle_remove_error)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


@router.post("/analyze/dry-run")
def analyze_dry_run(request: AnalyzeRequest):
    """
    Validate request without running full analysis
    Useful for testing before actual analysis
    """
    try:
        logger.info(f"Dry run for {request.github_url}")
        return {
            "status": "valid",
            "message": "Request is valid and ready for analysis",
            "github_url": request.github_url,
            "docker_path": request.docker_path or "docker-compose.yml"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
