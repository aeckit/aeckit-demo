import logging
from aeclib.us.structural.load_combinations.generic import get_load_combinations
from aeclib.us.structural.concrete.shear import (
    calculate_one_way_shear_capacity,
    calculate_two_way_shear_capacity,
)

logger = logging.getLogger("aeckit")

def footing_shear(project_data: dict) -> dict:
    """
    AECKit workflow script that verifies and sizes footing thickness (thickness_in)
    to satisfy LRFD shear requirements (one-way and two-way punching shear) under factored loads.
    """
    foundations = project_data.get("foundations", {})
    spread_footings = foundations.get("spread_footings", {})
    instances = spread_footings.get("instances", {})
    
    if not instances:
        return {
            "analysis_type": "footing_shear",
            "status": "FAIL",
            "error": "No footing instances found under foundations.spread_footings.instances."
        }
        
    materials = spread_footings.get("materials", {})
    constraints = spread_footings.get("design_constraints", {})
    
    concrete_strength_psi = materials.get("concrete_strength_psi", 3000.0)
    concrete_cover_in = materials.get("concrete_cover_in", 3.0)
    min_thickness = constraints.get("minimum_thickness_in", 12.0)
    
    reports = {}
    
    for footing_id, footing_data in instances.items():
        logger.info(f"Designing footing thickness for shear for {footing_id}...")
        
        dims = footing_data.get("dimensions", {})
        width_ft = dims.get("width_ft")
        length_ft = dims.get("length_ft")
        col_width_in = dims.get("column_width_in", 5.5)
        col_length_in = dims.get("column_length_in", 5.5)
        
        if not width_ft or not length_ft:
            logger.error(f"Missing plan dimensions for footing {footing_id}. Ensure footing_bearing.py runs first.")
            return {
                "analysis_type": "footing_shear",
                "status": "FAIL",
                "error": f"Missing plan dimensions for footing {footing_id}."
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
        
        thickness_in = dims.get("thickness_in", min_thickness)
        
        passed = False
        iteration = 0
        max_iterations = 50
        
        one_way_governing_ratio = 0.0
        two_way_governing_ratio = 0.0
        
        while not passed and iteration < max_iterations:
            iteration += 1
            
            # Effective depth: assume No. 6 bar (0.75 in diameter) as default for d calculation
            d_in = thickness_in - concrete_cover_in - 0.375
            if d_in <= 0:
                thickness_in += 2.0
                continue
                
            d_ft = d_in / 12.0
            
            temp_passed = True
            temp_one_way_ratio = 0.0
            temp_two_way_ratio = 0.0
            
            for case_id, case_data in combinations.items():
                p_u_column = case_data["values"].get("P", 0.0)
                
                # Accidental minimum eccentricity (1.0 inch in both directions)
                e_width = 1.0 / 12.0 # ft
                e_length = 1.0 / 12.0 # ft
                
                # Net factored pressure (caused by column load alone)
                net_base_pressure = p_u_column / (width_ft * length_ft) # ksf
                qu_max = net_base_pressure * (1.0 + (6.0 * e_width / width_ft) + (6.0 * e_length / length_ft))
                
                # A. One-Way Shear Checks
                # Length direction overhang
                cantilever_length_ft = (length_ft - (col_length_in / 12.0)) / 2.0
                overhang_shear_length_ft = cantilever_length_ft - d_ft
                
                # Width direction overhang
                cantilever_width_ft = (width_ft - (col_width_in / 12.0)) / 2.0
                overhang_shear_width_ft = cantilever_width_ft - d_ft
                
                # Vu for one-way shear
                Vu_one_way_length = 0.0
                if overhang_shear_length_ft > 0:
                    Vu_one_way_length = qu_max * width_ft * overhang_shear_length_ft # kips
                    
                Vu_one_way_width = 0.0
                if overhang_shear_width_ft > 0:
                    Vu_one_way_width = qu_max * length_ft * overhang_shear_width_ft # kips
                    
                # Capacity in kips
                phiVc_one_way_length = calculate_one_way_shear_capacity(concrete_strength_psi, width_ft * 12.0, d_in)
                phiVc_one_way_width = calculate_one_way_shear_capacity(concrete_strength_psi, length_ft * 12.0, d_in)
                
                ratio_length = Vu_one_way_length / phiVc_one_way_length if phiVc_one_way_length > 0 else 99.0
                ratio_width = Vu_one_way_width / phiVc_one_way_width if phiVc_one_way_width > 0 else 99.0
                
                temp_one_way_ratio = max(temp_one_way_ratio, ratio_length, ratio_width)
                
                if ratio_length > 1.0 or ratio_width > 1.0:
                    temp_passed = False
                    
                # B. Two-Way Punching Shear Check
                # Area inside the critical perimeter at d/2
                crit_col_w_ft = (col_width_in + d_in) / 12.0
                crit_col_l_ft = (col_length_in + d_in) / 12.0
                area_inside_ft2 = crit_col_w_ft * crit_col_l_ft
                
                # Tributary area for punching
                area_trib_punch_ft2 = max(0.0, (width_ft * length_ft) - area_inside_ft2)
                Vu_punch = qu_max * area_trib_punch_ft2 # kips
                
                phiVc_punch = calculate_two_way_shear_capacity(
                    concrete_strength_psi,
                    col_width_in,
                    col_length_in,
                    d_in,
                    column_type="interior"
                )
                
                ratio_punch = Vu_punch / phiVc_punch if phiVc_punch > 0 else 99.0
                temp_two_way_ratio = max(temp_two_way_ratio, ratio_punch)
                
                if ratio_punch > 1.0:
                    temp_passed = False
                    
            if temp_passed:
                passed = True
                one_way_governing_ratio = temp_one_way_ratio
                two_way_governing_ratio = temp_two_way_ratio
            else:
                thickness_in += 2.0 # Increment by 2 inches
                
        if not passed:
            logger.error(f"Thickness sizing failed to converge for footing {footing_id}.")
            return {
                "analysis_type": "footing_shear",
                "status": "FAIL",
                "error": f"Thickness sizing failed to converge for footing {footing_id}."
            }
            
        # 3. Store updated thickness in footing data
        footing_data["dimensions"]["thickness_in"] = thickness_in
        
        reports[footing_id] = {
            "status": "PASS",
            "thickness_in": thickness_in,
            "effective_depth_in": round(thickness_in - concrete_cover_in - 0.375, 3),
            "one_way_shear_demand_capacity_ratio": round(one_way_governing_ratio, 3),
            "two_way_shear_demand_capacity_ratio": round(two_way_governing_ratio, 3),
        }
        
    return {
        "analysis_type": "footing_shear",
        "status": "PASS",
        "results": reports,
        "building_updates": {
            "foundations": {
                "spread_footings": spread_footings
            }
        }
    }
