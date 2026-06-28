import yaml
import re
import numpy as np
import math
from pathlib import Path
from physics_utils import calculate_physics_parameters
DATA_DIR = Path(__file__).resolve().parent

with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

# Extract materials and physics
mat_specimen = params['material_specimen']
mat_fluid = params['material_fluid']
t_params = params['transducer']
sim_params = params['simulation']

# ==========================================
# 1. Physics Calculations
# ==========================================
# 1. Get pre-calculated physics
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")

use_gpu = bool(params.get('simulation', {}).get('gpu', {}).get('use_gpu', False))
# Original nproc from YAML (used only if GPU is off)
nproc = params.get('simulation', {}).get('mpi', {}).get('nproc', 1)
# Force serial execution when GPU is enabled
if use_gpu:
    nproc = 1
    print(f"--> GPU enabled: forcing NPROC = 1 in Par_file (serial run)")
else:
    print(f"--> Using {nproc} MPI processes | GPU Enabled: False")

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
par_data = re.sub(r'^GPU_MODE\s*=.*', f'GPU_MODE                         = {".true." if use_gpu else ".false."}', par_data, flags=re.MULTILINE)

#update the mesh file names
par_data = re.sub(r'^mesh_file\s*=.*', f'mesh_file                       = ./DATA/MESH/Mesh_{sim_params["mesh_name"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^nodes_coords_file\s*=.*', f'nodes_coords_file               = ./DATA/MESH/Nodes_{sim_params["mesh_name"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^materials_file\s*=.*', f'materials_file                  = ./DATA/MESH/Material_{sim_params["mesh_name"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^free_surface_file\s*=.*', f'free_surface_file               = ./DATA/MESH/Surf_free_{sim_params["mesh_name"]}', par_data, flags=re.MULTILINE)
par_data = re.sub(r'^absorbing_surface_file\s*=.*', f'absorbing_surface_file          = ./DATA/MESH/Surf_abs_{sim_params["mesh_name"]}', par_data, flags=re.MULTILINE)


# Update Number of Models
par_data = re.sub(r'^nbmodels\s*=.*', 'nbmodels                        = 2', par_data, flags=re.MULTILINE)
# Model 1: WATER (acoustic) -> Physical Surface M1
mat1_line = (f"1 1 {mat_fluid['rho']:.1f}d0 "f"{mat_fluid['vp']:.1f}d0 "f"0 0 0 9999 9999 0 0 0 0 0 0")
par_data = re.sub(r'^\s*1\s+1\s+.*$',mat1_line,par_data,flags=re.MULTILINE)

# Model 2: STEEL (elastic) -> Physical Surface M2
mat2_line = (f"2 1 {mat_specimen['rho']:.1f}d0 "f"{mat_specimen['vp']:.1f}d0 "f"{mat_specimen['vs']:.1f}d0 "f"0 0 9999 9999 0 0 0 0 0 0")
par_data = re.sub(r'^\s*2\s+1\s+.*$',mat2_line,par_data,flags=re.MULTILINE)

# Receiver settings 
receiver_cfg = params.get('receiver', {})

sampling_freq = float(receiver_cfg.get('sampling_frequency', 0.0))
if sampling_freq > 0.0:
    output_dt = 1.0 / sampling_freq
    ntstep_sample = max(1, int(round(output_dt / physics["dt"])))
    actual_freq = 1.0 / (ntstep_sample * physics["dt"])
    print(f"--> Desired output sampling: {sampling_freq*1e-6:.2f} MHz → NTSTEP_BETWEEN_OUTPUT_SAMPLE = {ntstep_sample} "
          f"(actual output rate: {actual_freq*1e-6:.2f} MHz)")
else:
    ntstep_sample = 1   # no down‑sampling
    print("--> No output down‑sampling (NTSTEP_BETWEEN_OUTPUT_SAMPLE = 1)")

seismotype = int(receiver_cfg.get('seismotype', 2))
#The nsetp_seismo has to be teh multiple of ntstep_sample
ntstep_seismos = int(ntstep_sample * 1000)

par_data = re.sub(r'^seismotype\s*=.*',f'seismotype                      = {seismotype}',par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NTSTEP_BETWEEN_OUTPUT_SEISMOS\s*=.*',f'NTSTEP_BETWEEN_OUTPUT_SEISMOS   = {ntstep_seismos}',par_data, flags=re.MULTILINE)
par_data = re.sub(r'^NTSTEP_BETWEEN_OUTPUT_SAMPLE\s*=.*',f'NTSTEP_BETWEEN_OUTPUT_SAMPLE    = {ntstep_sample}',par_data, flags=re.MULTILINE)

with par_path.open("w") as file:
    file.write(par_data)
    
print("--> Par_file successfully updated")