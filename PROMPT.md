**CONTEXT:**
Act as a Principal Cloud Architect. I am building a portfolio project to demonstrate the new **Google Agent Development Kit (ADK)** and **Spanner Graph**. The project is a "Smart Hospital Network Agent" that helps users find providers and clinics.

**TARGET STACK:**
- **Framework:** Google ADK (Python).
- **Database:** Google Spanner Graph (using GoogleSQL/GQL).
- **Compute:** Google Cloud Run.
- **Frontend:** React (Vite).

**TASK:**
Scaffold a complete `google-adk` project structure. Provide the file tree and the code for the critical files listed below.

**REQUIREMENTS:**

1.  **Project Structure:**
    Create a standard ADK project structure:
    - `/agent`: Contains the ADK agent logic.
    - `/tools`: Custom tools for Spanner Graph.
    - `/frontend`: React application.
    - `adk.yaml`: Agent configuration.

2.  **Dependencies (`requirements.txt`):**
    - `google-adk`
    - `google-cloud-spanner`
    - `uvicorn`

3.  **Spanner Tool (`/tools/spanner_search.py`):**
    - Create a custom ADK tool class `SpannerGraphTool`.
    - It must connect to a Spanner instance using `google.cloud.spanner`.
    - It should execute **GQL (Graph Query Language)** queries.
    - **Crucial:** Include a docstring that teaches the LLM the schema so it knows how to query it.
    - **Schema:**
      - Nodes: `Provider` (id, name, bio), `Clinic` (id, name), `Hospital` (id, name).
      - Edges: `WORKS_AT` (Provider -> Clinic), `AFFILIATED_WITH` (Clinic -> Hospital).

4.  **Agent Definition (`/agent/network_agent.py`):**
    - Initialize a `google.adk.Agent`.
    - Use model `gemini-1.5-pro`.
    - **System Instruction:** "You are a helpful healthcare assistant. You have access to a Spanner Graph database of providers. Translate user questions into valid GoogleSQL Graph queries (GQL) to answer them. Example: `GRAPH FinGraph MATCH (d:Doctor)-[:WORKS_AT]->(c:Clinic) RETURN d.name`."

5.  **Data Seeding (`/scripts/seed_spanner.py`):**
    - A Python script to create the Spanner instance, Database, and Schema (using `CREATE TABLE` and `CREATE PROPERTY GRAPH`).
    - Insert mock data for 5 hospitals, 10 clinics, and 20 providers.

6.  **Frontend (`/frontend/App.jsx`):**
    - A simple chat UI that connects to the ADK backend (default port 8000).

**OUTPUT INSTRUCTION:**
Provide the code blocks for the files above. Ensure the Spanner tool handles the GQL syntax correctly.