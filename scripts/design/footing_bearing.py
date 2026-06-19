import logging
from aeclib.us.structural.load_combinations.generic import get_load_combinations
from aeclib.us.structural.foundations.generic import validate_bearing_pressure

logger = logging.getLogger("aeckit")

def calculate_peak_bearing_pressure(
    width_ft: float,
    length_ft: float,
    thickness_in: float,
    footing_depth_ft: float,
    soil_unit_weight_pcf: float,
    axial_load_kips: float,
    accidental_eccentricity_in: float = 1.0,
    concrete_unit_weight_pcf: float = 150.0
) -> float:
    """
    Computes the peak service soil bearing pressure at the base of the footing,
    accounting for footing self-weight, soil overburden, and accidental eccentricities.
    """
    thickness_ft = thickness_in / 12.0
    
    # 1. Footing self-weight
    footing_weight = width_ft * length_ft * thickness_ft * (concrete_unit_weight_pcf / 1000.0)
    
    # 2. Soil overburden weight (above footing up to grade)
    soil_height = max(0.0, footing_depth_ft - thickness_ft)
    soil_weight = width_ft * length_ft * soil_height * (soil_unit_weight_pcf / 1000.0)
    
    # 3. Total service axial load at the base of footing (kips)
    P_total = axial_load_kips + footing_weight + soil_weight
    
    # 4. Eccentricities (accidental construction tolerance, converted to feet)
    e_width = accidental_eccentricity_in / 12.0
    e_length = accidental_eccentricity_in / 12.0
    
    # 5. Peak soil pressure using elastic two-way eccentricity formula (no liftoff since e << kern)
    base_pressure = (P_total * 1000.0) / (width_ft * length_ft) # psf
    q_max = base_pressure * (1.0 + (6.0 * e_width / width_ft) + (6.0 * e_length / length_ft))
    
    return q_max


def footing_bearing(project_data: dict) -> dict:
    """
    AECKit workflow script that sizes the plan dimensions of each spread footing
    to satisfy soil bearing capacity checks under all ASD load combinations.
    """
    foundations = project_data.get("foundations", {})
    spread_footings = foundations.get("spread_footings", {})
    instances = spread_footings.get("instances", {})
    
    if not instances:
        return {
            "analysis_type": "footing_bearing",
            "status": "FAIL",
            "error": "No footing instances found under foundations.spread_footings.instances."
        }
        
    materials = spread_footings.get("materials", {})
    geotechnical = spread_footings.get("geotechnical", {})
    constraints = spread_footings.get("design_constraints", {})
    
    # Read geotechnical inputs
    allowable_bearing = geotechnical.get("allowable_bearing_capacity_psf", 1500.0)
    soil_weight_pcf = geotechnical.get("soil_unit_weight_pcf", 120.0)
    
    # Read design constraints (with fallbacks)
    min_width = constraints.get("minimum_width_ft", 3.0)
    min_thickness = constraints.get("minimum_thickness_in", 12.0)
    aspect_ratio = constraints.get("target_aspect_ratio", 1.0)
    increment = constraints.get("sizing_increment_ft", 0.5)
    
    reports = {}
    
    for footing_id, footing_data in instances.items():
        logger.info(f"Sizing footing base for {footing_id}...")
        
        dims = footing_data.get("dimensions", {})
        depth_ft = dims.get("footing_depth_ft", 3.0)
        
        loads = footing_data.get("loads", {})
        dead_kips = loads.get("dead_kips", 0.0)
        live_kips = loads.get("live_kips", 0.0)
        
        # 1. Resolve service load combinations (ASD)
        # Using the standard combinations from aeclib
        combinations = get_load_combinations(
            dead={"P": dead_kips},
            live={"P": live_kips},
            method="ASD"
        )
        
        # 2. Sizing Optimization Loop
        width_ft = min_width
        thickness_in = min_thickness
        
        passed = False
        max_pressure_final = 0.0
        
        # Safety limit to prevent infinite loops
        max_iterations = 100
        iteration = 0
        
        while not passed and iteration < max_iterations:
            iteration += 1
            length_ft = width_ft * aspect_ratio
            
            # Check all combinations
            temp_passed = True
            temp_max_pressure = 0.0
            
            for case_id, case_data in combinations.items():
                p_asd = case_data["values"].get("P", 0.0)
                
                # Calculate pressure
                q_max = calculate_peak_bearing_pressure(
                    width_ft=width_ft,
                    length_ft=length_ft,
                    thickness_in=thickness_in,
                    footing_depth_ft=depth_ft,
                    soil_unit_weight_pcf=soil_weight_pcf,
                    axial_load_kips=p_asd
                )
                
                temp_max_pressure = max(temp_max_pressure, q_max)
                
                # Validate using aeclib presumptive rules
                res = validate_bearing_pressure(
                    design_bearing_pressure=q_max,
                    soil_class=None # Falls back to allowable default from geotechnical if none specified
                )
                
                # But we have explicit allowable bearing in our project geotechnical SSoT, so check it:
                if q_max > allowable_bearing:
                    temp_passed = False
                    
            if temp_passed:
                passed = True
                max_pressure_final = temp_max_pressure
            else:
                width_ft += increment
                
        if not passed:
            logger.error(f"Sizing failed to converge for footing {footing_id}.")
            return {
                "analysis_type": "footing_bearing",
                "status": "FAIL",
                "error": f"Sizing failed to converge for footing {footing_id}."
            }
            
        # 3. Store derived dimensions back into footing data
        length_ft = width_ft * aspect_ratio
        footing_data["dimensions"]["width_ft"] = width_ft
        footing_data["dimensions"]["length_ft"] = length_ft
        footing_data["dimensions"]["thickness_in"] = thickness_in
        
        reports[footing_id] = {
            "status": "PASS",
            "derived_width_ft": width_ft,
            "derived_length_ft": length_ft,
            "thickness_in": thickness_in,
            "max_bearing_pressure_psf": round(max_pressure_final, 1),
            "allowable_bearing_capacity_psf": allowable_bearing
        }
        
    return {
        "analysis_type": "footing_bearing",
        "status": "PASS",
        "results": reports,
        "building_updates": {
            "foundations": {
                "spread_footings": spread_footings
            }
        }
    }
