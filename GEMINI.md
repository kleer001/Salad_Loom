# GEMINI.md

## Project Overview

This project, Salad Loom, is a modular absurdist text synthesizer built on a visual node-graph editor. It allows users to create, connect, and run nodes to perform procedural text transformations — from Markov chains and N+7 substitution to semantic drift and dependency parsing — without writing code.

The project consists of several key components:

*   **Core Engine:** A Python-based engine that manages the node graph, data flow, and execution logic. All data is `List[str]`.
*   **Backend API:** A FastAPI server that exposes a RESTful API for interacting with the core engine.
*   **Frontend GUI:** A React-based web interface that provides a visual node editor for creating and managing workflows.
*   **Terminal User Interface (TUI):** A terminal-based interface for users who prefer a command-line experience.
*   **REPL:** An interactive Python shell for scripting and direct interaction with the Salad Loom core.

The system is designed to be modular and extensible. New nodes are auto-discovered: any `src/core/*_node.py` file is registered automatically via `enums.py` — no manual registration needed.

## Building and Running

### Prerequisites

*   Python 3.8+
*   Node.js 18+ and npm (for GUI only)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kleer001/Salad_Loom
    cd Salad_Loom
    ```

2.  **Set up the Python environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    export PYTHONPATH=$PYTHONPATH:$(pwd)/src
    ```

3.  **Download NLP models:**
    ```bash
    python -m spacy download en_core_web_sm
    python3 -c "import nltk; [nltk.download(p) for p in ['averaged_perceptron_tagger_eng','punkt_tab','words','cmudict']]"
    ```

4.  **Install frontend dependencies (optional, GUI only):**
    ```bash
    cd src/GUI
    npm install
    ```

### Running the Application

Salad Loom can be run in several modes:

*   **GUI Mode:**
    ```bash
    ./salad_loom -g
    ```
    Starts the FastAPI backend and the Vite dev server. GUI accessible at `http://localhost:5173`.

*   **TUI Mode:**
    ```bash
    ./salad_loom -t
    ```

*   **REPL Mode:**
    ```bash
    ./salad_loom -r
    ```

*   **API Only:**
    ```bash
    ./salad_loom -a
    ```
    API docs at `http://localhost:8000/api/v1/docs`.

*   **Batch Mode:**
    ```bash
    ./salad_loom -b -f examples/recipes/n_plus_7.json
    ```

### Testing

```bash
cd src
pytest
```

## Development Conventions

*   **Backend:** Python/FastAPI in `src/`. All node files in `src/core/*_node.py`.
*   **Frontend:** React/Vite in `src/GUI/src`.
*   **Node auto-discovery:** Class name is derived from filename: `my_node.py` → `MyNode`. No registration needed.
*   **Data model:** All connections carry `List[str]`. No other data types in the graph.
*   **Dependencies:** Python deps in `setup.py` and `requirements.txt`; frontend deps in `src/GUI/package.json`.
*   **API:** RESTful, documented via OpenAPI/Swagger at `/api/v1/docs`.
