# Knowledgedock

Knowledgedock is an extensible, desktop-based learning resource aggregator built with Python and PyQt5. 

While on the surface it serves as a distraction-free environment for reading educational materials, the core of the project was designed to solve several complex software engineering challenges, including **dynamic plugin architecture**, **asynchronous UI management**, and **heterogeneous data normalization**.

## Architectural Highlights

### 1. Manually Registered Plugin Architecture (The Extension System)
The application doesn't hardcode API integrations directly into the UI. Instead, it implements a robust plugin system using the Open-Closed Principle.
* **Abstract Base Classes**: Integrations (like DOAJ, OpenLibrary, Wikipedia, and arXiv) inherit from a base `Extension` class, enforcing a strict contract for data retrieval.
* **Extensibility**: New sources can be added smoothly. The `ExtensionManager` handles the lifecycle of these plugins, which are manually registered in the `main.py` orchestrator.

### 2. Unified Data Normalization
Educational APIs serve vastly different data structures (e.g., arXiv returns Atom XML, Wikipedia returns nested JSON snippets, OpenLibrary returns custom JSON metadata). 
* Knowledgedock implements an **ingestion layer** that normalizes these heterogeneous payloads into a unified `Resource` data model. 
* This allows the `DatabaseManager` and UI layer to interact with all resources predictably, regardless of their origin.

### 3. Asynchrony and Concurrency 
Building a desktop aggregator requires heavy network I/O. Using standard synchronous calls would freeze the PyQt5 event loop.
* **QThreads Integration**: The application utilizes PyQt's threading models (`download_helper.py`) to offload heavy network operations (like downloading 10MB PDFs or fetching large JSON payloads) to background threads.
* **Responsive UI**: The main thread remains responsive, handling UI updates, animations, and user interactions smoothly while worker threads handle data ingestion.

### 4. Offline Persistence & Caching
Rather than relying purely on REST calls, the application implements local state management.
* **SQLite Database**: A local `DatabaseManager` tracks bookmarks, downloaded files, and registered extensions.
* **Unified Library**: Users can download resources from multiple disjointed platforms (e.g., a PDF from DOAJ, an EPUB from OpenLibrary) and manage them within a single, queryable local SQLite interface.

## System Requirements

- Python 3.7+
- PyQt5 & PyQtWebEngine
- SQLite3 (built into Python)

## Installation & Setup

1. Clone the repository and navigate to the project directory:
```bash
cd mihon_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Future Technical Enhancements
- **Build Pipeline Optimization**: Implementing automated builds (e.g., PyInstaller via GitHub Actions) for cross-platform distribution.
- **Automated Testing Suite**: Introducing a `pytest` suite for the `DatabaseManager` and the Data Normalization pipeline to ensure stability when third-party APIs change.
- **LLM Summarization Engine**: Extending the plugin architecture to run local summarization models over fetched textual content.

## License
MIT License
