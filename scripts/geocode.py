from helpers.web import make_web_request

def geocode(project_data: dict) -> dict:
    """
    Extracts the address from the project data and gets coordinates using the US Census Geocoding API.
    Uses the local 'web' helper for cleaner logic.
    """
    address = project_data.get("address")
    if not address:
        return {"error": "Missing 'address' in project data."}
        
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    
    data = make_web_request(url, params=params)
    
    if "error" in data:
        return data

    matches = data.get('result', {}).get('addressMatches', [])
    if not matches:
        return {"error": "No coordinates found for the given address"}
        
    coords = matches[0].get('coordinates', {})
    latitude = coords.get('y')
    longitude = coords.get('x')

    return {
        "analysis_type": "geocoding",
        "latitude": latitude,
        "longitude": longitude,
        "building_updates": {
            "latitude": latitude,
            "longitude": longitude
        }
    }
