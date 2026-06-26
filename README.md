# SPECFEM2D-UT: An Open Framework for Ultrasonic Simulation and NDT Imaging

> **An open framework built on [SPECFEM2D](https://github.com/SPECFEM/specfem2d) for ultrasonic testing simulation — from conventional pulse-echo and phased array acquisition through to advanced wavefield imaging, anisotropic material modelling, guided waves, and full waveform inversion.**
  
[![License: GPL-3.0+](https://img.shields.io/badge/License-GPL--3.0%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Upstream: SPECFEM/specfem2d](https://img.shields.io/badge/upstream-SPECFEM%2Fspecfem2d-green)](https://github.com/SPECFEM/specfem2d)
 
---

## Why This Repository Exists

SPECFEM2D is a powerful open-source spectral-element solver developed primarily for seismic wave propagation. However, the same physics — elastic and acoustic wave propagation in heterogeneous media — applies directly to **ultrasonic testing at MHz frequencies and mm-scale geometries**.

Despite this, **no publicly available, runnable example exists** showing how to configure SPECFEM2D for industrial NDT. Researchers and engineers who want to use it for UT simulation must start from scratch, translating seismic conventions (km, Hz) into UT conventions (mm, MHz) on their own. This repository exists to fill that gap.

The goals here are:

1. Provide **ready-to-run NDT examples** inside the `EXAMPLES/` directory — so an NDT engineer or researcher can clone, compile, and simulate without needing a seismology background.
2. Supply **helper utilities** (Python scripts) for generating delay laws, post-processing B-scans and S-scans, and setting up phased array geometries.
3. Document the **key translation rules** from seismic to UT: mesh sizing at MHz frequencies, absorbing boundary placement, source time functions for transducer elements, and units.
4. Grow into a **community resource** for open-source ultrasonic simulation.

---

## What Is SPECFEM2D?

SPECFEM2D solves the 2D elastic, acoustic, viscoelastic, and poroelastic wave equations using the **Spectral Element Method (SEM)** — a high-order finite element approach that is highly accurate and computationally efficient. It supports:

- P-SV and SH wave propagation
- Coupled acoustic-elastic problems (e.g., immersion testing)
- Absorbing boundary conditions (C-PML) to suppress reflections at model edges
- Parallel execution via MPI
- GPU acceleration (CUDA)

For NDT, this means you can simulate: wave propagation in steel, aluminium, composites, or water-coupled specimens; reflection and transmission at interfaces; diffraction from cracks and defects; and full phased array acquisition sequences — all with a physically accurate wave solver.

The original SPECFEM2D was founded by Dimitri Komatitsch and Jeroen Tromp and is maintained by the [SPECFEM community](https://github.com/SPECFEM/specfem2d). This fork does not modify the solver itself. All changes are in the `EXAMPLES/` directory and the `utils_NDT/` utilities folder.

---

## Repository Structure

```
specfem2d/
│
├── EXAMPLES/                        ← NDT examples only
├── utils_NDT/                       ← Helper scripts for UT workflows
├── src/                             ← SPECFEM2D solver source (UT specific modificaton)
├── doc/                             ← Original SPECFEM2D documentation
├── CITATION.md                      ← How to cite this work and upstream SPECFEM2D
└── README.md                        ← This file
```

---


## Key Differences from Seismic SPECFEM2D Usage

| Parameter | Seismic typical | UT typical |
|---|---|---|
| Frequency | 1–100 Hz | 1–10 MHz |
| Domain size | km scale | mm–cm scale |
| Element size | ~100 m | ~0.1 mm |
| Time step | ~0.01 s | ~1 ns |
| Material | Rock, soil | Steel, aluminium, water |
| Source | Moment tensor / explosion | Force source (single element) |
| Receivers | Seismometers | Transducer elements |

The `utils_NDT/mesh_size_calculator.py` script helps you verify that your chosen element size satisfies the spatial sampling criterion for your target frequency and material.

---

## Getting Started

### Option 1: Zero-Install Cloud Simulation
Don't want to install Fortran compilers? Run our complete automated pipeline directly in your browser using Google's free GPUs! 

**Every example in this repository includes its own standalone Google Colab Notebook located directly inside its folder.** You can click the badge below (or open the notebook in any example folder) to instantly compile SPECFEM2D in the cloud and run the simulation with zero local setup.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OpenUltrasonics/specfem2d-UT/blob/master/EXAMPLES/01_Conventional_Pulse_Echo/01_Conventional_Pulse_Echo_colab.ipynb)


### Option 2: Local Installation

**Clone and Compile**

```bash
git clone https://github.com/OpenUltrasonics/specfem2d.git
```

For serial runs:
```bash
cd specfem2d
./configure FC=gfortran
make all
```

For MPI parallel runs:
```bash
cd specfem2d
./configure FC=gfortran CC=gcc CXX=mpicxx MPIFC=mpif90 --with-mpi
make all
```


```bash
cd EXAMPLES/01_Conventional_Pulse_Echo
./run_this_example.sh
```


---

## Citing This Work

If you use this repository in your research, please cite both the original SPECFEM2D and this repository:

**Original SPECFEM2D:**
> Komatitsch, D. and Tromp, J. (1999). Introduction to the spectral element method for three-dimensional seismic wave propagation. *Geophysical Journal International*, 139(3), 806–822.

> Komatitsch, D. and Vilotte, J.P. (1998). The spectral element method: an efficient tool to simulate the seismic response of 2D and 3D geological structures. *Bulletin of the Seismological Society of America*, 88(2), 368–392.

**This repository:**
> OpenUltrasonics (2025). SPECFEM2D for Ultrasonic NDT and Phased Array Simulation. https://github.com/OpenUltrasonics/specfem2d

See `CITATION.md` for full details and BibTeX entries.

---

## License

This repository is distributed under the **GNU General Public License v3.0 or later (GPL-3.0+)**, the same license as the upstream SPECFEM2D source code. GPL-3.0+ grants the right to copy, modify, and redistribute — provided that all modifications are also distributed under GPL-3.0+ and that the original authors are credited.
 
See `LICENSE` for the full license text.

---


## Modifications to the Solver Source
 
This fork includes **targeted modifications to `src/`** where necessary to support NDT-specific physics not available in upstream SPECFEM2D.

---

## Contributing

Contributions are very welcome — and you do not need to be a SPECFEM2D expert to help. Useful contributions include new NDT examples (different geometries, defect types, or materials), new phased array methods (FMC, TFM, plane wave imaging, TOFD, SAFT), post-processing utilities, documentation improvements, and validation results comparing simulations against experimental data.

**To contribute:**
1. Open an [issue](https://github.com/OpenUltrasonics/specfem2d/issues) to describe what you would like to add — this way we can discuss structure before any code is written.
2. Fork the repository, create a branch, add your contribution, and open a pull request.

Full step-by-step instructions, an example folder template, and a quality checklist are in [CONTRIBUTING.md](./CONTRIBUTING.md).

This project is part of the [OpenUltrasonics](https://github.com/OpenUltrasonics) initiative, which aims to make open-source tools for ultrasonic and NDT simulation accessible to researchers and engineers who should not have to start from scratch.

---

## Acknowledgements

The SPECFEM2D solver is developed and maintained by the [SPECFEM community](https://github.com/SPECFEM/specfem2d) and hosted by the [Computational Infrastructure for Geodynamics (CIG)](https://geodynamics.org). This fork does not modify the solver; all credit for the core simulation engine belongs to the SPECFEM authors.