import yaml
import math
import numpy as np
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent

def calculate_physics_parameters(yaml_path=SCRIPT_DIR / "00_parameters.yaml"):
    """
    Reads 00_parameters.yaml and calculates the core physics requirements.
    Acts as the Single Source of Truth for all mesh, source, and Par_file scripts.
    """
    with open(yaml_path, "r") as f:
        params = yaml.safe_load(f)

    # 1. Physics Extraction
    mat_steel = params['material_specimen']
    mat_wedge = params['material_wedge']
    t_params = params['transducer']
    sim_params = params['simulation']
    wedge_geom = params['geometry']['wedge_dimensions']

    f0 = float(t_params['f0'])
    f_max = f0  # Account for frequency bandwidth spread
    aperture = float(t_params['aperture'])

    # ---------------------------------------------------------
    # A. MESH SIZE & TRANSDUCER SPATIAL DISTRIBUTION
    # ---------------------------------------------------------
    # Driven by the slowest velocity (Shear wave in Rexolite)
    vs_min = min(mat_steel['vs'], mat_wedge['vs'])
    lambda_min = vs_min / f_max 
    
    mesh_size = lambda_min * 1.0  
    min_element_size = mesh_size / 4.0  # The smallest element in .geo is lc/4.0

    # Calculate Transducer Nodes (Spacing them correctly to map to GLL points)
    gll_spacing = lambda_min * 0.17
    n_sources = int(np.ceil(aperture / gll_spacing)) + 1

    # ---------------------------------------------------------
    # B. TIME STEP (CFL CONDITION) & NSTEP
    # ---------------------------------------------------------
    # Driven by the fastest velocity (P-wave in Steel)
    vp_max = max(mat_steel['vp'], mat_wedge['vp'])
    
    # 0.20 safety factor for unstructured Gmsh quads
    dt_cfl = 0.20 * ((min_element_size * 0.17) / vp_max)

    # Clean the dt number (e.g., 7.312e-10 -> 7.3e-10) for numerical stability
    exponent = np.floor(np.log10(dt_cfl))
    mantissa = np.floor(dt_cfl / (10**exponent) * 10) / 10.0
    dt = mantissa * (10**exponent)

    # Total frames based on requested time
    total_time = sim_params.get('total_time', 0.000050)
    nstep_exact = int(np.ceil(total_time / dt))
    
    # ROUND UP to nearest 100 (Clean logs and eliminates EOF mismatch errors)
    nstep = int(np.ceil(nstep_exact / 100.0)) * 100 

    # ---------------------------------------------------------
    # C. WEDGE GEOMETRY & ANGLE MATH
    # ---------------------------------------------------------
    wedge_angle_rad = math.radians(wedge_geom['wedge_angle'])
    slant_dx = wedge_geom['wedge_l'] - wedge_geom['wedge_l_flat']
    wedge_h_heel = wedge_geom['wedge_h_toe'] + (slant_dx * math.tan(wedge_angle_rad))

    # Center coordinates of the slanted face
    center_x = wedge_geom['wedge_x'] + (slant_dx / 2.0)
    center_z = wedge_geom['wedge_y'] + ((wedge_geom['wedge_h_toe'] + wedge_h_heel) / 2.0)

    # SPECFEM internal forcing angle (where Z points UP)
    specfem_angle = wedge_geom['wedge_angle'] 

    return {
        "mesh_size": mesh_size,
        "gll_spacing": gll_spacing,
        "n_sources": n_sources,
        "dt": dt,
        "nstep": nstep,
        "center_x": center_x,
        "center_z": center_z,
        "wedge_angle_rad": wedge_angle_rad,
        "specfem_angle": specfem_angle
    }

# Quick tester if run directly
if __name__ == "__main__":
    p = calculate_physics_parameters()
    print(f"Mesh Size: {p['mesh_size']*1000:.3f} mm")
    print(f"Time Step (DT): {p['dt']:.2e} s")
    print(f"NSTEP: {p['nstep']}")
    print(f"Sources: {p['n_sources']}")
    print(f"Wedge Center: ({p['center_x']:.4f}, {p['center_z']:.4f}) m")
    print(f"Wedge Angle: {math.degrees(p['wedge_angle_rad']):.2f}° | Specfem Angle: {p['specfem_angle']:.2f}°")