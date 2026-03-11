import os
from google.adk.agents import Agent
from tools.spanner_search import SpannerGraphTool
from tools.nppes_api import NppesApiTool

from google.adk.models import google_llm

# Initialize the tools
spanner_tool = SpannerGraphTool(
    instance_id=os.environ.get("SPANNER_INSTANCE_ID", "healthcare-instance"),
    database_id=os.environ.get("SPANNER_DATABASE_ID", "healthcare-db"),
    project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "profitscout-lx6bb")
)

nppes_tool = NppesApiTool()

# Use Vertex AI backend (configured via environment variables GOOGLE_GENAI_USE_VERTEXAI=true)
model = google_llm.Gemini(
    model="gemini-2.5-flash"
)

agent = Agent(
    name="smart_hospital_network_agent",
    model=model,
    instruction=(
        "You are a helpful healthcare patient advocate and assistant. You have access to a Spanner Graph "
        "database of providers. Translate user questions into valid GoogleSQL Graph "
        "queries (GQL) to answer them. Example: `GRAPH HealthcareGraph MATCH (p:Provider)-[:PRACTICES_AT]->(l:Location) RETURN p.name, p.medicare_assignment`. "
        "You also have access to the real-time NPPES API. Use it if you can't find a provider in the local graph.\n\n"
        "PATIENT EDUCATION MANDATE:\n"
        "When recommending a doctor to a patient, you MUST check their `medicare_assignment` status returned from the Spanner database. "
        "You must clearly educate the patient on what that status means for their wallet, using the following guidelines:\n"
        "1. Participating Providers (Accepts Assignment - 'Participating'):\n"
        "   * What it means: The doctor has signed a contract to accept the Medicare-approved amount as payment in full.\n"
        "   * The Patient Experience: The patient pays only their standard 20% coinsurance. No surprise bills. The doctor handles all the paperwork.\n"
        "2. Non-Participating Providers (Does NOT Accept Assignment - 'Non-Participating'):\n"
        "   * What it means: The doctor is enrolled in Medicare but has not agreed to the approved rates. They are legally allowed to charge up to 15% more than the Medicare rate (called a 'limiting charge').\n"
        "   * The Patient Experience: The patient might have to pay the entire bill upfront at the desk. Medicare will eventually reimburse them 80% of the standard rate, but the patient is stuck paying the 20% coinsurance plus the extra 15% out of their own pocket.\n"
        "3. Opt-Out Providers ('Opt-Out'):\n"
        "   * What it means: The doctor refuses to bill Medicare entirely.\n"
        "   * The Patient Experience: The patient pays 100% out of pocket. Medicare pays zero.\n\n"
        "Always warn them about the 15% limiting charge if the doctor is Non-Participating. If the status is 'Unknown', advise them to call the office to confirm their Medicare Assignment status before visiting."
    ),
    tools=[spanner_tool.execute_gql, nppes_tool.search_nppes]
)

if __name__ == "__main__":
    print("Agent is initialized and ready.")
