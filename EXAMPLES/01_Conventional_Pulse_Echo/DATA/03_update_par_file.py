import yaml
import re
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

# ==========================================
# 1. Physics Calculations
# ==========================================
f_max = params['transducer']['f0'] * 2.5
lambda_min = params['material']['vs'] / f_max

# Ensure this perfectly matches 01_create_mesh.py and 02_create_source_station.py
mesh_size = lambda_min * 1.0  
min_element_size = mesh_size / 3.0  # .geo uses lc/3.0 near the defect

# CFL Time Step calculation (Using 0.20 safety factor for unstructured Gmsh quads)
dt_cfl = 0.20 * ((min_element_size * 0.17) / params['material']['vp'])
exponent = np.floor(np.log10(dt_cfl))
mantissa = np.floor(dt_cfl / (10**exponent) * 10) / 10.0
dt = mantissa * (10**exponent)

# NSTEP Calculation (Check if your YAML uses 'total_time' or 'time_record')
total_time = params['simulation'].get('total_time', params['simulation'].get('time_record'))
nstep = int(np.ceil(total_time / dt))

# --- DYNAMIC NSOURCES CALCULATION ---
# Calculate how many nodes sit under the transducer to update the Par_file
aperture = float(params['transducer']['aperture'])
gll_spacing = mesh_size / 4.0 
n_sources = int(np.ceil(aperture / gll_spacing)) + 1

print(f"--> Calculated DT: {dt:.2e} | NSTEP: {nstep} | NSOURCES: {n_sources}")


# ==========================================
# 2. Update Par_file
# ==========================================
par_path = DATA_DIR / "Par_file"
with par_path.open("r") as file:
    par_data = file.read()

# Update Timesteps & Sources
par_data = re.sub(r'^DT\s*=.*', f'DT                              = {dt}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NSTEP\s*=.*', f'NSTEP                           = {nstep}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NSOURCES\s*=.*', f'NSOURCES                        = {n_sources}', par_data, flags=re.MULTILINE)

# Update Material 1
mat_line = f"1 1 {params['material']['rho']:.1f} {params['material']['vp']:.1f} {params['material']['vs']:.1f} 0 0 9999 9999 0 0 0 0 0 0"
par_data = re.sub(r'^1\s+1\s+\d.*', mat_line, par_data, flags=re.MULTILINE)

# Route Mesh Paths
mesh_name = params['simulation']['mesh_name']
base_path = f"./DATA/MESH/Mesh"  # LibGmsh2Specfem prepends "Mesh_" by default
par_data = re.sub(r'^mesh_file\s*=.*', f'mesh_file                       = {base_path}_{mesh_name}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^nodes_coords_file\s*=.*', f'nodes_coords_file               = ./DATA/MESH/Nodes_{mesh_name}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^materials_file\s*=.*', f'materials_file                  = ./DATA/MESH/Material_{mesh_name}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^free_surface_file\s*=.*', f'free_surface_file               = ./DATA/MESH/Surf_free_{mesh_name}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^absorbing_surface_file\s*=.*', f'absorbing_surface_file          = ./DATA/MESH/Surf_abs_{mesh_name}', par_data, flags=re.MULTILINE)

with par_path.open("w") as file:
    file.write(par_data)
    
print("--> Par_file successfully updated.")