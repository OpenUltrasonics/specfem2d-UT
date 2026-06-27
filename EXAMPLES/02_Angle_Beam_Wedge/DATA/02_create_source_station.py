import yaml
import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import the centralized physics brain
from physics_utils import calculate_physics_parameters

DATA_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = DATA_DIR.parent
CUSTOM_SOURCE_FILE = DATA_DIR / "source_time_function.txt"

# ==========================================
# 1. LOAD PARAMETERS & PHYSICS
# ==========================================
with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

# Request the single source of truth from our helper script
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")

dt = physics['dt']
nstep = physics['nstep']
n_sources = physics['n_sources']
center_x = physics['center_x']
center_z = physics['center_z']
wedge_angle_rad = physics['wedge_angle_rad']
specfem_angle =  physics['specfem_angle']

t_params = params['transducer']
f0 = float(t_params['f0'])
aperture = float(t_params['aperture'])
total_factor = float(t_params['total_factor'])

apodization = str(t_params.get('apodization', 'uniform')).lower()
use_custom_source = bool(t_params.get('use_custom_source', False))
window_type = str(t_params.get('window_type', 'hanning')).lower()
num_cycles = int(t_params.get('num_cycles', 3))

print(f"--> Transducer Aperture: {aperture*1000:.1f} mm | GLL Spacing: {physics['gll_spacing']*1000:.3f} mm")
print(f"--> Automatically generating {n_sources} point sources (Angle: {params['geometry']['wedge_dimensions']['wedge_angle']}°)")
print(f"--> Time Step (DT): {dt:.2e} s | NSTEP: {nstep}")

def create_custom_source_file(dt_val, nstep_val):
    # This guarantees EXACTLY 'nstep' rows
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
        elif window_type == "gaussian":
            sigma = burst_duration / 6.0
            window = np.exp(-0.5 * ((active_time - burst_duration / 2.0) / sigma) ** 2)
            window /= np.max(window)
        elif window_type == "rectangular":
            window = np.ones(active_count)
        else:
            raise ValueError(f"Unsupported window_type '{window_type}'.")

        amplitude[active] = carrier * window
        max_amplitude = np.max(np.abs(amplitude))
        if max_amplitude > 0:
            amplitude /= max_amplitude

    data = np.column_stack((time, amplitude))
    np.savetxt(CUSTOM_SOURCE_FILE, data, fmt="%.12e %.12e")
    print(f"--> Custom source file generated: {nstep_val} rows, {num_cycles} cycles, {window_type} window")
    return CUSTOM_SOURCE_FILE.relative_to(EXAMPLE_DIR).as_posix()

# ==========================================
# 2. WRITE SOURCE & STATIONS FILES
# ==========================================
source_time_function_type = 1
source_file_name = '""'

if use_custom_source:
    source_file_name = create_custom_source_file(dt, nstep)
    source_time_function_type = 8

# Create the spatial array ALONG THE SLANT
s_array = np.linspace(-aperture/2, aperture/2, n_sources)
xs_array = center_x + s_array * math.cos(wedge_angle_rad)
zs_array = center_z + s_array * math.sin(wedge_angle_rad)

# Apply Apodization Shape based on distance from center
if apodization == "gaussian":
    weights = np.exp(-0.5 * (s_array / (aperture/8.0)) ** 2)
else: # Uniform
    weights = np.ones(n_sources)

# Normalize so the TOTAL energy injected equals total_factor
weights_normalized = weights / np.sum(weights)

with (DATA_DIR / "SOURCE").open("w") as f:
    f.write(f"# Finite Width Transducer ({n_sources} nodes, {apodization} apodization)\n")
    for i, (x, z, w) in enumerate(zip(xs_array, zs_array, weights_normalized), 1):
        f.write(f"## Source {i}\n")
        f.write(f"source_surf = .false.\n")    # MUST BE FALSE SO Z IS RESPECTED
        f.write(f"xs = {x:.6f}\n")
        f.write(f"zs = {z:.6f}\n")
        f.write(f"source_type = 1\n")
        f.write(f"time_function_type = {source_time_function_type}\n")
        f.write(f"name_of_source_file = {source_file_name}\n")
        f.write(f"burst_band_width = 0.\n")
        f.write(f"f0 = {f0:.1f}\n")
        f.write(f"tshift = 0.0\n")
        f.write(f"anglesource = {specfem_angle:.2f}\n")
        f.write(f"Mxx = 0.\nMzz = 1.0\nMxz = 0.\n")
        f.write(f"factor = {total_factor * w:.6e}\n")
        f.write(f"vx = 0.0\nvz = 0.0\n\n")

with (DATA_DIR / "STATIONS").open("w") as f:
    f.write(f"S0001     UT       {center_x:.6f}  {center_z:.6f}  0.0        0.0\n")

print("--> SOURCE and STATIONS text files generated.")
# ==========================================
# 3. GENERATE VISUAL CONFIRMATION PLOT
# ==========================================
print("--> Generating Input Source Preview Plot...")

if use_custom_source:
    source_preview = np.loadtxt(CUSTOM_SOURCE_FILE)
    time_ax = source_preview[:, 0]
    pulse = source_preview[:, 1]
else:
    t_shift = 1.2 / f0
    t_end = 3.0 * t_shift
    time_ax = np.linspace(0, t_end, 1000)
    a = np.pi * f0 * (time_ax - t_shift)
    pulse = (1.0 - 2.0 * a**2) * np.exp(-a**2)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

# Panel 1: Time Domain Pulse
ax1.plot(time_ax * 1e6, pulse, color='#D62828', linewidth=2)
ax1.set_title(f"Custom Tone Burst ({f0/1e6:.2f} MHz, {num_cycles} cycles)" if use_custom_source else f"Time-Domain Pulse ({f0/1e6:.2f} MHz Ricker)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Time (µs)", fontsize=10)
ax1.set_ylabel("Normalized Amplitude", fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.axhline(0, color='black', linewidth=0.8)

# Panel 2: 2D Spatial Layout of the Slanted Array
sc = ax2.scatter(xs_array * 1000, zs_array * 1000, c=weights_normalized, cmap='Reds', s=40, edgecolor='black', zorder=5)
ax2.plot(xs_array * 1000, zs_array * 1000, color='black', linestyle='--', alpha=0.5)

# Visual vector math to point the arrow perfectly INTO the wedge in Matplotlib space
dx = math.sin(wedge_angle_rad) * 3 
dz = -math.cos(wedge_angle_rad) * 3 
ax2.arrow(center_x*1000, center_z*1000, dx, dz, head_width=0.6, head_length=0.8, fc='#0077B6', ec='#0077B6', zorder=10)

ax2.set_aspect('equal')
ax2.set_title(f"Transducer Placement (Angle: {params['geometry']['wedge_dimensions']['wedge_angle']}°)", fontsize=12, fontweight='bold')
ax2.set_xlabel("X Position (mm)", fontsize=10)
ax2.set_ylabel("Z Position (mm)", fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.6)
cbar = plt.colorbar(sc, ax=ax2)
cbar.set_label('Apodization Weight')

plt.tight_layout()
plot_path = EXAMPLE_DIR / "Preview_Input_Source.png"
plt.savefig(plot_path, dpi=200)
print(f"✅ Saved visual confirmation to: Preview_Input_Source.png")