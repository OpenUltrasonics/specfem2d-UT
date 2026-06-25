import yaml
import re
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
EXAMPLE_DIR = DATA_DIR.parent
CUSTOM_SOURCE_FILE = DATA_DIR / "source_time_function.txt"

# ==========================================
# 1. LOAD PARAMETERS & PHYSICS
# ==========================================
with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

t_params = params['transducer']
f0 = float(t_params['f0'])
aperture = float(t_params['aperture'])
center_x = float(t_params['center_x'])
zs = float(t_params['zs'])
total_factor = float(t_params['total_factor'])

apodization = str(t_params.get('apodization', 'uniform')).lower()
use_custom_source = bool(t_params.get('use_custom_source', False))
window_type = str(t_params.get('window_type', 'hanning')).lower()
num_cycles = int(t_params.get('num_cycles', 3))

# --- DYNAMIC NODE CALCULATION ---
# We calculate the distance between GLL nodes on the mesh surface to place a source exactly on each node.
vs = float(params['material']['vs'])
f_max = f0 * 2.5
lambda_min = vs / f_max
mesh_size = lambda_min * 1.0           # Same as in 01_create_mesh.py
gll_spacing = mesh_size / 4.0          # SPECFEM2D N=4 means 5 nodes per element edge (4 gaps)

n_sources = int(np.ceil(aperture / gll_spacing)) + 1
print(f"--> Transducer Aperture: {aperture*1000:.1f} mm | GLL Spacing: {gll_spacing*1000:.3f} mm")
print(f"--> Automatically generating {n_sources} point sources to model physical crystal.")


def read_par_value(name, cast):
    par_text = (DATA_DIR / "Par_file").read_text()
    match = re.search(rf"^{name}\s*=\s*([^\s#]+)", par_text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find {name} in DATA/Par_file")
    return cast(match.group(1).replace("d", "e").replace("D", "e"))

def create_custom_source_file(dt, nstep):
    time = np.arange(nstep) * dt
    amplitude = np.zeros(nstep)
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
    print(f"--> Custom source file generated: {nstep} rows, {num_cycles} cycles, {window_type} window")
    return CUSTOM_SOURCE_FILE.relative_to(EXAMPLE_DIR).as_posix()

# ==========================================
# 2. WRITE SOURCE & STATIONS FILES
# ==========================================
source_time_function_type = 1
source_file_name = '""'

if use_custom_source:
    dt = read_par_value("DT", float)
    nstep = read_par_value("NSTEP", int)
    source_file_name = create_custom_source_file(dt, nstep)
    source_time_function_type = 8

# Create the spatial array
xs_array = np.linspace(center_x - aperture/2, center_x + aperture/2, n_sources)

# Apply Apodization Shape
if apodization == "gaussian":
    weights = np.exp(-0.5 * ((xs_array - center_x) / (aperture/8.0)) ** 2)
else: # Uniform
    weights = np.ones(n_sources)

# Normalize so the TOTAL energy injected equals total_factor, preventing mesh-dependent blowups
weights_normalized = weights / np.sum(weights)

with (DATA_DIR / "SOURCE").open("w") as f:
    f.write(f"# Finite Width Transducer ({n_sources} nodes, {apodization} apodization)\n")
    for i, (x, w) in enumerate(zip(xs_array, weights_normalized), 1):
        f.write(f"## Source {i}\nsource_surf = .true.\nxs = {x:.6f}\nzs = {zs:.6f}\n")
        f.write(f"source_type = 1\ntime_function_type = {source_time_function_type}\nname_of_source_file = {source_file_name}\n")
        f.write(f"burst_band_width = 0.\nf0 = {f0:.1f}\ntshift = 0.0\nanglesource = 0.0\n")
        f.write(f"Mxx = 0.\nMzz = 1.0\nMxz = 0.\nfactor = {total_factor * w:.6e}\nvx = 0.0\nvz = 0.0\n\n")

with (DATA_DIR / "STATIONS").open("w") as f:
    f.write(f"S0001           UT       {center_x:.6f}  {zs:.6f}  0.0        0.0\n")

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
if use_custom_source:
    ax1.set_title(f"Custom Tone Burst ({f0/1e6:.2f} MHz, {num_cycles} cycles)", fontsize=12, fontweight='bold')
else:
    ax1.set_title(f"Time-Domain Pulse ({f0/1e6:.2f} MHz Ricker)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Time (µs)", fontsize=10)
ax1.set_ylabel("Normalized Amplitude", fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.axhline(0, color='black', linewidth=0.8)

# Panel 2: Spatial Apodization
marker_size = 100 if n_sources < 20 else 20
ax2.scatter(xs_array * 1000, weights_normalized, color='#0077B6', s=marker_size, zorder=5)
ax2.plot(xs_array * 1000, weights_normalized, color='#0077B6', linestyle='-', alpha=0.8)
ax2.fill_between(xs_array * 1000, 0, weights_normalized, color='#0077B6', alpha=0.2)
ax2.set_title(f"Spatial Apodization ({n_sources} Nodes, {apodization.title()})", fontsize=12, fontweight='bold')
ax2.set_xlabel("X Position on Block (mm)", fontsize=10)
ax2.set_ylabel("Relative Amplitude Weight", fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_ylim(0, max(weights_normalized) * 1.1)

plt.tight_layout()
plot_path = EXAMPLE_DIR / "Preview_Input_Source.png"
plt.savefig(plot_path, dpi=200)
print(f"✅ Saved visual confirmation to: Preview_Input_Source.png")