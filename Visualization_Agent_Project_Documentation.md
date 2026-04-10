# Visualization Agent Project Documentation

## 1. Project Summary

Visualization Agent is an AI-powered tool for analyzing and visualizing Python project architectures. It parses code and Docker Compose files, traces runtime execution, builds dependency graphs, and uses OpenAI GPT-4o-mini to generate architecture descriptions, risk analysis, and insights. It outputs Mermaid diagrams and HTML visualizations.

---

## 2. Main Features
- Static code analysis (AST-based module and import extraction)
- Docker Compose parsing and service-to-code mapping
- Runtime tracing (captures actual function calls and execution flow)
- AI-driven architecture description, risk detection, and insights
- Diagram generation (Mermaid, HTML)
- Comparison of static vs. runtime graphs

---

## 3. Key Modules & Responsibilities

### Parsers (`backend/app/parsers/`)
- **python_parser.py**: Extracts Python modules and their import relationships using AST.
- **docker_parser.py**: Reads Docker Compose YAML files to find service definitions.
- **service_mapper.py**: Connects Docker services to Python modules by matching names.

### Agents (`backend/app/agents/`)
- **architecture_agent.py**: Uses AI to generate human-readable architecture descriptions.
- **risk_agent.py**: Finds risky areas (like bottlenecks or isolated code) in the architecture.
- **diagram_agent.py**: Improves Mermaid diagrams for clarity using AI.
- **comparison_agent.py**: Compares static (code) and runtime (actual execution) graphs to find differences.
- **insight_agent.py**: Provides deeper insights and suggestions for improvements.

### Graph (`backend/app/graph/`)
- **graph_builder.py**: Builds directed graphs (using NetworkX) from parsed code and service data.
- **runtime_graph.py**: Builds graphs from runtime trace data (actual function calls during execution).

### Services (`backend/app/services/`)
- **llm_service.py**: Handles all communication with the OpenAI API for AI-powered analysis.
- **diagram_service.py**: Converts graph data into Mermaid diagram format.

### Utils (`backend/app/utils/`)
- **runtime_tracker.py**: Hooks into Python’s tracing system to capture function calls during execution.
- **diagram_html.py**: Generates HTML files with embedded Mermaid diagrams for visualization.
- **validator.py**: Checks Docker Compose files for errors or inconsistencies.

### Routes (`backend/app/routes/`)
- **analyze.py**: Main FastAPI endpoints for `/analyze` and `/diagram`, orchestrating the analysis pipeline.

### Scripts (`backend/app/scripts/`)
- **run_with_trace.py**: Script to run a Python project with tracing enabled, capturing runtime data.

### Data (`data/`)
- **sample_project/**: Example Python app and Docker Compose file for testing the analysis pipeline.

---

## 4. Technologies Used
- FastAPI, Uvicorn (backend)
- OpenAI API (GPT-4o-mini)
- NetworkX, Python AST, PyYAML
- Mermaid.js (diagram rendering)
- python-dotenv

---

## 5. API Endpoints
- `/analyze` (POST): Full analysis pipeline
- `/diagram` (POST): Diagram generation
- `/` (GET): Health check

---

## 6. Example: How It Works
1. User sends project path and Docker Compose file to `/analyze`.
2. The backend parses code and Docker Compose, builds graphs, and runs AI agents.
3. Returns architecture description, risks, diagrams, and insights.

---

## 7. Requirements
```
fastapi
uvicorn
openai
networkx
pyyaml
python-dotenv
```

---

## 8. Main Pipeline (analyze.py)
- Parses Python code and Docker Compose
- Builds static and runtime graphs
- Runs AI agents for architecture, risks, diagram enhancement, comparison, and insights
- Returns all results as JSON

---

## 9. Mermaid Diagram Example
```
graph TD
  service1 --> app.py
  app.py --> db.py
```

---

## 10. Contact
For more details, see the code or contact the author.
