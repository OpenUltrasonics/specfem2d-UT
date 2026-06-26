# Citation

If you use this repository in your research or engineering work, please cite the references below.

---

## 1. This Repository

When citing the NDT examples, utilities, or solver modifications in this repository:

**APA**
> OpenUltrasonics (2025). *SPECFEM2D for Ultrasonic NDT and Phased Array Simulation* [Software]. GitHub. https://github.com/OpenUltrasonics/specfem2d

**BibTeX**
```bibtex
@software{OpenUltrasonics2025,
  author       = {OpenUltrasonics},
  title        = {{SPECFEM2D} for Ultrasonic {NDT} and Phased Array Simulation},
  year         = {2025},
  publisher    = {GitHub},
  url          = {https://github.com/OpenUltrasonics/specfem2d},
  note         = {Fork of SPECFEM/specfem2d adapted for ultrasonic testing and
                  non-destructive evaluation}
}
```

---

## 2. Upstream SPECFEM2D Solver

This repository builds on the SPECFEM2D solver. Please also cite the two foundational papers for the spectral-element method as implemented in SPECFEM2D:

### Komatitsch & Tromp (1999) — 3D spectral-element method

**APA**
> Komatitsch, D., & Tromp, J. (1999). Introduction to the spectral element method for three-dimensional seismic wave propagation. *Geophysical Journal International*, 139(3), 806–822. https://doi.org/10.1046/j.1365-246X.1999.00967.x

**BibTeX**
```bibtex
@article{Komatitsch1999,
  author    = {Komatitsch, Dimitri and Tromp, Jeroen},
  title     = {Introduction to the spectral element method for
               three-dimensional seismic wave propagation},
  journal   = {Geophysical Journal International},
  year      = {1999},
  volume    = {139},
  number    = {3},
  pages     = {806--822},
  doi       = {10.1046/j.1365-246X.1999.00967.x}
}
```

### Komatitsch & Vilotte (1998) — 2D spectral-element method

**APA**
> Komatitsch, D., & Vilotte, J.-P. (1998). The spectral element method: an efficient tool to simulate the seismic response of 2D and 3D geological structures. *Bulletin of the Seismological Society of America*, 88(2), 368–392. https://doi.org/10.1785/BSSA0880020368

**BibTeX**
```bibtex
@article{Komatitsch1998,
  author    = {Komatitsch, Dimitri and Vilotte, Jean-Pierre},
  title     = {The spectral element method: an efficient tool to simulate
               the seismic response of {2D} and {3D} geological structures},
  journal   = {Bulletin of the Seismological Society of America},
  year      = {1998},
  volume    = {88},
  number    = {2},
  pages     = {368--392},
  doi       = {10.1785/BSSA0880020368}
}
```

---

## 3. Minimum Citation Recommendation

If journal word limits restrict the number of references, the minimum recommended set is:

1. This repository (software citation)
2. Komatitsch & Tromp (1999) — the primary SPECFEM2D reference
3. Komatitsch & Vilotte (1998) — the 2D formulation reference

---

## Notes

- The two Komatitsch papers are the citations requested in the official [SPECFEM2D documentation](https://specfem2d.readthedocs.io). Citing them credits the original authors of the solver this work depends on.
- If you use the **anisotropic external model** feature (per-GLL anisotropic constants), please mention in your methods section that this is an OpenUltrasonics extension to the standard SPECFEM2D external model interface.
- If your work uses a specific example from the `EXAMPLES/` folder (e.g. FMC, plane wave imaging), consider noting the example name in your methods section so readers can reproduce your simulation setup directly from this repository.