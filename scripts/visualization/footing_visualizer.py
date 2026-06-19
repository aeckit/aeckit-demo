import json
from pathlib import Path

def generate_box_object(x_size: float, y_size: float, z_min: float, z_max: float, color: str, opacity: float) -> dict:
    """
    Generates a 3D box wireframe and transparent solid mesh face definition.
    """
    x_half = x_size / 2.0
    y_half = y_size / 2.0
    
    vertices = [
        [-x_half, -y_half, z_min], # 0
        [x_half, -y_half, z_min],  # 1
        [x_half, y_half, z_min],   # 2
        [-x_half, y_half, z_min],  # 3
        [-x_half, -y_half, z_max], # 4
        [x_half, -y_half, z_max],  # 5
        [x_half, y_half, z_max],   # 6
        [-x_half, y_half, z_max]   # 7
    ]
    
    edges = [
        [0, 1], [1, 2], [2, 3], [3, 0], # Bottom loop
        [4, 5], [5, 6], [6, 7], [7, 4], # Top loop
        [0, 4], [1, 5], [2, 6], [3, 7]  # Verticals
    ]
    
    faces = [
        [0, 3, 2, 1], # Bottom
        [4, 5, 6, 7], # Top
        [0, 1, 5, 4], # South (-Y)
        [1, 2, 6, 5], # East (+X)
        [2, 3, 7, 6], # North (+Y)
        [3, 0, 4, 7]  # West (-X)
    ]
    
    return {
        "color": color,
        "opacity": opacity,
        "vertices": vertices,
        "edges": edges,
        "faces": faces
    }


def generate_footing_geometry(
    width_ft: float,
    length_ft: float,
    thickness_in: float,
    footing_depth_ft: float,
    column_width_in: float,
    column_length_in: float,
    concrete_cover_in: float = 3.0,
    reinforcement: dict = None
) -> dict:
    """
    Generates 3D box meshes (footing and column) and rebar grids for the footing visualization.
    """
    t_ft = thickness_in / 12.0
    z_bottom = -footing_depth_ft
    z_top = z_bottom + t_ft
    
    objects = []
    
    # 1. Concrete Footing Box (Transparent Gray)
    footing_box = generate_box_object(width_ft, length_ft, z_bottom, z_top, "#9ca3af", 0.25)
    objects.append(footing_box)
    
    # 2. Column Box (Semi-transparent Amber/Brown)
    column_box = generate_box_object(column_width_in / 12.0, column_length_in / 12.0, z_top, 1.0, "#d97706", 0.75)
    objects.append(column_box)
    
    # 3. Steel Reinforcement Layout
    if reinforcement:
        rebar_diameter_map = {
            3: 0.375,
            4: 0.500,
            5: 0.625,
            6: 0.750,
            7: 0.875,
            8: 1.000,
            9: 1.128,
            10: 1.270,
            11: 1.410,
        }
        
        d_cover = concrete_cover_in / 12.0
        
        # A. Long Direction Rebar (Spans in Y, distributed in X)
        long_reinf = reinforcement.get("long_direction", {})
        bar_size = long_reinf.get("bar_size", 5)
        bar_count = long_reinf.get("bar_count", 0)
        d_bar = rebar_diameter_map.get(bar_size, 0.625) / 12.0
        
        z_bar_long = z_bottom + d_cover + d_bar / 2.0
        
        if bar_count > 0:
            if bar_count > 1:
                spacing_ft = (width_ft - 2.0 * d_cover - d_bar) / (bar_count - 1)
            else:
                spacing_ft = 0.0
                
            x_start = -width_ft / 2.0 + d_cover + d_bar / 2.0
            y_start = -length_ft / 2.0 + d_cover
            y_end = length_ft / 2.0 - d_cover
            
            verts_long = []
            edges_long = []
            
            for i in range(bar_count):
                x_i = x_start + i * spacing_ft
                idx = len(verts_long)
                verts_long.append([x_i, y_start, z_bar_long])
                verts_long.append([x_i, y_end, z_bar_long])
                edges_long.append([idx, idx + 1])
                
            objects.append({
                "color": "#0284c7", # Sky blue
                "vertices": verts_long,
                "edges": edges_long
            })
            
        # B. Short Direction Rebar (Spans in X, distributed in Y, sits on top of long bars)
        short_reinf = reinforcement.get("short_direction", {})
        bar_size_short = short_reinf.get("bar_size", 5)
        bar_count_short = short_reinf.get("bar_count", 0)
        d_bar_short = rebar_diameter_map.get(bar_size_short, 0.625) / 12.0
        
        z_bar_short = z_bar_long + d_bar / 2.0 + d_bar_short / 2.0
        
        if bar_count_short > 0:
            if bar_count_short > 1:
                spacing_ft_short = (length_ft - 2.0 * d_cover - d_bar_short) / (bar_count_short - 1)
            else:
                spacing_ft_short = 0.0
                
            y_start_short = -length_ft / 2.0 + d_cover + d_bar_short / 2.0
            x_start_short = -width_ft / 2.0 + d_cover
            x_end_short = width_ft / 2.0 - d_cover
            
            verts_short = []
            edges_short = []
            
            for j in range(bar_count_short):
                y_j = y_start_short + j * spacing_ft_short
                idx = len(verts_short)
                verts_short.append([x_start_short, y_j, z_bar_short])
                verts_short.append([x_end_short, y_j, z_bar_short])
                edges_short.append([idx, idx + 1])
                
            objects.append({
                "color": "#10b981", # Emerald green
                "vertices": verts_short,
                "edges": edges_short
            })
            
    return {
        "objects": objects
    }


def footing_visualizer(project_data: dict) -> dict:
    """
    AECKit workflow script that reads the set of spread footings from project_data,
    generates 3D geometries, and writes them to the visualizations/ folder.
    """
    foundations = project_data.get("foundations", {})
    spread_footings = foundations.get("spread_footings", {})
    instances = spread_footings.get("instances", {})
    
    if not instances:
        return {
            "analysis_type": "footing_visualizer",
            "status": "FAIL",
            "error": "No footing instances found under foundations.spread_footings.instances."
        }
        
    materials = spread_footings.get("materials", {})
    concrete_cover_in = materials.get("concrete_cover_in", 3.0)
        
    # Resolve active project directory from the .aeckit context config
    try:
        with open(".aeckit", "r") as f:
            config = json.load(f)
        company = config["company"]
        project = config["project"]
    except Exception:
        # Fallbacks for safety
        company = "demo"
        project = "spread-footing"
        
    viz_dir = Path("companies") / company / project / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for footing_id, footing_data in instances.items():
        dims = footing_data.get("dimensions", {})
        reinforcement = footing_data.get("reinforcement")
        
        # Read dimensions
        width = dims.get("width_ft")
        length = dims.get("length_ft")
        thickness = dims.get("thickness_in")
        depth = dims.get("footing_depth_ft")
        col_w = dims.get("column_width_in")
        col_l = dims.get("column_length_in")
        
        if None in (width, length, thickness, depth, col_w, col_l):
            print(f"Skipping {footing_id} due to missing dimensions.")
            continue
            
        # Generate geometry JSON
        geometry = generate_footing_geometry(
            width_ft=width,
            length_ft=length,
            thickness_in=thickness,
            footing_depth_ft=depth,
            column_width_in=col_w,
            column_length_in=col_l,
            concrete_cover_in=concrete_cover_in,
            reinforcement=reinforcement
        )
        
        # Write file
        file_path = viz_dir / f"{footing_id}.viz.json"
        with open(file_path, "w") as f:
            json.dump(geometry, f, indent=4)
            
        generated_files.append(str(file_path))
        print(f"Generated visualization: {file_path}")
        
    return {
        "analysis_type": "footing_visualizer",
        "status": "PASS",
        "generated_files": generated_files
    }
