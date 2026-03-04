# Production Plan: Smart Hospital Network Agent using NPPES Data

To transform this portfolio project into a production-grade, free public service, we need to move away from mock data and utilize the official **National Plan and Provider Enumeration System (NPPES)** dataset provided by CMS.

Here is the high-level architecture and implementation plan:

## 1. Data Ingestion & Pipeline (ETL)

The NPPES provides data in two ways: a real-time API (limited to 200 results per query) and bulk downloadable CSV files (over 4GB in size). For a Graph RAG system, we need the bulk data to pre-populate our Spanner database.

*   **Download Phase:** Create a scheduled Cloud Run Job or Cloud Function that triggers monthly to download the "Monthly Full Replacement NPI File" from the CMS Data Dissemination page.
*   **Transform Phase (Dataflow/Dataflow/Pandas):** 
    *   The raw CSV is massive. We need an ETL pipeline (like Google Cloud Dataflow using Apache Beam) to parse the CSV.
    *   Map the flat CSV rows to our Graph schema:
        *   **Nodes:** Extract `Provider` (NPI, Name, Credentials), `Clinic` (Practice Location Address), and `Hospital` (if affiliated via secondary APIs or organizational NPIs).
        *   **Edges:** Create `WORKS_AT` edges linking the Provider NPI to their practice location.

### Expanded Graph Schema (NPPES Potential)
The NPPES bulk CSV contains hundreds of columns that allow for a much richer graph than our mock data. We can add new nodes and edges such as:
*   **Node: `Specialty/Taxonomy`**: Providers have primary and secondary taxonomy codes.
    *   *Edge:* `HAS_SPECIALTY` (Provider -> Taxonomy). This allows queries like *"Find me all cardiologists in NY."*
*   **Node: `Organization/Entity`**: Entity Type 2 NPIs represent organizations rather than individuals.
    *   *Edge:* `AFFILIATED_WITH` or `PART_OF` (Individual Provider [Type 1] -> Organization [Type 2]).
*   **Node: `Location/State`**: Geocoding the practice addresses.
    *   *Edge:* `LOCATED_IN` (Clinic/Organization -> State/City).
*   **Node: `Identifier/Issuer`**: Providers often list other state licenses or Medicare/Medicaid IDs.
    *   *Edge:* `HOLDS_LICENSE` (Provider -> State License).
*   **Load Phase (Spanner):** Use the Spanner batch mutation API (similar to our current `seed_spanner.py`, but optimized for millions of rows) to write the transformed nodes and edges into the Spanner Graph tables.

## 2. Real-Time Data Augmentation (Optional)

Since the bulk file is monthly, newly registered doctors won't appear immediately.
*   We can create a secondary Google ADK Tool (`NppesApiTool`) that calls the `https://npiregistry.cms.hhs.gov/api/` endpoint in real-time. 
*   If the agent cannot find a provider in the Spanner Graph, it can fall back to the NPPES API to fetch the latest data and even insert it into the graph on the fly.

## 3. Productionizing the Agent Backend

*   **Compute:** Deploy the Google ADK Python application to **Google Cloud Run** using a Dockerfile. Cloud Run scales to zero (keeping costs low for a free service) and scales up infinitely during traffic spikes.
*   **Database:** Ensure the Spanner instance is sized appropriately. For a public service, a multi-region Spanner configuration provides high availability, though a single-region setup is cheaper for an initial launch.
*   **Security & Guardrails:**
    *   Implement rate limiting (e.g., using Cloud Armor) to prevent abuse of the free service.
    *   Refine the Agent's `instruction` to strictly refuse non-healthcare queries to save on LLM token costs.

## 4. Frontend & Hosting

*   **UI:** The current Streamlit application is excellent for prototyping. For a highly scalable public frontend, we could either deploy the Streamlit app to Cloud Run alongside the backend, or rewrite it in Next.js/React and host it on **Firebase Hosting** or **Cloud Run**.
*   **Domain:** Purchase a domain and map it to the frontend service.

## Summary Architecture Flow
1. **CMS NPPES** -> *Monthly CSV Download* -> **Google Cloud Storage**
2. **Cloud Storage** -> *Dataflow ETL Job* -> **Google Spanner Graph**
3. **User** -> *Streamlit UI* -> **Cloud Run (ADK Agent)**
4. **Agent** -> *Translates to GQL* -> **Spanner Graph** -> *Returns Answer to User*
