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
    mat_specimen = params['material_specimen']
    mat_fluid = params['material_fluid']
    t_params = params['transducer']
    sim_params = params['simulation']

    f0 = float(t_params['f0'])
    f_max = f0 * 1.8  #  buffer for bandwidth spread of the toneburst
    aperture = float(t_params['aperture'])

    # ---------------------------------------------------------
    # A. MESH SIZE (Based on the absolute slowest wave)
    # ---------------------------------------------------------
    # The slowest wave in the entire model dictates the mesh size. 
    # In immersion testing, the Fluid P-wave (~1500 m/s) is slower than the Steel S-wave (~3200 m/s). 
    v_min = min(mat_fluid['vp'], mat_specimen['vs'])
    lambda_min = v_min / f_max 
    
    # For SPECFEM (Degree 4), 1 element per wavelength gives ~5 points/wavelength.
    # We use 1.6 as a safety factor to ensure highly accurate wave shapes.
    mesh_size = lambda_min / 1.6  

    # ---------------------------------------------------------
    # B. SOURCE SPATIAL DISTRIBUTION (Axisymmetry)
    # ---------------------------------------------------------
    # For an axisymmetric transducer, the array spans from X=0 to X=radius.
    radius = aperture / 2.0
    
    # To avoid spatial aliasing, we place a point source at least once per GLL node.
    # Average spacing between GLL nodes is roughly mesh_size / 4.0
    avg_gll_spacing = mesh_size / 4.0
    n_sources = int(np.ceil(radius / avg_gll_spacing)) + 1

    # ---------------------------------------------------------
    # C. TIME STEP (CFL STABILITY CONDITION)
    # ---------------------------------------------------------
    # Driven by the absolute fastest wave (P-wave in Steel)
    v_max = max(mat_specimen['vp'], mat_fluid['vp'])
    
    # The shortest distance between two GLL points in a degree-4 element is ~0.17 * mesh_size
    min_gll_distance = 0.17 * mesh_size
    
    # CFL Condition: dt <= C * (dx_min / V_max), where C is typically 0.3 for SPECFEM2D
    dt_cfl = 0.30 * (min_gll_distance / v_max)

    # Clean the dt number (e.g., 1.28e-8 -> 1.2e-8) for numerical safety in the Par_file
    exponent = np.floor(np.log10(dt_cfl))
    mantissa = np.floor(dt_cfl / (10**exponent) * 10) / 10.0
    dt = mantissa * (10**exponent)

    # ---------------------------------------------------------
    # D. TOTAL STEPS (NSTEP)
    # ---------------------------------------------------------
    total_time = sim_params.get('total_time', 0.000050)
    nstep_exact = int(np.ceil(total_time / dt))
    
    # Round up to nearest 100 for clean log outputs
    nstep = int(np.ceil(nstep_exact / 100.0)) * 100 

    return {
        "mesh_size": mesh_size,
        "n_sources": n_sources,
        "dt": dt,
        "nstep": nstep,
        "v_min": v_min,
        "v_max": v_max,
        "radius": radius
    }

# Quick tester if run directly
if __name__ == "__main__":
    p = calculate_physics_parameters()
    print(f"Slowest Wave: {p['v_min']} m/s | Fastest Wave: {p['v_max']} m/s")
    print(f"Optimal Mesh Size (lc): {p['mesh_size']*1000:.3f} mm")
    print(f"Time Step (DT): {p['dt']:.2e} s")
    print(f"NSTEP: {p['nstep']}")
    print(f"Axisymmetric Sources: {p['n_sources']}")