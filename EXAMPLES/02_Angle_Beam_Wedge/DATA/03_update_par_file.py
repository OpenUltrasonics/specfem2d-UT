import yaml
import re
import numpy as np
from pathlib import Path
from physics_utils import calculate_physics_parameters
DATA_DIR = Path(__file__).resolve().parent

with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

# Extract materials and physics
mat_steel = params['material_specimen']
mat_wedge = params['material_wedge']
t_params = params['transducer']
sim_params = params['simulation']

# ==========================================
# 1. Physics Calculations
# ==========================================
# 1. Get pre-calculated physics
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")

f0 = float(t_params['f0'])
f_max = f0 
nproc = int(params.get('simulation', {}).get('mpi', {}).get('nproc', 1))

# ==========================================
# 2. Update Par_file
# ==========================================
par_path = DATA_DIR / "Par_file"
with par_path.open("r") as file:
    par_data = file.read()

# Update Timesteps & Sources
par_data = re.sub(r'^DT\s*=.*', f'DT                              = {physics["dt"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NSTEP\s*=.*', f'NSTEP                           = {physics["nstep"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NSOURCES\s*=.*', f'NSOURCES                        = {physics["n_sources"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NPROC\s*=.*', f'NPROC                           = {nproc}', par_data, flags=re.MULTILINE)

# Update Number of Models
par_data = re.sub(r'^nbmodels\s*=.*', 'nbmodels                        = 2', par_data, flags=re.MULTILINE)

# Material 1: Steel (Corresponds to Physical Surface 1: M1_Steel)
mat1_line = f"1 1 {mat_steel['rho']:.1f} {mat_steel['vp']:.1f} {mat_steel['vs']:.1f} 0 0 9999 9999 0 0 0 0 0 0"
par_data = re.sub(r'^1\s+1\s+\d.*', mat1_line, par_data, flags=re.MULTILINE)

# Material 2: Rexolite Wedge (Corresponds to Physical Surface 2: M2_Wedge)
mat2_line = f"2 1 {mat_wedge['rho']:.1f} {mat_wedge['vp']:.1f} {mat_wedge['vs']:.1f} 0 0 9999 9999 0 0 0 0 0 0"
par_data = re.sub(r'^2\s+1\s+\d.*', mat2_line, par_data, flags=re.MULTILINE)


with par_path.open("w") as file:
    file.write(par_data)
    
print("--> Par_file successfully updated with Multi-Material properties.")