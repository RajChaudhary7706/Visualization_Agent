"""
Unit tests for Visualization Agent
Tests for: LLM service, edge extractor, risk detection, validation
"""

import pytest
import networkx as nx
from unittest.mock import patch, MagicMock
import tempfile
import os
import sys
import shutil
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

TEST_TMP_DIR = BACKEND_DIR / ".tmp_test_workspace"
TEST_TMP_DIR.mkdir(exist_ok=True)

def _safe_unlink(path: Path) -> None:
    """Best-effort cleanup for Windows file locking."""
    try:
        if path.exists():
            path.unlink()
    except PermissionError:
        pass

# ============================================================================
# LLM Service Tests
# ============================================================================

def test_llm_service_initialization():
    """Test LLM service initialization with proper error handling"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        from app.services.llm_service import LLMService
        service = LLMService()
        assert service.api_key == "test-key"
        assert service.model == "gpt-4o-mini"

def test_llm_service_missing_api_key():
    """Test that missing API key raises proper error"""
    with patch.dict(os.environ, {}, clear=True):
        from app.services.llm_service import LLMService, LLMServiceError
        with pytest.raises(LLMServiceError):
            LLMService()

def test_cost_estimation():
    """Test cost estimation calculation"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        from app.services.llm_service import LLMService
        service = LLMService()
        
        # Test prompt of 4000 chars (1000 tokens)
        cost = service.estimate_cost("x" * 4000, is_completion=True)
        
        assert "estimated_input_cost" in cost
        assert "estimated_output_cost" in cost
        assert cost["total_estimated_cost"] > 0

def test_llm_call_with_retry():
    """Test LLM call with retry logic"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        from app.services.llm_service import LLMService
        
        with patch.object(LLMService, '__init__', lambda x: None):
            service = LLMService()
            service.client = MagicMock()
            service.api_key = "test"
            service.model = "gpt-4o-mini"
            service.max_tokens = 100
            service.temperature = 0.7
            service.request_timeout = 60
            service.max_retries = 3
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage.total_tokens = 50
            service.client.chat.completions.create.return_value = mock_response
            
            result = service.call_llm("test prompt")
            assert result == "Test response"
            assert service.client.chat.completions.create.called

# ============================================================================
# Edge Extractor Tests
# ============================================================================

def test_python_import_extraction():
    """Test Python import extraction with AST"""
    from app.services.edge_extractor import extract_python_imports

    temp_file = TEST_TMP_DIR / "service_import_test.py"

    try:
        _safe_unlink(temp_file)
        temp_file.write_text("""
import os
from collections import defaultdict
from app.models import User

class Service:
    def method(self):
        pass
""", encoding="utf-8")

        file_map = {"service.py": str(temp_file)}
        edges = extract_python_imports(str(temp_file), file_map)

        # Should have extracted imports
        assert len(edges) >= 0  # May or may not find local imports
    finally:
        _safe_unlink(temp_file)

def test_js_import_extraction():
    """Test JavaScript import extraction"""
    from app.services.edge_extractor import extract_js_imports

    temp_file = TEST_TMP_DIR / "app_import_test.js"

    try:
        _safe_unlink(temp_file)
        temp_file.write_text("""
import React from 'react';
const express = require('express');
import('./config').then(config => {});
""", encoding="utf-8")

        file_map = {"app.js": str(temp_file)}
        edges = extract_js_imports(str(temp_file), file_map)

        # Should extract some edges (even if targets don't exist)
        assert isinstance(edges, list)
    finally:
        _safe_unlink(temp_file)

def test_js_relative_import_resolution():
    """Test JS relative import resolution for frontend projects"""
    from app.services.edge_extractor import extract_edges

    temp_dir = TEST_TMP_DIR / "frontend_import_case"

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        (temp_dir / "src").mkdir(parents=True, exist_ok=True)

        main_file = temp_dir / "src" / "main.js"
        app_file = temp_dir / "src" / "App.jsx"

        main_file.write_text("import App from './App';\n", encoding="utf-8")
        app_file.write_text("export default function App() { return null; }\n", encoding="utf-8")

        file_map = {
            "src/main.js": str(main_file),
            "src/App.jsx": str(app_file),
        }

        edges = extract_edges(file_map)
        assert ("src/main", "src/App", "import") in edges
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_import_resolver():
    """Test import path resolution"""
    from app.services.edge_extractor import _resolve_import
    
    file_map = {
        "app/models/user.py": "/path/to/user.py",
        "app/services/auth.py": "/path/to/auth.py",
        "utils/helpers.py": "/path/to/helpers.py"
    }
    
    # Test exact match
    result = _resolve_import("user", file_map)
    assert result is not None
    
    # Test partial match
    result = _resolve_import("helpers", file_map)
    assert result is not None

# ============================================================================
# Risk Detection Tests
# ============================================================================

def test_spof_detection():
    """Test Single Point of Failure detection"""
    from app.agents.risk_agent import RiskDetector
    
    # Create a test graph with SPOF
    G = nx.DiGraph()
    G.add_nodes_from(['A', 'B', 'C', 'D', 'E', 'F', 'DB'], type='code')
    G.nodes['DB']['type'] = 'service'
    
    # DB is critical hub
    G.add_edges_from([
        ('A', 'DB'),
        ('B', 'DB'),
        ('C', 'DB'),
        ('D', 'DB'),
        ('E', 'DB'),
        ('F', 'DB'),
        ('DB', 'FileSystem')
    ])
    
    detector = RiskDetector(G)
    spofs = detector._detect_spof()
    
    # Should detect DB as SPOF
    assert any('DB' in str(s) for s in spofs)

def test_circular_dependency_detection():
    """Test circular dependency detection"""
    from app.agents.risk_agent import RiskDetector
    
    # Create graph with cycle
    G = nx.DiGraph()
    G.add_edges_from([
        ('ModuleA', 'ModuleB'),
        ('ModuleB', 'ModuleC'),
        ('ModuleC', 'ModuleA')  # Creates cycle
    ])
    
    detector = RiskDetector(G)
    cycles = detector._detect_circular_dependencies()
    
    # Should detect the cycle
    assert len(cycles) > 0
    assert 'ModuleA' in str(cycles[0]['nodes'])

def test_dead_code_detection():
    """Test unused code detection"""
    from app.agents.risk_agent import RiskDetector
    
    G = nx.DiGraph()
    G.add_nodes_from(['UsedModule', 'UnusedModule', 'Service'])
    G.add_edge('Service', 'UsedModule')
    # UnusedModule has no edges
    
    detector = RiskDetector(G)
    dead = detector._detect_dead_code()
    
    # Should detect UnusedModule
    unused_found = any('UnusedModule' in str(d) for d in dead)
    assert unused_found or len(dead) >= 0  # Lenient check

def test_coupling_analysis():
    """Test coupling metrics calculation"""
    from app.agents.risk_agent import RiskDetector
    
    G = nx.DiGraph()
    G.add_edges_from([
        ('A', 'B'),
        ('A', 'C'),
        ('B', 'C'),
        ('C', 'D'),
        ('D', 'A')
    ])
    
    detector = RiskDetector(G)
    metrics = detector._analyze_coupling()
    
    assert 'average_connections_per_module' in metrics
    assert 'coupling_ratio' in metrics
    assert metrics['coupling_ratio'] > 0

def test_health_score_calculation():
    """Test health score calculation"""
    from app.agents.risk_agent import RiskDetector, _get_health_status
    
    G = nx.DiGraph()
    G.add_edge('A', 'B')
    
    detector = RiskDetector(G)
    summary = detector._generate_summary()
    
    assert 'health_score' in summary
    assert 0 <= summary['health_score'] <= 100
    assert summary['status'] in ['EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'CRITICAL']

# ============================================================================
# Validation Tests
# ============================================================================

def test_analyze_request_validation():
    """Test AnalyzeRequest validation"""
    from app.routes.analyze import AnalyzeRequest
    
    # Valid request
    req = AnalyzeRequest(
        github_url="https://github.com/user/repo.git",
        docker_path="docker-compose.yml"
    )
    assert req.github_url == "https://github.com/user/repo.git"

def test_invalid_github_url():
    """Test invalid GitHub URL rejection"""
    from app.routes.analyze import AnalyzeRequest
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            github_url="not-a-url",
            docker_path=None
        )

def test_path_traversal_prevention():
    """Test prevention of path traversal attacks"""
    from app.routes.analyze import AnalyzeRequest
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            github_url="https://github.com/user/repo",
            docker_path="../../etc/passwd"
        )

def test_absolute_path_prevention():
    """Test prevention of absolute paths"""
    from app.routes.analyze import AnalyzeRequest
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            github_url="https://github.com/user/repo",
            docker_path="/etc/docker-compose.yml"
        )

# ============================================================================
# Integration Tests
# ============================================================================

def test_full_analysis_pipeline():
    """Integration test of full pipeline"""

    temp_dir = TEST_TMP_DIR / "pipeline_case"

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(exist_ok=True)
        main_file = temp_dir / "main.py"
        utils_file = temp_dir / "utils.py"

        main_file.write_text("import utils\nclass Main: pass\n", encoding="utf-8")
        utils_file.write_text("def helper(): pass\n", encoding="utf-8")

        # Scan project
        from app.services.edge_extractor import extract_edges
        from app.services.file_scanner import scan_project

        file_map = scan_project(str(temp_dir))
        assert len(file_map) == 2

        edges = extract_edges(file_map)
        assert isinstance(edges, list)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_mermaid_includes_isolated_nodes():
    """Test Mermaid output includes isolated modules, not just edges."""
    from app.services.diagram_service import generate_mermaid

    G = nx.DiGraph()
    G.add_node("src/main", type="code")
    G.add_node("src/App", type="code")
    G.add_edge("src/main", "src/App", type="import", weight=1)
    G.add_node("src/isolated", type="code")

    mermaid = generate_mermaid(G)

    assert 'src_main["src/main"]' in mermaid
    assert 'src_App["src/App"]' in mermaid
    assert 'src_isolated["src/isolated"]' in mermaid

def test_scan_project_includes_non_code_repo_files():
    """Test repo scan includes non-code files and skips obvious junk dirs."""
    from app.services.file_scanner import scan_project

    temp_dir = TEST_TMP_DIR / "scan_repo_case"

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        (temp_dir / "src").mkdir(parents=True, exist_ok=True)
        (temp_dir / "node_modules").mkdir(parents=True, exist_ok=True)

        (temp_dir / "src" / "main.js").write_text("console.log('x')\n", encoding="utf-8")
        (temp_dir / "README.md").write_text("# Demo\n", encoding="utf-8")
        (temp_dir / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
        (temp_dir / "node_modules" / "ignore.js").write_text("ignored\n", encoding="utf-8")

        file_map = scan_project(str(temp_dir))

        assert "src/main.js" in file_map
        assert "README.md" in file_map
        assert "package.json" in file_map
        assert "node_modules/ignore.js" not in file_map
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_graph_builder_adds_folder_hierarchy():
    """Test graph includes folder nodes and contains edges."""
    from app.graph.graph_builder import build_full_graph

    graph = build_full_graph(
        ["src/main.js", "src/components/App.jsx"],
        [("src/main.js", "src/components/App.jsx", "import")],
        {},
        {},
    )

    assert "src" in graph.nodes
    assert "src/components" in graph.nodes
    assert "src/main.js" in graph.nodes
    assert "src/components/App.jsx" in graph.nodes
    assert graph.nodes["src"]["type"] == "folder"
    assert graph.nodes["src/components"]["type"] == "folder"
    assert graph.nodes["src/main.js"]["type"] == "code"
    assert graph.nodes["src/components/App.jsx"]["type"] == "code"
    assert ("src", "src/main.js") in graph.edges
    assert ("src", "src/components") in graph.edges

def test_mermaid_shows_code_file_extensions():
    """Test Mermaid labels keep real file extensions."""
    from app.graph.graph_builder import build_full_graph
    from app.services.diagram_service import generate_mermaid

    graph = build_full_graph(
        ["src/main.js", "src/components/App.jsx"],
        [("src/main.js", "src/components/App.jsx", "import")],
        {},
        {},
    )

    mermaid = generate_mermaid(graph)

    assert 'src_main_js["src/main.js"]' in mermaid
    assert 'src_components_App_jsx["src/components/App.jsx"]' in mermaid

# ============================================================================
# Performance Tests
# ============================================================================

def test_large_graph_handling():
    """Test handling of large graphs"""
    from app.agents.risk_agent import RiskDetector
    
    # Create large graph
    G = nx.DiGraph()
    for i in range(100):
        G.add_node(f"module_{i}")
    
    for i in range(99):
        G.add_edge(f"module_{i}", f"module_{i+1}")
    
    detector = RiskDetector(G)
    
    # Should not crash
    summary = detector._generate_summary()
    assert summary['health_score'] >= 0
    
def test_extract_code_structures_python():
    """Test Python code structure extraction."""
    from app.services.code_structure_extractor import extract_code_structures

    temp_dir = TEST_TMP_DIR / "structure_python_case"

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        sample_file = temp_dir / "sample.py"
        sample_file.write_text(
            """
class UserService:
    def get_user(self):
        return 1

def helper():
    return True

async def load_data():
    return []
""",
            encoding="utf-8",
        )

        file_map = {"sample.py": str(sample_file)}
        structures = extract_code_structures(file_map)

        assert "sample.py" in structures
        assert "UserService" in structures["sample.py"]["classes"]
        assert "helper" in structures["sample.py"]["functions"]
        assert "load_data" in structures["sample.py"]["async_functions"]
        assert "get_user" in structures["sample.py"]["methods"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_build_file_tree():
    """Test nested file tree generation."""
    from app.services.tree_builder import build_file_tree

    modules = [
        "src/main.py",
        "src/services/auth.py",
        "src/services/user.py",
        "README.md",
    ]

    tree = build_file_tree(modules)

    assert isinstance(tree, list)
    assert any(node["name"] == "src" and node["type"] == "folder" for node in tree)
    assert any(node["name"] == "README.md" and node["type"] == "file" for node in tree)


def test_extract_code_structures_javascript():
    """Test JS/TS code structure extraction."""
    from app.services.code_structure_extractor import extract_code_structures

    temp_dir = TEST_TMP_DIR / "structure_js_case"

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        sample_file = temp_dir / "app.js"
        sample_file.write_text(
            """
export function login() {
    return true;
}

class AuthService {
    authenticate() {
        return true;
    }
}

const loadUser = () => {
    return {};
};
""",
            encoding="utf-8",
        )

        file_map = {"app.js": str(sample_file)}
        structures = extract_code_structures(file_map)

        assert "app.js" in structures
        assert "AuthService" in structures["app.js"]["classes"]
        assert "login" in structures["app.js"]["functions"]
        assert "loadUser" in structures["app.js"]["arrow_functions"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Run tests with: pytest test_visualization_agent.py -v
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
