import os
from google.cloud import spanner  # type: ignore

def create_database(instance_id, database_id, project_id=None):
    spanner_client = spanner.Client(project=project_id)
    instance = spanner_client.instance(instance_id)
    
    # Define DDL statements for nodes, edges, and the property graph
    ddl_statements = [
        """
        CREATE TABLE Provider (
            id INT64 NOT NULL,
            name STRING(MAX),
            bio STRING(MAX)
        ) PRIMARY KEY (id)
        """,
        """
        CREATE TABLE Clinic (
            id INT64 NOT NULL,
            name STRING(MAX)
        ) PRIMARY KEY (id)
        """,
        """
        CREATE TABLE Hospital (
            id INT64 NOT NULL,
            name STRING(MAX)
        ) PRIMARY KEY (id)
        """,
        """
        CREATE TABLE WorksAt (
            provider_id INT64 NOT NULL,
            clinic_id INT64 NOT NULL,
            FOREIGN KEY (provider_id) REFERENCES Provider(id),
            FOREIGN KEY (clinic_id) REFERENCES Clinic(id)
        ) PRIMARY KEY (provider_id, clinic_id)
        """,
        """
        CREATE TABLE AffiliatedWith (
            clinic_id INT64 NOT NULL,
            hospital_id INT64 NOT NULL,
            FOREIGN KEY (clinic_id) REFERENCES Clinic(id),
            FOREIGN KEY (hospital_id) REFERENCES Hospital(id)
        ) PRIMARY KEY (clinic_id, hospital_id)
        """,
        """
        CREATE PROPERTY GRAPH HealthcareGraph
        NODE TABLES (
            Provider,
            Clinic,
            Hospital
        )
        EDGE TABLES (
            WorksAt
                SOURCE KEY (provider_id) REFERENCES Provider(id)
                DESTINATION KEY (clinic_id) REFERENCES Clinic(id)
                LABEL WORKS_AT,
            AffiliatedWith
                SOURCE KEY (clinic_id) REFERENCES Clinic(id)
                DESTINATION KEY (hospital_id) REFERENCES Hospital(id)
                LABEL AFFILIATED_WITH
        )
        """
    ]

    print(f"Creating database {database_id} on instance {instance_id}...")
    database = instance.database(database_id)
    operation = database.create(extra_statements=ddl_statements)
    operation.result(120)
    print("Database and Schema created.")

def seed_data(instance_id, database_id, project_id=None):
    spanner_client = spanner.Client(project=project_id)
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)

    print("Inserting mock data...")
    with database.batch() as batch:
        # 5 Hospitals
        batch.insert(
            table='Hospital',
            columns=('id', 'name'),
            values=[(i, f'Hospital {i}') for i in range(1, 6)]
        )
        # 10 Clinics
        batch.insert(
            table='Clinic',
            columns=('id', 'name'),
            values=[(i, f'Clinic {i}') for i in range(1, 11)]
        )
        # 20 Providers
        batch.insert(
            table='Provider',
            columns=('id', 'name', 'bio'),
            values=[(i, f'Dr. Provider {i}', f'Bio for Doctor {i}') for i in range(1, 21)]
        )
        # Edges WorksAt (Provider -> Clinic)
        batch.insert(
            table='WorksAt',
            columns=('provider_id', 'clinic_id'),
            values=[(i, (i % 10) + 1) for i in range(1, 21)]
        )
        # Edges AffiliatedWith (Clinic -> Hospital)
        batch.insert(
            table='AffiliatedWith',
            columns=('clinic_id', 'hospital_id'),
            values=[(i, (i % 5) + 1) for i in range(1, 11)]
        )
    print("Mock data inserted successfully.")

if __name__ == "__main__":
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    instance_id = os.environ.get("SPANNER_INSTANCE_ID", "healthcare-instance")
    database_id = os.environ.get("SPANNER_DATABASE_ID", "healthcare-db")
    
    # create_database(instance_id, database_id, project_id)
    # seed_data(instance_id, database_id, project_id)
    print("Run create_database and seed_data after ensuring the Spanner instance exists.")
