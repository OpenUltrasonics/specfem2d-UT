# Ultrasonic Immersion Testing (Axisymmetric)

This example simulates a circular immersion transducer radiating into a water tank
that contains a steel specimen. The geometry is axisymmetric, and the absorbing
boundaries are implemented with Perfectly Matched Layers (PML).  
The wave field (pressure) is recorded by virtual receivers placed on the transducer
face, and an averaged A‑scan is produced.

The example is self‑contained under `EXAMPLES/03_Ultrasonic_Immersion_Testing`.
Paths are resolved relative to the example directory and the SPECFEM2D checkout,
so it should work from any clone location.

## Python Environment

Using conda or mamba:

```bash
cd EXAMPLES/03_Ultrasonic_Immersion_Testing
conda env create -f environment.yml
conda activate specfem2d-ut
```

Using venv and pip:

```bash
cd EXAMPLES/03_Ultrasonic_Immersion_Testing
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

### Option 1: Google Colab (Recommended)

Open this example directly in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OpenUltrasonics/specfem2d-UT/blob/master/EXAMPLES/03_Ultrasonic_Immersion_Testing/03_Ultrasonic_Immersion_Testing_colab.ipynb)

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

Two materials are defined – **water** (fluid) and **steel** (solid).

```yaml
material_water:
  vp: 1500.0               # P‑wave velocity (m/s)
  rho: 1000.0              # Density (kg/m³)

material_steel:
  vp: 5950.0               # P‑wave velocity (m/s)
  vs: 3200.0               # S‑wave velocity (m/s)
  rho: 7850.0              # Density (kg/m³)
```

| Parameter | Description     | Units  |
| --------- | --------------- | ------ |
| `vp`    | P‑wave velocity | m/s    |
| `vs`    | S‑wave velocity (ignored for fluids) | m/s |
| `rho`   | Density         | kg/m³ |

### Geometry

The tank and specimen are defined by their radii because the simulation is
axisymmetric – the left edge of the mesh (x = 0) is the axis of rotational
symmetry (the z‑axis in 3D). All horizontal dimensions are therefore radii,
and the entire 3D geometry is obtained by revolving the cross‑section around
that axis. The transducer is circular and centred on the symmetry axis.

```yaml
geometry:
  tank_dimensions:
    tank_width: 0.075       # Total width (diameter) of the tank (m)
    tank_depth: 0.050       # Depth of the tank (m)

  specimen_dimensions:
    specimen_width: 0.030   # Width (diameter) of the steel specimen (m)
    specimen_depth: 0.015   # Height of the specimen (m)
    z_offset: 0.01          # Vertical gap above tank bottom (m)

  pm_thickness: 0.002       # PML layer thickness (m)
```

| Parameter           | Description                                          | Units |
| ------------------- | ---------------------------------------------------- | ----- |
| `tank_width`      | Full tank diameter                                   | m     |
| `tank_depth`      | Tank height                                          | m     |
| `specimen_width`  | Specimen diameter                                    | m     |
| `specimen_depth`  | Specimen height                                      | m     |
| `z_offset`        | Distance from tank bottom to specimen bottom         | m     |
| `pm_thickness`    | Thickness of the PML absorbing layers                | m     |

### Boundary Conditions

```yaml
boundaries:
  top: absorbing
  bottom: absorbing
  left: free        # not used (symmetry axis)
  right: absorbing
```

Each boundary can be `free` or `absorbing`.  
In this axisymmetric setup, absorbing conditions are provided by **PML layers**
on the top, bottom, and right sides. The left boundary (x = 0) is the symmetry
axis and does **not** require a separate absorbing condition.

### Transducer Parameters

```yaml
transducer:
  f0: 2250000.0            # Frequency (2.25 MHz)
  aperture: 0.015          # Transducer diameter (m)
  total_factor: 1.0e9      # Source amplitude scaling factor
  apodization: "uniform"   # Element weighting: "uniform" or "gaussian"
  use_custom_source: False # Use a custom tone‑burst wavelet
  window_type: "hanning"   # Envelope: "hanning", "gaussian", "rectangular"
  num_cycles: 3            # Number of cycles in the tone burst
```

| Parameter             | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| `f0`                | Centre frequency (Hz)                                              |
| `aperture`          | Physical diameter of the circular transducer (m)                  |
| `total_factor`      | Scaling factor applied to the source amplitude                     |
| `apodization`       | Weighting across the multi‑source array (`uniform` or `gaussian`)|
| `use_custom_source` | `True` → tone burst; `False` → default Ricker wavelet             |
| `window_type`       | Envelope applied to the tone burst                                 |
| `num_cycles`        | Number of cycles in the burst (typically 2–5)                      |

### Receiver Settings

```yaml
receiver:
  seismotype: 4                      # 4 = pressure (suitable for fluid)
  sampling_frequency: 100.0e6        # Desired output sampling rate (Hz)
```

| Parameter              | Description                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `seismotype`         | Quantity recorded: 1=displ, 2=veloc, 3=accel, 4=pressure, 5=curl of displ, 6=fluid potential                                     |
| `sampling_frequency` | Target output sample rate (Hz). The script automatically computes the down‑sampling factor `NTSTEP_BETWEEN_OUTPUT_SAMPLE`.     |

Multiple receivers are automatically placed on the transducer face and averaged in the A‑scan plot.

### Simulation Controls

```yaml
simulation:
  total_time: 0.000030     # 30 µs – enough for the first interface echoes
  mesh_name: "ultrasonic_immersion_testing"

  mpi:
    nproc: 8               # Number of MPI processes

  gpu:
    use_gpu: False         # Set to True to enable GPU acceleration

```

| Parameter          | Description                                                                                         |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| `total_time`     | Total simulation time (seconds). Must cover the desired time of flight.                            |
| `mesh_name`      | Name of the mesh file (without extension). Must match the `.msh` file created by Gmsh.            |
| `mpi.nproc`      | Number of MPI ranks. If GPU is used, this is forced to 1 (serial).                                 |
| `gpu.use_gpu`    | Set to `True` only if you compiled the GPU‑enabled version of SPECFEM2D.                           |
| `axisymmetry`    | When `true` the solver runs in cylindrical (r,z) coordinates. Requires an axial‑elements file.     |

After modifying `DATA/00_parameters.yaml`, rerun the example:

```bash
bash run_this_example.sh
```

---

## Modifying the Geometry

The axisymmetric geometry is generated from a template `.geo` file located in `DATA/`.
The pipeline (`01_create_mesh.py`) reads this template and replaces placeholders
with the actual values from the YAML. You can edit the template directly to change
the tank shape, add internal structures, or modify the PML layout.

Geometry files can be created or edited using:

- **[Gmsh](https://gmsh.info/)** (recommended) — free and open‑source mesh generator with GUI and scripting.
- **Any text editor** — `.geo` files are plain text with a well‑documented scripting language.
- **AI coding assistants or LLMs** — tools like ChatGPT or GitHub Copilot can generate `.geo` files from plain‑English descriptions, which can then be refined manually.

After updating the template, run the example again; the pipeline will automatically remesh.

---

## Output

After a successful run the script produces:
- `A_Scan_Result.png` – averaged pulse‑echo A‑scan (pressure vs. time of flight).
- Seismogram files in `OUTPUT_FILES/` (SU format).

The A‑scan uses percentile‑based normalisation to make the defect echo visible even when the direct arrival (main bang) is much larger.

> **Note:** The wavefield resolution is intentionally kept low to speed up the
> simulation. For a high‑resolution wavefield, set `output_wavefield_dumps = .true.`
> in the `Par_file` — be aware this creates very large output files.
