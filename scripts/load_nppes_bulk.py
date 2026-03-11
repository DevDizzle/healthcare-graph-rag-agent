import os
import csv
import json
import urllib.request
from google.cloud import spanner

def create_schema(instance_id, database_id, project_id):
    spanner_client = spanner.Client(project=project_id)
    instance = spanner_client.instance(instance_id)
    
    ddl_statements = [
        """
        CREATE TABLE Provider (
            npi INT64 NOT NULL,
            name STRING(MAX),
            credential STRING(MAX),
            medicare_assignment STRING(MAX)
        ) PRIMARY KEY (npi)
        """,
        """
        CREATE TABLE Organization (
            npi INT64 NOT NULL,
            name STRING(MAX)
        ) PRIMARY KEY (npi)
        """,
        """
        CREATE TABLE Location (
            location_id STRING(MAX) NOT NULL,
            city STRING(MAX),
            state STRING(MAX),
            address STRING(MAX)
        ) PRIMARY KEY (location_id)
        """,
        """
        CREATE TABLE Specialty (
            name STRING(MAX) NOT NULL
        ) PRIMARY KEY (name)
        """,
        """
        CREATE TABLE PracticesAt (
            provider_npi INT64 NOT NULL,
            location_id STRING(MAX) NOT NULL,
            FOREIGN KEY (provider_npi) REFERENCES Provider(npi),
            FOREIGN KEY (location_id) REFERENCES Location(location_id)
        ) PRIMARY KEY (provider_npi, location_id)
        """,
        """
        CREATE TABLE LocatedIn (
            org_npi INT64 NOT NULL,
            location_id STRING(MAX) NOT NULL,
            FOREIGN KEY (org_npi) REFERENCES Organization(npi),
            FOREIGN KEY (location_id) REFERENCES Location(location_id)
        ) PRIMARY KEY (org_npi, location_id)
        """,
        """
        CREATE TABLE HasSpecialty (
            provider_npi INT64 NOT NULL,
            specialty_name STRING(MAX) NOT NULL,
            FOREIGN KEY (provider_npi) REFERENCES Provider(npi),
            FOREIGN KEY (specialty_name) REFERENCES Specialty(name)
        ) PRIMARY KEY (provider_npi, specialty_name)
        """,
        """
        CREATE PROPERTY GRAPH HealthcareGraph
        NODE TABLES (
            Provider,
            Organization,
            Location,
            Specialty
        )
        EDGE TABLES (
            PracticesAt
                SOURCE KEY (provider_npi) REFERENCES Provider(npi)
                DESTINATION KEY (location_id) REFERENCES Location(location_id)
                LABEL PRACTICES_AT,
            LocatedIn
                SOURCE KEY (org_npi) REFERENCES Organization(npi)
                DESTINATION KEY (location_id) REFERENCES Location(location_id)
                LABEL LOCATED_IN,
            HasSpecialty
                SOURCE KEY (provider_npi) REFERENCES Provider(npi)
                DESTINATION KEY (specialty_name) REFERENCES Specialty(name)
                LABEL HAS_SPECIALTY
        )
        """
    ]

    print(f"Creating database {database_id} on instance {instance_id}...")
    try:
        database = instance.database(database_id, ddl_statements=ddl_statements)
        operation = database.create()
        operation.result(120)
        print("Database and Schema created.")
    except Exception as e:
        print(f"Schema creation failed (might already exist): {e}")


def fetch_cms_data(npi_list):
    """Fetches Medicare Assignment and Specialty from CMS Provider Data API for a list of NPIs."""
    results = {}
    chunk_size = 50
    for i in range(0, len(npi_list), chunk_size):
        chunk = npi_list[i:i+chunk_size]
        npi_filter = ",".join(chunk)
        url = f"https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0?filter[npi]={npi_filter}&limit=100"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                for row in data.get("results", []):
                    npi = int(row.get("npi"))
                    assgn = row.get("ind_assgn")
                    spec = row.get("pri_spec")
                    results[npi] = {"assignment": assgn, "specialty": spec}
        except Exception as e:
            print("CMS API fetch failed:", e)
    return results


def load_nppes_data(instance_id, database_id, project_id, csv_path=None, limit=None):
    spanner_client = spanner.Client(project=project_id)
    instance = spanner_client.instance(instance_id)
    database = instance.database(database_id)
    
    if not csv_path:
        print("Please provide the path to the NPPES CSV file.")
        return

    print(f"Starting bulk load from {csv_path}...")
    
    providers_raw = []
    orgs = []
    locations = []
    practices = []
    located_in = []
    
    batch_size = 1000
    count = 0
    
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            npi = int(row.get('NPI', 0))
            entity_type = row.get('Entity Type Code', '')
            if not npi or not entity_type:
                continue
                
            city = row.get('Provider Business Practice Location Address City Name', '')
            state = row.get('Provider Business Practice Location Address State Name', '')
            address = row.get('Provider First Line Business Practice Location Address', '')
            location_id = f"{address}_{city}_{state}".replace(" ", "_").upper()
            
            if location_id and location_id != "__":
                locations.append((location_id, city, state, address))
            
            if entity_type == '1':  # Individual Provider
                first = row.get('Provider First Name', '')
                last = row.get('Provider Last Name (Legal Name)', '')
                cred = row.get('Provider Credential Text', '')
                providers_raw.append((npi, f"{first} {last}".strip(), cred))
                
                if location_id and location_id != "__":
                    practices.append((npi, location_id))
                    
            elif entity_type == '2':  # Organization
                org_name = row.get('Provider Organization Name (Legal Business Name)', '')
                orgs.append((npi, org_name))
                
                if location_id and location_id != "__":
                    located_in.append((npi, location_id))
                    
            count += 1
            if count % batch_size == 0:
                _commit_batch(database, providers_raw, orgs, locations, practices, located_in)
                providers_raw, orgs, locations, practices, located_in = [], [], [], [], []
                print(f"Processed {count} rows...")
                
            if limit and count >= limit:
                break
                
    _commit_batch(database, providers_raw, orgs, locations, practices, located_in)
    print(f"Finished loading {count} records!")


def _commit_batch(database, providers_raw, orgs, locations, practices, located_in):
    unique_locations = list({loc[0]: loc for loc in locations}.values())
    
    npi_list = [str(p[0]) for p in providers_raw]
    cms_data = fetch_cms_data(npi_list) if npi_list else {}
    
    providers = []
    specialties = []
    has_specialty = []
    
    for npi, name, cred in providers_raw:
        cms_info = cms_data.get(npi, {})
        assgn_raw = cms_info.get("assignment", "")
        
        if assgn_raw == "Y":
            assignment = "Participating"
        elif assgn_raw in ["N", "M"]:
            assignment = "Non-Participating"
        else:
            assignment = "Unknown"
            
        providers.append((npi, name, cred, assignment))
        
        spec_name = cms_info.get("specialty")
        if spec_name:
            # Capitalize each word for cleaner strings (e.g. OPHTHALMOLOGY -> Ophthalmology)
            spec_name = spec_name.title()
            specialties.append((spec_name,))
            has_specialty.append((npi, spec_name))
            
    # Deduplicate specialties
    unique_specialties = list({s[0]: s for s in specialties}.values())
    
    def insert_mutations(transaction):
        if unique_locations:
            transaction.insert_or_update(
                table='Location',
                columns=('location_id', 'city', 'state', 'address'),
                values=unique_locations
            )
        if unique_specialties:
            transaction.insert_or_update(
                table='Specialty',
                columns=('name',),
                values=unique_specialties
            )
        if providers:
            transaction.insert_or_update(
                table='Provider',
                columns=('npi', 'name', 'credential', 'medicare_assignment'),
                values=providers
            )
        if orgs:
            transaction.insert_or_update(
                table='Organization',
                columns=('npi', 'name'),
                values=orgs
            )
        if practices:
            transaction.insert_or_update(
                table='PracticesAt',
                columns=('provider_npi', 'location_id'),
                values=practices
            )
        if located_in:
            transaction.insert_or_update(
                table='LocatedIn',
                columns=('org_npi', 'location_id'),
                values=located_in
            )
        if has_specialty:
            transaction.insert_or_update(
                table='HasSpecialty',
                columns=('provider_npi', 'specialty_name'),
                values=has_specialty
            )
            
    if any([unique_locations, providers, orgs, practices, located_in, unique_specialties, has_specialty]):
        database.run_in_transaction(insert_mutations)


if __name__ == "__main__":
    PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "profitscout-lx6bb")
    INSTANCE_ID = os.environ.get("SPANNER_INSTANCE_ID", "healthcare-instance")
    DATABASE_ID = "healthcare-db"
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_schema(INSTANCE_ID, DATABASE_ID, PROJECT_ID)
    elif len(sys.argv) > 2 and sys.argv[1] == "load":
        csv_path = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
        load_nppes_data(INSTANCE_ID, DATABASE_ID, PROJECT_ID, csv_path, limit)
    else:
        print("Usage:")
        print("  python load_nppes_bulk.py create")
        print("  python load_nppes_bulk.py load <path_to_csv> [limit]")
