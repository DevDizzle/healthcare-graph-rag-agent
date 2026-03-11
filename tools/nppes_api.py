import requests
from typing import List, Dict, Any

class NppesApiTool:
    """
    Tool to search the real-time National Plan and Provider Enumeration System (NPPES) API.
    
    Use this tool when the Spanner Graph does not have the provider, or when the user 
    asks for real-time/nationwide data about a specific doctor or organization that might not
    be in the local graph.
    """
    
    def search_nppes(self, first_name: str = "", last_name: str = "", organization_name: str = "", taxonomy_description: str = "", city: str = "", state: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Searches the real-time NPPES API for providers or organizations.
        
        Args:
            first_name (str): Provider's first name (can use * for wildcard).
            last_name (str): Provider's last name.
            organization_name (str): Legal Business Name or DBA for organizations.
            taxonomy_description (str): Provider specialty (e.g., 'Ophthalmology', 'Optometrist').
            city (str): Practice location city.
            state (str): Practice location state (2-letter abbreviation).
            limit (int): Number of results to return (max 200).
            
        Returns:
            List[Dict[str, Any]]: A list of matching providers/organizations.
        """
        base_url = "https://npiregistry.cms.hhs.gov/api/"
        params = {
            "version": "2.1",
            "limit": min(limit, 200)
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
                
            results = []
            for item in data.get("results", []):
                basic = item.get("basic", {})
                addresses = item.get("addresses", [])
                taxonomies = item.get("taxonomies", [])
                
                # Extract primary practice location
                location = next((addr for addr in addresses if addr.get("address_purpose") == "LOCATION"), {})
                
                # Extract specialty descriptions
                specialties = [tax.get("desc") for tax in taxonomies if tax.get("desc")]
                
                provider_info = {
                    "npi": item.get("number"),
                    "type": item.get("enumeration_type"), # NPI-1 or NPI-2
                    "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip() if item.get("enumeration_type") == "NPI-1" else basic.get("organization_name", ""),
                    "credentials": basic.get("credential", ""),
                    "specialties": specialties,
                    "city": location.get("city", ""),
                    "state": location.get("state", ""),
                    "address": location.get("address_1", "")
                }
                results.append(provider_info)
                
            return results
        except requests.exceptions.RequestException as e:
            return [{"error": f"API request failed: {str(e)}"}]
