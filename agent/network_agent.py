import os
from google.adk.agents import Agent
from tools.spanner_search import SpannerGraphTool
from tools.nppes_api import NppesApiTool

# Initialize the tools
spanner_tool = SpannerGraphTool(
    instance_id=os.environ.get("SPANNER_INSTANCE_ID", "healthcare-instance"),
    database_id=os.environ.get("SPANNER_DATABASE_ID", "healthcare-db"),
    project_id=os.environ.get("GOOGLE_CLOUD_PROJECT", "profitscout-lx6bb")
)

nppes_tool = NppesApiTool()

agent = Agent(
    name="smart_hospital_network_agent",
    model="gemini-3-flash-preview",
    instruction=(
        "You are a helpful healthcare assistant. You have access to a Spanner Graph "
        "database of providers. Translate user questions into valid GoogleSQL Graph "
        "queries (GQL) to answer them. Example: `GRAPH HealthcareGraph MATCH (d:Provider)-[:WORKS_AT]->(c:Clinic) RETURN d.name`. "
        "You also have access to the real-time NPPES API. Use it if you can't find a provider in the local graph, "
        "or if the user explicitly asks for nationwide real-time data."
    ),
    tools=[spanner_tool.execute_gql, nppes_tool.search_nppes]
)

if __name__ == "__main__":
    print("Agent is initialized and ready.")
