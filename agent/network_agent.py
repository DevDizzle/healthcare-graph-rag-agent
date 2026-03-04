import os
from google.adk.agents import Agent
from tools.spanner_search import SpannerGraphTool

# Initialize the Spanner Tool
spanner_tool = SpannerGraphTool(
    instance_id=os.environ.get("SPANNER_INSTANCE_ID", "healthcare-instance"),
    database_id=os.environ.get("SPANNER_DATABASE_ID", "healthcare-db")
)

agent = Agent(
    name="Smart Hospital Network Agent",
    model="gemini-3-flash-preview",
    instruction=(
        "You are a helpful healthcare assistant. You have access to a Spanner Graph "
        "database of providers. Translate user questions into valid GoogleSQL Graph "
        "queries (GQL) to answer them. Example: `GRAPH HealthcareGraph MATCH (d:Provider)-[:WORKS_AT]->(c:Clinic) RETURN d.name`."
    ),
    tools=[spanner_tool.execute_gql]
)

if __name__ == "__main__":
    print("Agent is initialized and ready.")
