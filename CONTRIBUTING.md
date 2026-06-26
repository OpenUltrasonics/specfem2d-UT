# Contributing to OpenUltrasonics / SPECFEM2D-NDT

Thank you for your interest in contributing! This project exists because the NDT and ultrasonic simulation community needs open, accessible examples — and that only happens when people share their work. Every contribution, however small, helps the next researcher get started faster.

---

## What Can I Contribute?

You don't need to be a SPECFEM2D expert or a software developer to contribute. Useful contributions include:

- **New NDT examples** — a new inspection geometry, defect type, or material (composites, austenitic welds, layered media, etc.)
- **New phased array methods** — FMC, plane wave imaging, TFM, SAFT, PWI compounding, TOFD, etc.
- **Post-processing utilities** — Python or MATLAB scripts for B-scan extraction, TFM reconstruction, delay law generation, mesh sizing
- **Documentation improvements** — clearer explanations, better README files, diagrams, or worked results
- **Bug reports** — if something in an example doesn't run correctly, please tell us
- **Validation results** — if you have compared a SPECFEM2D simulation against experimental data or another solver, that is extremely valuable to share

---

## Types of Contribution

### Reporting a Bug or Problem

If an example fails to run, produces unexpected results, or the documentation is unclear:

1. Go to the [Issues page](https://github.com/OpenUltrasonics/specfem2d/issues)
2. Click **New issue**
3. Describe the problem: what you ran, what you expected, what happened instead
4. Include the error message or console output if relevant
5. Mention your OS, compiler, and Python version

This is genuinely helpful even if you cannot fix the problem yourself.

---

### Suggesting a New Example or Feature

Have an idea for a new UT/NDT example or utility that would be useful to others?

1. Open a [New issue](https://github.com/OpenUltrasonics/specfem2d/issues) and describe the idea
2. We can discuss the best way to implement and structure it before any code is written
3. If you want to build it yourself, we will help guide you through the process

---

### Submitting a New Example or Utility (Pull Request)

If you want to add something to the repository yourself, here is the full workflow:

#### Step 1 — Fork and clone

Click the **Fork** button at the top of this repository page to create your own copy. Then clone it locally:

```bash
git clone https://github.com/<your-github-username>/specfem2d.git
cd specfem2d
```

#### Step 2 — Create a branch for your work

Never work directly on `master`. Create a new branch with a descriptive name:

```bash
git checkout -b add-FMC-example
```

or for a utility script:

```bash
git checkout -b add-TFM-reconstruction-script
```

#### Step 3 — Add your contribution

**For a new NDT example**, create a self-contained folder under `EXAMPLES/`:

```
EXAMPLES/
└── UT_XX_your_example_name/
    ├── README.md                  ← describe the setup, geometry, expected results
    ├── parameter.yaml             ← all simulation parameters
    ├── your_geometry.geo          ← Gmsh geometry file
    ├── run_this_example.sh        ← one-command runner
    ├── environment.yml            ← conda environment (or requirements.txt)
    └── your_notebook.ipynb        ← optional Colab notebook
```

Please follow the structure of `EXAMPLES/01_Conventional_Pulse_Echo` as a reference.

**For a utility script**, add it under `utils_NDT/` with a clear filename and a short docstring at the top explaining what it does, its inputs, and its outputs.

#### Step 4 — Commit your changes

Check what has changed:

```bash
git status
git diff
```

Stage and commit:

```bash
git add EXAMPLES/UT_XX_your_example_name/
git commit -m "Add FMC phased array example for steel plate with SDH"
```

Keep commits focused — one logical change per commit. A clear commit message is a gift to anyone reading the history later.

#### Step 5 — Push to your fork

```bash
git push origin add-FMC-example
```

#### Step 6 — Open a Pull Request

Go to your fork on GitHub. You will see a prompt to **Compare & pull request**. Click it and:

- Write a short title describing what you are adding
- In the description, explain: what the example simulates, what material/geometry/frequency/method is used, and any known limitations
- If you have a figure showing the expected output (B-scan, wavefield snapshot, TFM image), attach it — this is very helpful for reviewers

We will review the PR, may suggest small changes, and merge it once everything looks good.

---

## Example Quality Checklist

Before submitting an example, please check:

- [ ] The example runs end-to-end with `bash run_this_example.sh` from a clean clone
- [ ] A `README.md` is included explaining the physical setup and expected results
- [ ] `parameter.yaml` contains all user-adjustable parameters (not hard-coded in scripts)
- [ ] Geometry is defined in a `.geo` file (not a hard-coded mesh)
- [ ] Output files are not committed to the repository (add them to `.gitignore` if needed)
- [ ] Frequencies, material properties, and geometry dimensions are in SI units (Hz, m/s, m, kg/m³)
- [ ] The `environment.yml` or `requirements.txt` is included and tested

---

## Keeping Your Fork Up to Date

If some time passes between when you forked and when you submit, the main repository may have new commits. To bring those in:

```bash
git remote add upstream https://github.com/OpenUltrasonics/specfem2d.git
git fetch upstream
git merge upstream/master
```

---

## Questions?

Open an issue and tag it with the `question` label. No question is too basic — if you are confused, others probably are too, and your question may lead to better documentation.

---

## Modifications to the Solver Source (`src/`)

Unlike a pure example repository, this fork **does include targeted modifications to the SPECFEM2D solver source code** where they are necessary to support UT/NDT capabilities that do not exist upstream. The current modifications are:

- **`src/specfem2D/define_external_model.f90`** — Extended to allow spatially varying anisotropic elastic constants (C11, C13, C33, C55, etc.) to be specified at every GLL point. This enables simulation of textured or grain-oriented materials such as austenitic stainless steel welds.

If you have a modification to `src/` that enables new NDT physics:
1. Open an issue first describing what you changed and why it is needed for UT/NDT.
2. Keep the change as small and targeted as possible — modify only what is needed.
3. Add a comment block at the top of any modified Fortran subroutine or module clearly marking it as an OpenUltrasonics modification, with your name and date:

```fortran
! -----------------------------------------------------------------------
! OpenUltrasonics modification — <your name>, <date>
! Purpose: <one sentence description>
! -----------------------------------------------------------------------
```

This makes it easy to diff our changes against upstream in the future.

If your change would also be useful for the seismic community, consider additionally submitting it as a pull request to the [upstream SPECFEM2D repository](https://github.com/SPECFEM/specfem2d).

---

## License

This repository is distributed under the **GNU General Public License v3.0 or later (GPL-3.0+)**, the same license as the upstream SPECFEM2D source code. All contributions — examples, utilities, documentation, and source code modifications — must be compatible with and distributed under GPL-3.0+.