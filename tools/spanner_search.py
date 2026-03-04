from google.cloud import spanner  # type: ignore
from typing import List, Dict, Any, Optional

class SpannerGraphTool:
    """
    Tool to execute GQL (Graph Query Language) queries against Google Spanner Graph.
    
    The schema of the healthcare network graph (Graph Name: 'HealthcareGraph') is:
    - Nodes:
        - `Provider` (properties: id, name, bio)
        - `Clinic` (properties: id, name)
        - `Hospital` (properties: id, name)
    - Edges:
        - `WORKS_AT` (From Provider to Clinic)
        - `AFFILIATED_WITH` (From Clinic to Hospital)
        
    Usage:
    - The query MUST start with 'GRAPH HealthcareGraph ...'
    - Example: `GRAPH HealthcareGraph MATCH (d:Provider)-[:WORKS_AT]->(c:Clinic) RETURN d.name, c.name`
    """
    
    def __init__(self, instance_id: str, database_id: str, project_id: Optional[str] = None):
        self.client = spanner.Client(project=project_id)
        self.instance = self.client.instance(instance_id)
        self.database = self.instance.database(database_id)

    def execute_gql(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a GQL query against the Spanner Graph database.
        
        Args:
            query (str): The GQL query string. MUST start with 'GRAPH HealthcareGraph'.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the graph results.
        """
        results = []
        try:
            # Use a read-only snapshot for consistency and performance
            with self.database.snapshot() as snapshot:
                results_iterator = snapshot.execute_sql(query)
                
                # Iterate and convert rows to dicts
                for row in results_iterator:
                    # Dynamically map field names to values
                    # 'fields' is available on the iterator after the first read
                    columns = [field.name for field in results_iterator.fields]
                    results.append(dict(zip(columns, row)))
                    
            return results
        except Exception as e:
            # Return the error to the LLM so it can fix its query
            return [{"error": f"Query execution failed: {str(e)}"}]
