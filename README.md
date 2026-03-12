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

*   **Google Agent Development Kit (ADK):** The core orchestrator (Python) that manages the Gemini model, system instructions, and tool calling via Vertex AI.
*   **Google Spanner Graph:** A horizontally scalable, globally consistent database with native graph capabilities. We use **GoogleSQL Graph (GQL)** to map Nodes (`Provider`, `Specialty`, `Location`) and Edges (`WORKS_AT`, `HAS_SPECIALTY`).
*   **Gemini 2.5 Flash:** The underlying LLM powering the agent's reasoning. It dynamically maps user intent to the database schema exposed via the tool's docstrings.
*   **Google Cloud Run:** The serverless compute platform hosting the containerized ADK backend API.
*   **Streamlit (Frontend):** A fast, lightweight, and modern chat interface for users to interact with the backend agent.

## 🧠 Architecture Highlights

1.  **Deterministic Graph Retrieval:** Unlike standard RAG that relies entirely on vector embeddings and semantic similarity (which can hallucinate or miss exact matches), *Graph RAG* executes deterministic queries against the Spanner database.
2.  **Real-Time API Fallback & Joins:** When a provider isn't found in the local graph, the agent automatically falls back to querying the national **NPPES API**. Behind the scenes, the agent performs a real-time join against the **CMS Provider Data API** to enrich the NPPES data with live "Medicare Assignment" financial status.
3.  **Visible Retrieval Tracing:** The Streamlit UI features an expandable "Retrieval Trace" panel, allowing interviewers and engineers to instantly verify *how* the agent acquired its data (e.g., whether it fired a GQL query or executed a real-time API join).

## 🌟 Example Queries

Try these prompts in the demo to see the agent's reasoning and retrieval in action:
*   *"Find me a doctor named Ardalan Enkeshafi."* -> **Tests Spanner Graph Retrieval**
*   *"Find me an eye doctor in Saint Augustine, FL. What is their medicare status?"* -> **Tests Real-Time Fallback & CMS Joining**
*   *"I need a Family Medicine doctor in Chicago."* -> **Tests Fallback & Patient Financial Education Mandate**

## 📂 Project Structure

*   `/agent/`: Contains the `google-adk` initialization, system prompts, and model configuration.
*   `/tools/`: Custom tools for the agent. Contains `spanner_search.py` which handles the connection to Spanner and GQL execution.
*   `/scripts/`: Utilities like `seed_spanner.py` to programmatically create the Spanner Graph schema and insert mock data.
*   `streamlit_app.py`: The Streamlit application for the chat UI.
*   `.github/workflows/`: CI/CD automation.

## 🌟 Why is this useful?

1.  **For Patients:** Simplifies finding the right doctor within a specific network without navigating confusing directories.
2.  **For Organizations:** Demonstrates how massive, complex institutional knowledge (personnel, facilities, capabilities) can be unlocked for conversational querying without pre-building hundreds of API endpoints.
3.  **For Developers:** Proves out the viability of **GQL + LLMs**. Writing GQL manually is hard; letting an LLM write it dynamically based on a schema docstring is incredibly powerful and scalable.