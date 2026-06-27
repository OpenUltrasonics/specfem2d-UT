import sys
import re
import yaml
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

try:
    import obspy
except ImportError:
    print("ERROR: obspy is required to read SPECFEM2D SU output.")
    sys.exit(1)

# ==========================================
# 1. FILE PATHS
# ==========================================
EXAMPLE_DIR = Path(__file__).resolve().parent
DATA_DIR = EXAMPLE_DIR / "DATA"
PAR_FILE  = DATA_DIR / "Par_file"
YAML_FILE = DATA_DIR / "00_parameters.yaml"

# ==========================================
# 2. READ PARAMETERS FROM YAML (for title, etc.)
# ==========================================
with YAML_FILE.open("r") as f:
    params = yaml.safe_load(f)

f0_MHz = params['transducer']['f0'] / 1e6

# ==========================================
# 3. READ SIMULATION PARAMETERS FROM Par_file
# ==========================================
par_text = PAR_FILE.read_text()

# DT
match_dt = re.search(r'^DT\s*=\s*([\d\.eEdD+\-]+)', par_text, re.MULTILINE)
if not match_dt:
    print("❌ Could not find DT in Par_file")
    sys.exit(1)
raw_dt = float(match_dt.group(1).replace('d','e').replace('D','e'))

# NTSTEP_BETWEEN_OUTPUT_SAMPLE
match_nt = re.search(r'^NTSTEP_BETWEEN_OUTPUT_SAMPLE\s*=\s*(\d+)', par_text, re.MULTILINE)
if not match_nt:
    print("❌ Could not find NTSTEP_BETWEEN_OUTPUT_SAMPLE in Par_file, assuming 1 (no downsampling)")
    ntstep_sample = 1
else:
    ntstep_sample = int(match_nt.group(1))

# Seismotype (for correct SU filename)
match_seis = re.search(r'^seismotype\s*=\s*(\d+)', par_text, re.MULTILINE)
if not match_seis:
    print("❌ Could not find seismotype in Par_file, assuming 2 (velocity)")
    seismotype = 2
else:
    seismotype = int(match_seis.group(1))

dt_effective = raw_dt * ntstep_sample
actual_freq = 1.0 / dt_effective
print(f"--> Seismotype: {seismotype}")
print(f"--> DT = {raw_dt:.3e} s  |  NTSTEP_BETWEEN_OUTPUT_SAMPLE = {ntstep_sample}")
print(f"--> Effective dt = {dt_effective:.3e} s  (output rate = {actual_freq*1e-6:.3f} MHz)")

# ==========================================
# 4. DETERMINE CORRECT SU FILE BASED ON SEISMOTYPE
# ==========================================
# Mapping: seismotype -> SU output filename
su_file_map = {
    1: "Uz_file_single.su",      # displacement
    2: "Uz_file_single_v.su",    # velocity
    3: "Uz_file_single_a.su",    # acceleration
    4: "Up_file_single_p.su",    # pressure
    5: "Uz_file_single_c.su",    # curl of displacement
    6: "Uz_file_single_f.su",    # fluid potential
}

if seismotype not in su_file_map:
    print(f"❌ Unsupported seismotype {seismotype}. Cannot determine SU file.")
    sys.exit(1)

output_file = EXAMPLE_DIR / "OUTPUT_FILES" / su_file_map[seismotype]

if not output_file.exists():
    print(f"❌ Error: {output_file} not found.")
    print("Did the simulation finish? Make sure SU_FORMAT = .true. in your Par_file!")
    sys.exit(1)

print(f"Reading SU file: {output_file}...")

# ==========================================
# 5. LOAD SU FILE AND AVERAGE TRACES
# ==========================================
st = obspy.read(str(output_file), format="SU", byteorder='<', unpack_trace_headers=True)

n_traces = len(st)
if n_traces == 0:
    print("❌ No traces found.")
    sys.exit(1)

print(f"Loaded {n_traces} receiver(s).")

traces = np.array([tr.data for tr in st])
n_samples = traces.shape[1]
mean_trace = np.mean(traces, axis=0)

time_axis_us = np.arange(n_samples) * dt_effective * 1e6
print(f"Time span: {time_axis_us[0]:.2f} – {time_axis_us[-1]:.2f} µs, {n_samples} samples")

# ==========================================
# 6. SIGNAL PROCESSING & PLOTTING
# ==========================================
percentile_target = 99.5
norm_factor = np.percentile(np.abs(mean_trace), percentile_target)

if norm_factor == 0:
    norm_factor = np.max(np.abs(mean_trace))
if norm_factor == 0:
    print("ERROR: The selected trace contains only zero amplitudes.")
    sys.exit(1)

normalized_amplitude = mean_trace / norm_factor

plt.figure(figsize=(10, 4))
plt.plot(time_axis_us, normalized_amplitude, color='#0077B6', linewidth=1.2)

# Professional formatting
plt.title(f"Pulse‑Echo A‑Scan (avg of {n_traces} receivers, {f0_MHz:.2f} MHz in Steel)",
          fontsize=14, fontweight='bold')
plt.xlabel("Time of Flight (µs)", fontsize=12)
plt.ylabel("Amplitude (% FSH)", fontsize=12)

plt.grid(True, linestyle='--', alpha=0.7)
plt.axhline(0, color='black', linewidth=0.8)
plt.xlim(0, max(time_axis_us))
plt.ylim(-1.1, 1.1)

plt.tight_layout()

# Save and show
save_path = EXAMPLE_DIR / "A_Scan_Result.png"
plt.savefig(save_path, dpi=300)
print(f"✅ A‑Scan successfully plotted and saved to {save_path}")
plt.show()