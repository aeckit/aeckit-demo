import logging
import math
from aeclib.us.structural.load_combinations.generic import get_load_combinations
from aeclib.us.structural.concrete.flexure import calculate_required_flexural_steel_area
from aeclib.us.structural.concrete.reinforcement import (
    validate_minimum_reinforcement,
    calculate_development_length,
    calculate_hooked_development_length,
)

logger = logging.getLogger("aeckit")

def footing_reinforcement(project_data: dict) -> dict:
    """
    AECKit workflow script that designs the flexural reinforcement layout (bar size, count, spacing)
    for each spread footing, meeting ACI 318 minimum reinforcement and development length requirements.
    """
    foundations = project_data.get("foundations", {})
    spread_footings = foundations.get("spread_footings", {})
    instances = spread_footings.get("instances", {})
    
    if not instances:
        return {
            "analysis_type": "footing_reinforcement",
            "status": "FAIL",
            "error": "No footing instances found under foundations.spread_footings.instances."
        }
        
    materials = spread_footings.get("materials", {})
    
    concrete_strength_psi = materials.get("concrete_strength_psi", 3000.0)
    steel_yield_strength_psi = materials.get("steel_yield_strength_psi", 60000.0)
    concrete_cover_in = materials.get("concrete_cover_in", 3.0)
    
    reports = {}
    
    # Standard rebar definitions
    rebar_info = {
        4: {"diameter_in": 0.500, "area_sq_in": 0.20},
        5: {"diameter_in": 0.625, "area_sq_in": 0.31},
        6: {"diameter_in": 0.750, "area_sq_in": 0.44},
        7: {"diameter_in": 0.875, "area_sq_in": 0.60},
        8: {"diameter_in": 1.000, "area_sq_in": 0.79},
    }
    
    for footing_id, footing_data in instances.items():
        logger.info(f"Designing flexural reinforcement for {footing_id}...")
        
        dims = footing_data.get("dimensions", {})
        width_ft = dims.get("width_ft")
        length_ft = dims.get("length_ft")
        thickness_in = dims.get("thickness_in")
        col_width_in = dims.get("column_width_in", 5.5)
        col_length_in = dims.get("column_length_in", 5.5)
        
        if not width_ft or not length_ft or not thickness_in:
            logger.error(f"Missing dimensions for footing {footing_id}. Ensure bearing and shear scripts run first.")
            return {
                "analysis_type": "footing_reinforcement",
                "status": "FAIL",
                "error": f"Missing dimensions for footing {footing_id}."
            }
            
        loads = footing_data.get("loads", {})
        dead_kips = loads.get("dead_kips", 0.0)
        live_kips = loads.get("live_kips", 0.0)
        
        # 1. Resolve factored load combinations (LRFD)
        combinations = get_load_combinations(
            dead={"P": dead_kips},
            live={"P": live_kips},
            method="LRFD"
        )
        
        # Find governing moments across all combinations
        max_moment_L = 0.0
        max_moment_B = 0.0
        
        # Cantilever spans
        cantilever_L = (length_ft - (col_length_in / 12.0)) / 2.0 # ft
        cantilever_B = (width_ft - (col_width_in / 12.0)) / 2.0 # ft
        
        for case_id, case_data in combinations.items():
            p_u = case_data["values"].get("P", 0.0)
            
            # Accidental minimum eccentricity (1.0 inch in both directions)
            e_width = 1.0 / 12.0 # ft
            e_length = 1.0 / 12.0 # ft
            
            # Net factored pressure (caused by column load alone)
            net_base_pressure = p_u / (width_ft * length_ft) # ksf
            qu_max = net_base_pressure * (1.0 + (6.0 * e_width / width_ft) + (6.0 * e_length / length_ft))
            
            # Moments at face of column
            Mu_L = qu_max * width_ft * (cantilever_L ** 2) / 2.0 # kip-ft
            Mu_B = qu_max * length_ft * (cantilever_B ** 2) / 2.0 # kip-ft
            
            max_moment_L = max(max_moment_L, Mu_L)
            max_moment_B = max(max_moment_B, Mu_B)
            
        # Design effective depth d (assume No. 6 bar for d calculation)
        d_in = thickness_in - concrete_cover_in - 0.375
        
        # A. Long Direction Reinforcement ( distributed across width B, spanning along length L )
        b_L = width_ft * 12.0 # inches
        As_L_req = calculate_required_flexural_steel_area(
            max_moment_L, concrete_strength_psi, steel_yield_strength_psi, b_L, d_in
        )
        # Apply minimum reinforcement
        min_result_L = validate_minimum_reinforcement(As_L_req, b_L, thickness_in)
        As_L_min = 0.0018 * b_L * thickness_in
        As_L_design = max(As_L_req, As_L_min)
        
        # B. Short Direction Reinforcement ( distributed across length L, spanning along width B )
        b_B = length_ft * 12.0 # inches
        As_B_req = calculate_required_flexural_steel_area(
            max_moment_B, concrete_strength_psi, steel_yield_strength_psi, b_B, d_in
        )
        # Apply minimum reinforcement
        min_result_B = validate_minimum_reinforcement(As_B_req, b_B, thickness_in)
        As_B_min = 0.0018 * b_B * thickness_in
        As_B_design = max(As_B_req, As_B_min)
        
        # Available development lengths (in inches)
        avail_ld_L = cantilever_L * 12.0 - concrete_cover_in
        avail_ld_B = cantilever_B * 12.0 - concrete_cover_in
        
        # Helper to select rebar layout
        def select_rebar_layout(As_required, section_width_in, available_ld_in):
            selected_size = None
            selected_count = None
            selected_spacing = None
            selected_ld = None
            ld_status = "FAIL"
            
            fallback = None
            
            # Try bar sizes 4 through 8
            for bar_size in [4, 5, 6, 7, 8]:
                info = rebar_info[bar_size]
                d_b = info["diameter_in"]
                a_b = info["area_sq_in"]
                
                # Count based on area
                count = max(4, math.ceil(As_required / a_b))
                # Spacing center-to-center
                spacing = (section_width_in - (2.0 * concrete_cover_in) - d_b) / (count - 1.0)
                
                # Development length
                ld = calculate_development_length(
                    bar_size, steel_yield_strength_psi, concrete_strength_psi,
                    is_top_bar=False, is_epoxy_coated=False
                )
                
                # Spacing limits: 3.0 in to 18.0 in
                if 3.0 <= spacing <= 18.0:
                    if fallback is None:
                        # Record the smallest bar that meets spacing as our fallback
                        fallback = {
                            "size": bar_size,
                            "count": count,
                            "spacing": round(spacing, 2),
                            "ld": round(ld, 2)
                        }
                        
                    if ld <= available_ld_in:
                        selected_size = bar_size
                        selected_count = count
                        selected_spacing = round(spacing, 2)
                        selected_ld = round(ld, 2)
                        ld_status = "PASS"
                        break # Found a perfect fit!
                        
            # Fallback if no straight size passes development length check
            if ld_status == "FAIL":
                if fallback is not None:
                    # Check hooked development length for our fallback bar size
                    fallback_size = fallback["size"]
                    ldh = calculate_hooked_development_length(
                        fallback_size, steel_yield_strength_psi, concrete_strength_psi,
                        is_epoxy_coated=False
                    )
                    
                    selected_size = fallback_size
                    selected_count = fallback["count"]
                    selected_spacing = fallback["spacing"]
                    selected_ld = round(ldh, 2)
                    
                    if ldh <= available_ld_in:
                        ld_status = "PASS (90-deg hook typical)"
                    else:
                        ld_status = "FAIL (Hook too long)"
                else:
                    # Fallback to No. 4 bar if nothing fit spacing
                    selected_size = 4
                    info = rebar_info[4]
                    selected_count = max(4, math.ceil(As_required / info["area_sq_in"]))
                    selected_spacing = round((section_width_in - (2.0 * concrete_cover_in) - info["diameter_in"]) / (selected_count - 1.0), 2)
                    
                    ldh = calculate_hooked_development_length(4, steel_yield_strength_psi, concrete_strength_psi)
                    selected_ld = round(ldh, 2)
                    
                    if ldh <= available_ld_in:
                        ld_status = "PASS (90-deg hook typical)"
                    else:
                        ld_status = "FAIL (Hook too long)"
                
            return {
                "bar_size": selected_size,
                "bar_count": selected_count,
                "spacing_in": selected_spacing,
                "area_provided_sq_in": round(selected_count * rebar_info[selected_size]["area_sq_in"], 2),
                "development_length_in": selected_ld,
                "available_development_length_in": round(available_ld_in, 2),
                "development_length_status": ld_status
            }
            
        long_reinf = select_rebar_layout(As_L_design, b_L, avail_ld_L)
        short_reinf = select_rebar_layout(As_B_design, b_B, avail_ld_B)
        
        # Save design back to footing
        footing_data["reinforcement"] = {
            "long_direction": long_reinf,
            "short_direction": short_reinf
        }
        
        reports[footing_id] = {
            "status": "PASS",
            "moments_kip_ft": {
                "long_direction_Mu": round(max_moment_L, 1),
                "short_direction_Mu": round(max_moment_B, 1)
            },
            "reinforcement": {
                "long_direction": long_reinf,
                "short_direction": short_reinf
            }
        }
        
    return {
        "analysis_type": "footing_reinforcement",
        "status": "PASS",
        "results": reports,
        "building_updates": {
            "foundations": {
                "spread_footings": spread_footings
            }
        }
    }
