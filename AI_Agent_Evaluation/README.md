# Generic AI Agent Testing Platform

A universal testing engine for AI agents, analogous to PyTest for software.

## Architecture Overview

This platform is built using a Clean Architecture approach with a robust Plugin System. It separates the core orchestration logic from the specific implementations of agents and evaluation frameworks.

### Core Modules:
1.  **Execution Engine**: The orchestrator that coordinates the workflow.
2.  **Agent Registry & Connectors**: Manages agent configurations and connects to them via REST APIs or Python classes.
3.  **Test Case Manager**: Loads and validates test cases from JSON, CSV, or Excel.
4.  **Evaluation Engine & Plugins**: Evaluates agent outputs using metrics like latency, JSON schema validation, or (in future milestones) DeepEval and RAGAS.
5.  **History & Reports**: Stores execution history, enables regression comparison, and generates HTML reports.

## Getting Started

### Prerequisites

*   Python 3.11+
*   Virtual environment recommended

### Installation

1.  Clone the repository and navigate to the root directory.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up environment variables:
    ```bash
    cp .env.example .env
    ```

### Running the Application

The platform consists of two components: the FastAPI backend and the Streamlit frontend.

1.  **Start the Backend (API):**
    ```bash
    python main.py
    ```
    The API documentation will be available at `http://localhost:8000/docs`.

2.  **Start the Frontend (UI):**
    Open a new terminal window and run:
    ```bash
    streamlit run src/ui/app.py
    ```
    The UI will be available at `http://localhost:8501`.

## Plugin System

The platform is designed to be highly extensible. You can add new Agent Connectors or Evaluation Metrics without modifying the core engine.

### Adding an Evaluator

To add a new evaluator:
1. Create a Python file in `src/evaluation/plugins/`.
2. Subclass `BaseEvaluator` from `src.core.interfaces`.
3. Decorate your class with `@register_evaluator("your_metric_name")`.
4. Import your new module in `src/evaluation/plugins/__init__.py`.

Example:
```python
from src.evaluation.registry import register_evaluator
from src.core.interfaces import BaseEvaluator

@register_evaluator("my_custom_metric")
class MyCustomEvaluator(BaseEvaluator):
    evaluator_name = "my_custom_metric"
    # ... implement evaluate() ...
```

### Adding a Connector

To add a new connector (e.g., gRPC, WebSocket):
1. Create a Python file in `src/connectors/plugins/`.
2. Subclass `BaseConnector` from `src.core.interfaces`.
3. Decorate your class with `@register_connector("your_protocol")`.
4. Import your module in `src/connectors/plugins/__init__.py`.
