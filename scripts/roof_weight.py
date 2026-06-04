def roof_weight(project_data: dict) -> dict:
    """
    Asks the user for the roof weight and returns updates for the project data.
    """
    try:
        weight_input = input("How much weight is in the roof (in lbs)? ")
        weight = float(weight_input)
    except ValueError:
        return {"error": "Invalid weight entered. Please enter a number."}

    return {
        "analysis_type": "roof_weight",
        "results": {
            "roof_weight": weight
        },
        "building_updates": {
            "metadata": {
                "roof_weight": weight
            }
        }
    }
