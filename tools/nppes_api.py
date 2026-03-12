import requests
import json
import urllib.request
import concurrent.futures
from typing import List, Dict, Any

class NppesApiTool:
    """
    Tool to search the real-time National Plan and Provider Enumeration System (NPPES) API.
    
    Use this tool when the Spanner Graph does not have the provider, or when the user 
    asks for real-time/nationwide data about a specific doctor or organization that might not
    be in the local graph.
    """
    
    def _fetch_single_npi_status(self, npi: str) -> Dict[str, str]:
        """Fetches status for a single NPI with timeout."""
        url = f"https://data.cms.gov/provider-data/api/1/datastore/query/mj5m-pzi6/0?conditions[0][property]=npi&conditions[0][value]={npi}&conditions[0][operator]=%3D"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                rows = data.get("results", [])
                if rows:
                    assgn_raw = rows[0].get("ind_assgn", "")
                    if assgn_raw == "Y":
                        return {npi: "Participating"}
                    elif assgn_raw in ["N", "M"]:
                        return {npi: "Non-Participating"}
        except Exception as e:
            print(f"Warning: CMS Medicare lookup failed for NPI {npi}: {e}")
        return {npi: "Unknown"}

    def _fetch_cms_medicare_status(self, npi_list: List[str]) -> Dict[str, str]:
        """Helper to fetch Medicare Assignment status in parallel."""
        if not npi_list:
            return {}
            
        results = {}
        # Limit enrichment to top 5 to keep response time fast for demo
        npi_to_fetch = npi_list[:5]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_npi = {executor.submit(self._fetch_single_npi_status, npi): npi for npi in npi_to_fetch}
            for future in concurrent.futures.as_completed(future_to_npi):
                try:
                    res = future.result()
                    results.update(res)
                except Exception:
                    pass
                    
        return results

    def search_nppes(self, first_name: str = "", last_name: str = "", organization_name: str = "", taxonomy_description: str = "", city: str = "", state: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the real-time NPPES API for providers or organizations.
        
        Args:
            first_name (str): Provider's first name (can use * for wildcard).
            last_name (str): Provider's last name.
            organization_name (str): Legal Business Name or DBA for organizations.
            taxonomy_description (str): Provider specialty (e.g., 'Ophthalmology', 'Optometrist').
            city (str): Practice location city.
            state (str): Practice location state (2-letter abbreviation).
            limit (int): Number of results to return (max 200). Default 5 for demo performance.
            
        Returns:
            List[Dict[str, Any]]: A list of matching providers/organizations.
        """
        base_url = "https://npiregistry.cms.hhs.gov/api/"
        params = {
            "version": "2.1",
            "limit": min(limit, 10) # Strictly limit for demo reliability
        }
        
        if first_name: params["first_name"] = first_name
        if last_name: params["last_name"] = last_name
        if organization_name: params["organization_name"] = organization_name
        if taxonomy_description: params["taxonomy_description"] = taxonomy_description
        if city: params["city"] = city
        if state: params["state"] = state
        
        # We need at least one search criterion besides version and limit
        if len(params) <= 2:
            return [{"error": "You must provide at least one search parameter (e.g., first_name, last_name, organization_name, taxonomy_description)."}]
            
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "Errors" in data:
                return [{"error": data["Errors"]}]
                
            npi_list = []
            raw_results = []
            
            # First pass: parse NPPES and collect NPIs
            for item in data.get("results", []):
                npi = str(item.get("number"))
                npi_list.append(npi)
                
                basic = item.get("basic", {})
                addresses = item.get("addresses", [])
                taxonomies = item.get("taxonomies", [])
                
                # Extract primary practice location
                location = next((addr for addr in addresses if addr.get("address_purpose") == "LOCATION"), {})
                
                # Extract specialty descriptions
                specialties = [tax.get("desc") for tax in taxonomies if tax.get("desc")]
                
                provider_info = {
                    "npi": npi,
                    "type": item.get("enumeration_type"), # NPI-1 or NPI-2
                    "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip() if item.get("enumeration_type") == "NPI-1" else basic.get("organization_name", ""),
                    "credentials": basic.get("credential", ""),
                    "specialties": specialties,
                    "city": location.get("city", ""),
                    "state": location.get("state", ""),
                    "address": location.get("address_1", "")
                }
                raw_results.append(provider_info)
                
            # Second pass: fetch Medicare status and merge
            cms_status_map = self._fetch_cms_medicare_status(npi_list)
            
            final_results = []
            for provider in raw_results:
                npi = provider["npi"]
                provider["medicare_assignment"] = cms_status_map.get(npi, "Unknown")
                final_results.append(provider)
                
            return final_results
        except requests.exceptions.RequestException as e:
            return [{"error": f"API request failed: {str(e)}"}]
