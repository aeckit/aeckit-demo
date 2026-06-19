from helpers.web import make_web_request

def seismic_hazards(project_data: dict) -> dict:
    """
    Fetches seismic design parameters from the USGS Seismic Design Web Services.
    Requires 'latitude' and 'longitude' at the root of project_data.
    """
    lat = project_data.get("latitude")
    lng = project_data.get("longitude")
    
    if not lat or not lng:
        return {"error": "Missing 'latitude' or 'longitude' in project data. Run geocode first."}

    # Engineering parameters directly from project data (with defaults)
    risk_cat = project_data.get("risk_category", "II")
    site_class = project_data.get("site_class", "D")
    
    base_url = "https://earthquake.usgs.gov/ws/designmaps/asce7-16.json"
    params = {
        "latitude": lat,
        "longitude": lng,
        "riskCategory": risk_cat,
        "siteClass": site_class,
        "title": project_data.get("name", "Fissure Project")
    }
    
    data = make_web_request(base_url, params=params)
    
    if not data or "error" in data:
        return data or {"error": "Empty response from USGS API."}
        
    # USGS response structure: data['response']['data']
    # Safely navigate the nested dictionary
    response = data.get("response")
    if response is None:
        return {"error": f"API returned success but 'response' is null. Full data: {data}"}
        
    usgs_data = response.get("data")
    if not usgs_data:
        return {"error": "Seismic data for this location is not available in the ASCE 7-16 standard."}

    # Extract design factors
    seismic_factors = {
        "ss": usgs_data.get("ss"),
        "s1": usgs_data.get("s1"),
        "sds": usgs_data.get("sds"),
        "sd1": usgs_data.get("sd1"),
        "sms": usgs_data.get("sms"),
        "sm1": usgs_data.get("sm1"),
        "seismic_design_category": usgs_data.get("seismicDesignCategory")
    }

    return {
        "analysis_type": "seismic_hazards",
        "parameters_used": {
            "risk_category": risk_cat,
            "site_class": site_class
        },
        "results": seismic_factors,
        "project_updates": {
            "seismic": seismic_factors,
            "risk_category": risk_cat,
            "site_class": site_class
        }
    }
