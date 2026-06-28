import yaml
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# IMPORT THE BRAIN
from physics_utils import calculate_physics_parameters

DATA_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = DATA_DIR.parent
CUSTOM_SOURCE_FILE = DATA_DIR / "source_time_function.txt"

# ==========================================
# 1. LOAD PARAMETERS & PHYSICS
# ==========================================
with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

# The single source of truth calculates all geometry and time rules
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")

dt = physics['dt']
nstep = physics['nstep']
n_sources = physics['n_sources']  
radius = physics['radius']

t_params = params['transducer']
f0 = float(t_params['f0'])
total_factor = float(t_params['total_factor'])

use_custom_source = bool(t_params.get('use_custom_source', False))
window_type = str(t_params.get('window_type', 'hanning')).lower()
num_cycles = int(t_params.get('num_cycles', 1))

# DYNAMIC FIX: Read the exact tank depth from the YAML geometry
tank_z = float(params.get('geometry', {}).get('tank_dimensions', {}).get('tank_depth', 0.050))
Z_SURFACE = tank_z  # Perfectly glues the array to the top boundary

print(f"--> Tank Top Boundary detected at Z = {Z_SURFACE*1000:.1f} mm")

print(f"--> Using DT={dt:.2e}, NSTEP={nstep}, and {n_sources} Source Nodes.")

def create_custom_source_file(dt_val, nstep_val):
    time = np.arange(nstep_val) * dt_val
    amplitude = np.zeros(nstep_val)
    
    burst_duration = num_cycles / f0
    active = time <= burst_duration
    active_count = int(np.count_nonzero(active))

    if active_count > 0:
        active_time = time[active]
        carrier = np.sin(2.0 * np.pi * f0 * active_time)

        if window_type in ("hanning", "hann"):
            window = np.hanning(active_count)
        else:
            window = np.ones(active_count)

        amplitude[active] = carrier * window
        max_amplitude = np.max(np.abs(amplitude))
        if max_amplitude > 0:
            amplitude /= max_amplitude

    data = np.column_stack((time, amplitude))
    np.savetxt(CUSTOM_SOURCE_FILE, data, fmt="%.12e %.12e")
    return CUSTOM_SOURCE_FILE.relative_to(EXAMPLE_DIR).as_posix()

# ==========================================
# 2. WRITE SOURCE & STATIONS FILES
# ==========================================
source_time_function_type = 1
source_file_name = '""'

if use_custom_source:
    source_file_name = create_custom_source_file(dt, nstep+100)
    source_time_function_type = 8

# Axisymmetric Spatial Array (Starts at 1 micron to avoid divide-by-zero singularity!)
xs_array = np.linspace(1e-6, radius, n_sources)
zs_array = np.full(n_sources, Z_SURFACE)

# CRITICAL AXISYMMETRY MATH: Area Weighting
weights = xs_array.copy()
weights[0] = weights[1] / 2.0 
weights_normalized = weights / np.sum(weights)

with (DATA_DIR / "SOURCE").open("w") as f:
    f.write(f"# Axisymmetric Immersion Transducer ({n_sources} nodes)\n")
    for i, (x, z, w) in enumerate(zip(xs_array, zs_array, weights_normalized), 1):
        f.write(f"## Source {i}\n")
        f.write(f"source_surf = .false.\n")   
        f.write(f"xs = {x:.6f}\n")
        f.write(f"zs = {z:.6f}\n")
        f.write(f"source_type = 1\n")
        f.write(f"time_function_type = {source_time_function_type}\n")
        f.write(f"name_of_source_file = {source_file_name}\n")
        f.write(f"burst_band_width = 0.\n")
        f.write(f"f0 = {f0:.1f}\n")
        f.write(f"tshift = 0.0\n")
        f.write(f"anglesource = 0.0\n")
        f.write(f"Mxx = 1.0\nMzz = 1.0\nMxz = 0.\n") 
        f.write(f"factor = {total_factor * w:.6e}\n")
        f.write(f"vx = 0.0\nvz = 0.0\n\n")

# STATIONS
with (DATA_DIR / "STATIONS").open("w") as f:
    for i, (x, z) in enumerate(zip(xs_array, zs_array), 1):
        f.write(f"S{i:04d}     UT       {x:.6f}  {z:.6f}  0.0        0.0\n")

print("--> SOURCE and STATIONS text files generated.")

# ==========================================
# 3. GENERATE VISUAL CONFIRMATION PLOT
# ==========================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

ax1.plot(xs_array * 1000, weights_normalized, color='#D62828', marker='o', linewidth=2)
ax1.set_title("Radial Area Weighting (Axisymmetry)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Radius from Center (mm)", fontsize=10)
ax1.set_ylabel("Force Amplitude Weight", fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.6)

sc = ax2.scatter(xs_array * 1000, zs_array * 1000, c=weights_normalized, cmap='Reds', s=40, edgecolor='black', zorder=5)
ax2.axvline(0, color='blue', linestyle='--', label='Axis of Symmetry (X=0)')
ax2.set_xlim(-1, (radius*1000) + 2)
ax2.set_ylim((Z_SURFACE*1000) - 2, (Z_SURFACE*1000) + 2)
ax2.set_title("Axisymmetric Transducer Placement", fontsize=12, fontweight='bold')
ax2.set_xlabel("Radial Position X (mm)", fontsize=10)
ax2.set_ylabel("Depth Z (mm)", fontsize=10)
ax2.legend()
ax2.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plot_path = EXAMPLE_DIR / "Preview_Input_Source.png"
plt.savefig(plot_path, dpi=200)
print(f"✅ Saved visual confirmation to: Preview_Input_Source.png")