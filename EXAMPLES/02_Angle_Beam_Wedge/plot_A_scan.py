import sys
import yaml
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import importlib.util

# Import the centralized physics brain

EXAMPLE_DIR = Path(__file__).resolve().parent
DATA_DIR = EXAMPLE_DIR / "DATA"

physics_utils_path = DATA_DIR / "physics_utils.py"
spec = importlib.util.spec_from_file_location("physics_utils", str(physics_utils_path))
physics_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(physics_utils)
calculate_physics_parameters = physics_utils.calculate_physics_parameters

try:
    import obspy
except ImportError:
    print("ERROR: obspy is required to read SPECFEM2D SU output.")
    print(f"Install the example dependencies with: {sys.executable} -m pip install -r {EXAMPLE_DIR / 'requirements.txt'}")
    sys.exit(1)

# ==========================================
# 1. LOAD PIPELINE PARAMETERS & PHYSICS
# ==========================================
# Adjust this path if your script is located inside the DATA folder directly
param_file = EXAMPLE_DIR / "DATA" / "00_parameters.yaml" 

with param_file.open("r") as f:
    params = yaml.safe_load(f)

# Request the single source of truth from our helper script
physics = calculate_physics_parameters(param_file)

# Extract the exact DT used by the simulation
time_step = physics['dt']
print(f"--> Extracted Time Step (DT) from physics_utils: {time_step:.2e} s")

# ==========================================
# 2. FILE PATHS & EXTRACTION
# ==========================================
# SPECFEM2D outputs Z-displacement/velocity to Uz_file_single.su
output_file = EXAMPLE_DIR / "OUTPUT_FILES" / "Uz_file_single_v.su"

if not output_file.exists():
    print(f"❌ Error: {output_file} not found.")
    print("Did the simulation finish? Make sure SU_FORMAT = .true. in your Par_file!")
    sys.exit(1)

print(f"Reading SU file: {output_file}...")
st = obspy.read(str(output_file), format="SU", byteorder='<', unpack_trace_headers=True)

# Pulse-Echo has 1 station, so we only need the first trace
trace = st[0].data

n_samples = len(trace)
time_axis_us = np.arange(n_samples) * time_step * 1e6  # Convert seconds to microseconds (µs)

print(f"Loaded 1 receiver with {n_samples} time samples.")

# ==========================================
# 3. SIGNAL PROCESSING & PLOTTING
# ==========================================
# PERCENTILE NORMALIZATION
# Bypasses the massive "Main Bang" source pulse to reveal the smaller echoes
percentile_target = 99.5
norm_factor = np.percentile(np.abs(trace), percentile_target)

# Fallback in case the 99.5th percentile is somehow zero
if norm_factor == 0:
    norm_factor = np.max(np.abs(trace))
    
if norm_factor == 0:
    print("ERROR: The selected trace contains only zero amplitudes.")
    sys.exit(1)

normalized_amplitude = trace / norm_factor

plt.figure(figsize=(10, 4))
plt.plot(time_axis_us, normalized_amplitude, color='#0077B6', linewidth=1.2)

# Professional Formatting
plt.title(f"Pulse-Echo A-Scan ({params['transducer']['f0']/1e6:.2f} MHz in Steel)", fontsize=14, fontweight='bold')
plt.xlabel("Time of Flight (µs)", fontsize=12)
plt.ylabel("Amplitude (% FSH)", fontsize=12)

plt.grid(True, linestyle='--', alpha=0.7)
plt.axhline(0, color='black', linewidth=0.8)  # Center Zero-line
plt.xlim(0, max(time_axis_us))

# Clamping the Y-axis acts like an amplifier saturation limit
# The main bang will shoot past this, allowing the true echoes to be seen clearly
plt.ylim(-1.1, 1.1) 
plt.tight_layout()

# Save and Show
save_path = EXAMPLE_DIR / "A_Scan_Result.png"
plt.savefig(save_path, dpi=300)
print(f"✅ A-Scan successfully plotted and saved to {save_path}")
plt.show()