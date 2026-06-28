
# Angle Beam Wedge Example (Pulse‑Echo on Notch)

This example simulates an ultrasonic angle‑beam inspection using a Rexolite wedge
mounted on a steel specimen containing a small EDM notch.
The wedge generates a shear wave that propagates into the steel, reflects off the
defect, and is recorded by an array of virtual receivers on the wedge face.

The example is self‑contained under `EXAMPLES/02_Angle_Beam_Wedge`.
Paths are resolved relative to the example directory and the SPECFEM2D checkout,
so it should work from any clone location.

## Python Environment

Using conda or mamba:

```bash
cd EXAMPLES/02_Angle_Beam_Wedge
conda env create -f environment.yml
conda activate specfem2d-ut
```

Using venv and pip:

```bash
cd EXAMPLES/02_Angle_Beam_Wedge
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

### Option 1: Google Colab (Recommended)

Open this example directly in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OpenUltrasonics/specfem2d-UT/blob/master/EXAMPLES/02_Angle_Beam_Wedge/02_Angle_Beam_Wedge_colab.ipynb)

The notebook automatically installs dependencies, compiles SPECFEM2D, and runs the simulation.

### Option 2: Local Execution

For local installation and compilation instructions, please follow the **Getting Started** section in the repository's main README.

Once SPECFEM2D has been successfully compiled, run this example from the example directory:

```bash
bash run_this_example.sh
```

---

## Modifying the Simulation Setup

All simulation parameters are defined in `DATA/00_parameters.yaml`.

### Material Properties

Two materials are defined – **steel** (specimen) and **Rexolite** (wedge).

```yaml
material_specimen:
  vp: 5950.0               # P-wave velocity (m/s)
  vs: 3200.0               # S-wave velocity (m/s)
  rho: 7850.0              # Density (kg/m³)

material_wedge:
  vp: 2330.0               # Rexolite P-wave
  vs: 1160.0               # Rexolite S-wave
  rho: 1180.0              # Rexolite Density
```

| Parameter | Description     | Units  |
| --------- | --------------- | ------ |
| `vp`    | P-wave velocity | m/s    |
| `vs`    | S-wave velocity | m/s    |
| `rho`   | Density         | kg/m³ |

### Geometry

```yaml
geometry:
  specimen_dimensions:
    specimen_width: 0.060  # m
    specimen_depth: 0.015  # m

  wedge_dimensions:
    wedge_x: 0.010         # Start position of wedge (m)
    wedge_y: 0.015         # Base of wedge – must equal specimen_depth
    wedge_l: 0.030         # Total length of wedge base (m)
    wedge_angle: 30.6      # Wedge angle in degrees
    wedge_h_toe: 0.005     # Height of the front vertical toe (m)
    wedge_l_flat: 0.005    # Length of the top flat section (m)

  notch_dimensions:
    notch_x_cord: 0.045    # Notch position from left edge (m)
    notch_width: 0.0005    # Notch width (m)
    notch_height: 0.005    # Notch height (m)
```

| Parameter          | Description                                             | Units |
| ------------------ | ------------------------------------------------------- | ----- |
| `specimen_width` | Width of the steel block                                | m     |
| `specimen_depth` | Height (thickness) of the steel block                   | m     |
| `wedge_x`        | Horizontal offset of the wedge toe                      | m     |
| `wedge_y`        | Vertical position of the wedge base (same as depth)     | m     |
| `wedge_l`        | Base length of the wedge                                | m     |
| `wedge_angle`    | Wedge angle (inclination of the slanted transducer face)| deg   |
| `wedge_h_toe`    | Vertical height of the left toe                         | m     |
| `wedge_l_flat`   | Length of the horizontal top section                    | m     |
| `notch_x_cord`   | Horizontal position of the notch                        | m     |
| `notch_width`    | Width of the notch                                      | m     |
| `notch_height`   | Height (depth) of the notch                             | m     |

### Boundary Conditions

```yaml
boundaries:
  top: absorbing
  bottom: free
  left: absorbing
  right: absorbing
```

Each boundary can be `free` or `absorbing`. In this angle‑beam setup the **top** (slanted wedge and the outer face) is **absorbing** to eliminate internal wedge reverberations, while the **bottom** of the steel block is **free**.

### Transducer Parameters

```yaml
transducer:
  f0: 2250000.0            # Frequency (2.25 MHz)
  aperture: 0.015          # Transducer element width (m)
  total_factor: 1.0e9      # Source amplitude scaling factor
  apodization: "uniform"   # Element weighting: "uniform" or "gaussian"
  use_custom_source: True  # Use a custom tone‑burst wavelet
  window_type: "hanning"   # Envelope: "hanning", "gaussian", "rectangular"
  num_cycles: 3            # Number of cycles in the tone burst
```

| Parameter             | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| `f0`                | Centre frequency (Hz)                                              |
| `aperture`          | Physical width of the transducer on the slanted face (m)          |
| `total_factor`      | Scaling factor applied to the source amplitude                     |
| `apodization`       | Weighting across the multi‑source array (`uniform` or `gaussian`)|
| `use_custom_source` | `True` → tone burst; `False` → default Ricker wavelet             |
| `window_type`       | Envelope applied to the tone burst                                 |
| `num_cycles`        | Number of cycles in the burst (typically 2–5)                      |

### Receiver Settings

```yaml
receiver:
  seismotype: 4                      # 1=displ, 2=veloc, 3=accel, 4=pressure, …
  sampling_frequency: 100.0e6        # Desired output sampling rate (Hz)
```

| Parameter              | Description                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `seismotype`         | Quantity recorded: 1=displ, 2=veloc, 3=accel, 4=pressure, 5=curl of displ, 6=fluid potential                                     |
| `sampling_frequency` | Target output sample rate (Hz). The script automatically computes the down‑sampling factor `NTSTEP_BETWEEN_OUTPUT_SAMPLE`.     |

Multiple receivers are automatically placed on the transducer face and averaged in the A‑scan plot. The number of receivers is derived from the source array to capture a representative response.

### Simulation Controls

```yaml
simulation:
  total_time: 0.000027     # 27 µs – long enough to capture the notch echo
  mesh_name: "angle_beam_wedge"

  mpi:
    nproc: 8               # Number of MPI processes

  gpu:
    use_gpu: False         # Set to True to enable GPU acceleration
```

| Parameter      | Description                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `total_time` | Total simulation time (seconds). Must cover the flight time to the defect and back.                |
| `mesh_name`  | Name of the mesh file (without extension). Must match the `.msh` file created by Gmsh.            |
| `mpi.nproc`  | Number of MPI ranks. If GPU is used, this is forced to 1 (serial).                                 |
| `gpu.use_gpu`| Set to `True` only if you compiled the GPU‑enabled version of SPECFEM2D.                           |

After modifying `DATA/00_parameters.yaml`, rerun the example:

```bash
bash run_this_example.sh
```

---

## Modifying the Geometry

The specimen and wedge geometry are defined in the Gmsh `.geo` file located in this example directory.
To change the specimen size, wedge shape, or notch dimensions,
edit the `.geo` file directly and regenerate the mesh before rerunning.

Geometry files can be created or edited using:

- **[Gmsh](https://gmsh.info/)** (recommended) — free and open‑source mesh generator with GUI and scripting.
- **Any text editor** — `.geo` files are plain text with a well‑documented scripting language.
- **AI coding assistants or LLMs** — tools like ChatGPT or GitHub Copilot can generate `.geo` files from plain‑English descriptions, which can then be refined manually.

After updating the geometry, run the example again; the pipeline will automatically remesh.

---

## Output

After a successful run the script produces:
- `A_Scan_Result.png` – averaged pulse‑echo A‑scan (pressure vs. time of flight).
- Seismogram files in `OUTPUT_FILES/` (SU format).

The A‑scan uses percentile‑based normalisation to make the defect echo visible even when the direct arrival (main bang) is much larger.
