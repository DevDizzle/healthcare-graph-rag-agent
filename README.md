# Smart Hospital Network Agent (Graph RAG)

A cutting-edge portfolio project demonstrating a **Graph-based Retrieval-Augmented Generation (Graph RAG)** architecture. This agentic application helps users intuitively search for healthcare providers, clinics, and hospital affiliations using natural language, seamlessly bridging the gap between conversational AI and complex, structured graph data.

## 🚀 Overview

The **Smart Hospital Network Agent** solves a critical problem in healthcare: data fragmentation. Healthcare networks are highly connected (Doctors work at Clinics, Clinics are affiliated with Hospitals), making traditional relational databases cumbersome for deep relationship queries. By modeling this data as a property graph, the agent can traverse complex relationships instantly.

Instead of requiring users (patients or staff) to navigate complex UI forms or know query languages, they can simply ask questions in plain English like:
* *"Which clinics is Dr. Provider 1 affiliated with?"*
* *"Find me all doctors working at hospitals near me."*

The Agent translates these natural language queries into executable **GQL (Graph Query Language)** in real-time.

## 🛠️ Technologies Used

This project showcases modern, cloud-native agentic development using the latest Google technologies:

*   **Google Agent Development Kit (ADK):** The core orchestrator (Python) that manages the Gemini 3 Flash model, system instructions, and tool calling.
*   **Google Spanner Graph:** A horizontally scalable, globally consistent database with native graph capabilities. We use the emerging **GoogleSQL Graph (GQL)** syntax to map Nodes (`Provider`, `Clinic`, `Hospital`) and Edges (`WORKS_AT`, `AFFILIATED_WITH`).
*   **Gemini 3 Flash:** The underlying LLM powering the agent's reasoning. It dynamically maps user intent to the database schema exposed via the tool's docstrings.
*   **Google Cloud Run:** (Targeted) The serverless compute platform to host the containerized ADK backend.
*   **React + Vite (Frontend):** A fast, lightweight, and modern chat interface for users to interact with the backend agent.
*   **GitHub Actions (CI/CD):** Automated pipelines for linting (`flake8`) and type checking (`mypy`) the Python codebase, ensuring robust, production-ready code.

## 🧠 Architecture Highlights

1.  **Agentic Tool Use:** The agent is given a specific tool (`SpannerGraphTool`). The magic happens in the tool's Python docstring, where the exact graph schema (nodes, properties, edges) is defined. The LLM reads this "contract" and uses it to construct precise GQL queries.
2.  **Deterministic Data Retrieval:** Unlike standard RAG that relies entirely on vector embeddings and semantic similarity (which can hallucinate or miss exact matches), *Graph RAG* executes deterministic queries against the database, returning 100% accurate factual data from the graph to the LLM for formatting.
3.  **Schema Enforcement:** The automated CI/CD pipeline ensures that the Python types, especially the interaction boundaries between the agent and the Spanner tool, remain strict.

## 📂 Project Structure

*   `/agent/`: Contains the `google-adk` initialization, system prompts, and model configuration.
*   `/tools/`: Custom tools for the agent. Contains `spanner_search.py` which handles the connection to Spanner and GQL execution.
*   `/scripts/`: Utilities like `seed_spanner.py` to programmatically create the Spanner Graph schema and insert mock data.
*   `/frontend/`: The Vite React application for the chat UI.
*   `.github/workflows/`: CI/CD automation.

## 🌟 Why is this useful?

1.  **For Patients:** Simplifies finding the right doctor within a specific network without navigating confusing directories.
2.  **For Organizations:** Demonstrates how massive, complex institutional knowledge (personnel, facilities, capabilities) can be unlocked for conversational querying without pre-building hundreds of API endpoints.
3.  **For Developers:** Proves out the viability of **GQL + LLMs**. Writing GQL manually is hard; letting an LLM write it dynamically based on a schema docstring is incredibly powerful and scalable.