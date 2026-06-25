#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
ENVIRONMENT_FILE="$SCRIPT_DIR/environment.yml"

find_specfem2d_dir() {
    local candidate xmesh_target

    if [ -n "${SPECFEM2D_DIR:-}" ]; then
        candidate="$SPECFEM2D_DIR"
        if [ -x "$candidate/bin/xmeshfem2D" ] && [ -f "$candidate/utils/Gmsh/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py" ]; then
            cd "$candidate" && pwd
            return 0
        fi
    fi

    candidate="$SCRIPT_DIR/../.."
    if [ -x "$candidate/bin/xmeshfem2D" ] && [ -f "$candidate/utils/Gmsh/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py" ]; then
        cd "$candidate" && pwd
        return 0
    fi

    if [ -x "$SCRIPT_DIR/bin/xmeshfem2D" ] && command -v readlink >/dev/null 2>&1; then
        xmesh_target="$(readlink -f "$SCRIPT_DIR/bin/xmeshfem2D")"
        candidate="$(dirname "$(dirname "$xmesh_target")")"
        if [ -x "$candidate/bin/xmeshfem2D" ] && [ -f "$candidate/utils/Gmsh/LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py" ]; then
            cd "$candidate" && pwd
            return 0
        fi
    fi

    return 1
}

find_working_python() {
    local candidate
    for candidate in "$PYTHON_BIN" \
                     "$SCRIPT_DIR/.venv/bin/python" \
                     "$SCRIPT_DIR/../../.venv/bin/python" \
                     "${CONDA_PREFIX:+$CONDA_PREFIX/bin/python}" \
                     python3 python; do
        [ -n "$candidate" ] || continue
        command -v "$candidate" >/dev/null 2>&1 || [ -x "$candidate" ] || continue
        if "$candidate" -c "import yaml, gmsh, numpy, matplotlib" >/dev/null 2>&1; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

print_python_setup_help() {
    echo "Create a Python environment first, for example:"
    echo "  python3 -m venv .venv"
    echo "  . .venv/bin/activate"
    echo "  python -m pip install --upgrade pip"
    echo "  python -m pip install -r \"$REQUIREMENTS_FILE\""
    echo
    echo "Or with conda/mamba:"
    echo "  conda env create -f \"$ENVIRONMENT_FILE\""
    echo "  conda activate specfem2d-ut"
    echo
    echo "Then rerun:"
    echo "  bash \"$SCRIPT_DIR/run_this_example.sh\""
}

echo "=========================================================="
echo "    OPENULTRASONICS: CONVENTIONAL PULSE-ECHO PIPELINE     "
echo "=========================================================="

echo "Checking dependencies..."

if ! SPECFEM2D_DIR="$(find_specfem2d_dir)"; then
    echo "CRITICAL ERROR: Could not find the SPECFEM2D root directory."
    echo "Run this example from inside a SPECFEM2D checkout, or set:"
    echo "  SPECFEM2D_DIR=/path/to/specfem2d bash run_this_example.sh"
    exit 1
fi
export SPECFEM2D_DIR

if ! PYTHON_BIN="$(find_working_python)"; then
    echo "CRITICAL ERROR: Could not find a Python environment with yaml, gmsh, numpy, and matplotlib."
    print_python_setup_help
    exit 1
fi

PYTHON_DIR="$(dirname "$PYTHON_BIN")"
export PATH="$PYTHON_DIR:$PATH"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib-$USER}"
mkdir -p "$MPLCONFIGDIR"

# 2. Ensure the actual Gmsh terminal application is installed and accessible
if ! command -v gmsh &> /dev/null; then
    echo "CRITICAL ERROR: 'gmsh' terminal command could not be found."
    echo "Install the packages in $REQUIREMENTS_FILE, activate the conda environment from $ENVIRONMENT_FILE, or set PYTHON_BIN to that environment's python."
    exit 1
fi

echo "Using Python: $PYTHON_BIN"
echo "Using Gmsh:   $(command -v gmsh)"
echo "Using SPECFEM2D root: $SPECFEM2D_DIR"
echo "Dependencies verified. Proceeding with simulation..."

echo "Preparing SPECFEM2D output directory..."
mkdir -p "$SCRIPT_DIR/OUTPUT_FILES"

echo "[1/5] Building Mesh via Gmsh..."
"$PYTHON_BIN" "$SCRIPT_DIR/DATA/01_create_mesh.py"

echo "[2/5] Updating Par_file physics and CFL limits..."
"$PYTHON_BIN" "$SCRIPT_DIR/DATA/03_update_par_file.py"

echo "[3/5] Creating Source, Station, and optional custom source arrays..."
"$PYTHON_BIN" "$SCRIPT_DIR/DATA/02_create_source_station.py"

echo "[4/5] Running mesher (xmeshfem2D)..."
"${SPECFEM2D_DIR}/bin/xmeshfem2D"

echo "[5/5] Running explicit wave solver (xspecfem2D)..."
"${SPECFEM2D_DIR}/bin/xspecfem2D"

echo "=========================================================="
echo " ✅ SIMULATION COMPLETE."
echo "=========================================================="

"$PYTHON_BIN" "$SCRIPT_DIR/plot_A_scan.py"

"$PYTHON_BIN" "$SCRIPT_DIR/create_gif.py"