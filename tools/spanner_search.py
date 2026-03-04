from google.cloud import spanner
from typing import List, Dict, Any

class SpannerGraphTool:
    """
    Tool to execute GQL (Graph Query Language) queries against Google Spanner Graph.
    
    The schema of the healthcare network graph is as follows:
    - Nodes:
        - `Provider` (properties: id, name, bio)
        - `Clinic` (properties: id, name)
        - `Hospital` (properties: id, name)
    - Edges:
        - `WORKS_AT` (From Provider to Clinic)
        - `AFFILIATED_WITH` (From Clinic to Hospital)
        
    Example GQL Query:
    GRAPH FinGraph MATCH (d:Provider)-[:WORKS_AT]->(c:Clinic) RETURN d.name, c.name
    """
    
    def __init__(self, instance_id: str, database_id: str, project_id: str = None):
        self.spanner_client = spanner.Client(project=project_id)
        self.instance = self.spanner_client.instance(instance_id)
        self.database = self.instance.database(database_id)

    def execute_gql(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a GQL query against the Spanner Graph database.
        
        Args:
            query (str): The GQL query string.
            
        Returns:
            List[Dict[str, Any]]: The results of the query.
        """
        results = []
        try:
            with self.database.snapshot() as snapshot:
                # GQL is executed via the execute_sql method
                results_iterator = snapshot.execute_sql(query)
                for row in results_iterator:
                    row_dict = dict(zip([col.name for col in results_iterator.fields], row))
                    results.append(row_dict)
            return results
        except Exception as e:
            return [{"error": str(e)}]
