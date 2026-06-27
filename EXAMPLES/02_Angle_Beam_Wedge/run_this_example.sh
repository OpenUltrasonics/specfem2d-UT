#!/bin/bash
# =============================================================================
# OPENULTRASONICS: ANGLE BEAM PIPELINE
# =============================================================================
# MPI is controlled entirely from DATA/00_parameters.yaml:
#
#   simulation:
#     mpi:
#       nproc: 4    # >1 → mpirun -np N
#                   #  1 → serial
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
PARAMS_FILE="$SCRIPT_DIR/DATA/00_parameters.yaml"

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

find_specfem2d_dir() {
    local candidate converter
    converter="utils/Gmsh/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py"
    for candidate in "${SPECFEM2D_DIR:-}" "$SCRIPT_DIR/../.." "$SCRIPT_DIR"; do
        [ -n "$candidate" ] || continue
        if [ -x "$candidate/bin/xmeshfem2D" ] && [ -f "$candidate/$converter" ]; then
            cd "$candidate" && pwd; return 0
        fi
    done
    return 1
}

find_working_python() {
    local candidate
    for candidate in \
        "$PYTHON_BIN" \
        "$SCRIPT_DIR/.venv/bin/python" \
        "$SCRIPT_DIR/../../.venv/bin/python" \
        "${CONDA_PREFIX:+$CONDA_PREFIX/bin/python}" \
        python3 python; do
        [ -n "$candidate" ] || continue
        command -v "$candidate" >/dev/null 2>&1 || [ -x "$candidate" ] || continue
        if "$candidate" -c "import yaml, gmsh, numpy, matplotlib" >/dev/null 2>&1; then
            printf '%s\n' "$candidate"; return 0
        fi
    done
    return 1
}

section() { echo; echo "──────────────────────────────────────────"; echo "  $*"; echo "──────────────────────────────────────────"; }

# ─────────────────────────────────────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────────────────────────────────────
echo "=========================================================="
echo "    OPENULTRASONICS: Angle_Beam_Wedge PIPELINE     "
echo "=========================================================="

# ─────────────────────────────────────────────────────────────────────────────
# DEPENDENCY CHECKS
# ─────────────────────────────────────────────────────────────────────────────
section "Checking dependencies"

if ! SPECFEM2D_DIR="$(find_specfem2d_dir)"; then
    echo "ERROR: Cannot find SPECFEM2D root (needs bin/xmeshfem2D)."
    echo "  Set:  SPECFEM2D_DIR=/path/to/specfem2d bash run_this_example.sh"
    exit 1
fi
export SPECFEM2D_DIR

if ! PYTHON_BIN="$(find_working_python)"; then
    echo "ERROR: No Python with yaml/gmsh/numpy/matplotlib found."
    echo "  python3 -m venv .venv && . .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

export PATH="$(dirname "$PYTHON_BIN"):$PATH"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-$USER}"
mkdir -p "$MPLCONFIGDIR"

if ! command -v gmsh &>/dev/null; then
    echo "ERROR: 'gmsh' CLI not found. Install it or activate your conda env."
    exit 1
fi

echo "  Python    : $PYTHON_BIN"
echo "  Gmsh      : $(command -v gmsh)"
echo "  SPECFEM2D : $SPECFEM2D_DIR"

# ─────────────────────────────────────────────────────────────────────────────
# READ NPROC AND GPU FLAG FROM YAML — only used here to decide serial vs MPI
# 03_update_par_file.py reads the YAML itself and update the par_file nothing is passed from here
# ─────────────────────────────────────────────────────────────────────────────
section "MPI / GPU configuration"

# The following Python snippet reads both simulation.mpi.nproc and
# simulation.gpu.use_gpu. It outputs two shell variable assignments
# that we evaluate directly.
eval "$("$PYTHON_BIN" - <<'EOF'
import yaml, sys

with open("DATA/00_parameters.yaml") as f:
    data = yaml.safe_load(f)

# --- GPU flag ---
gpu = False
try:
    gpu = data["simulation"]["gpu"]["use_gpu"]
except (KeyError, TypeError):
    pass

# --- MPI nproc ---
nproc = 1
try:
    nproc = int(data["simulation"]["mpi"]["nproc"])
except (KeyError, TypeError):
    pass

# --- Decide final NPROC ---
if gpu:
    print("NPROC=1; GPU_ACTIVE=true")
else:
    print(f"NPROC={nproc}; GPU_ACTIVE=false")
EOF
)"

# --- User feedback ---
if [ "$GPU_ACTIVE" = "true" ]; then
    echo "  GPU acceleration requested (gpu.use_gpu = True)."
    echo "  Overriding user NPROC value → forcing serial run (NPROC=1)."
else
    if [ "$NPROC" -gt 1 ]; then
        MPIRUN="${MPIRUN:-mpirun}"
        if ! command -v "$MPIRUN" &>/dev/null; then
            echo "ERROR: '$MPIRUN' not found. Install OpenMPI/MPICH or set MPIRUN=srun"
            exit 1
        fi
        echo "  mode  : MPI  →  $MPIRUN -np $NPROC"
    else
        echo "  mode  : serial"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# run_solver <binary>
# ─────────────────────────────────────────────────────────────────────────────
run_solver() {
    if [ "$NPROC" -gt 1 ]; then
        "${MPIRUN}" -np "$NPROC" "$1"
    else
        "$1"
    fi
}
# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
section "[1/5] Building mesh via Gmsh"
"$PYTHON_BIN" "$SCRIPT_DIR/DATA/01_create_mesh.py"

section "[2/5] Creating source, station, and custom source arrays"
"$PYTHON_BIN" "$SCRIPT_DIR/DATA/02_create_source_station.py"

section "[3/5] Updating Par_file"
"$PYTHON_BIN" "$SCRIPT_DIR/DATA/03_update_par_file.py"

section "[4/5] Running mesher  (xmeshfem2D,  np=$NPROC)"
mkdir -p "$SCRIPT_DIR/OUTPUT_FILES"
run_solver "${SPECFEM2D_DIR}/bin/xmeshfem2D"

section "[5/5] Running wave solver  (xspecfem2D,  np=$NPROC)"
run_solver "${SPECFEM2D_DIR}/bin/xspecfem2D"

echo
echo "=========================================================="
echo " ✅ SIMULATION COMPLETE."
echo "=========================================================="

"$PYTHON_BIN" "$SCRIPT_DIR/plot_A_scan.py"
"$PYTHON_BIN" "$SCRIPT_DIR/create_gif.py"