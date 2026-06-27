import yaml
import os
import sys
import re
import subprocess
from pathlib import Path
from physics_utils import calculate_physics_parameters

# =====================================================================
# 1. ROBUST PATH RESOLUTION
# =====================================================================
DATA_DIR = Path(__file__).resolve().parent
SPECFEM2D_DIR = Path(os.environ.get("SPECFEM2D_DIR", DATA_DIR.parents[2])).resolve()

# =====================================================================
# 2. PARAMETERS & GEOMETRY SETUP
# =====================================================================
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")
mesh_size = physics['mesh_size']

# 2. Setup Files
with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

mesh_dir = DATA_DIR / "MESH"
mesh_dir.mkdir(exist_ok=True)

mesh_name = params['simulation']['mesh_name']
geo_source = DATA_DIR / f"{mesh_name}.geo"
geo_dest = mesh_dir / f"{mesh_name}.geo"
msh_filename = mesh_dir / f"{mesh_name}.msh"

if not geo_source.exists():
    print(f"❌ Error: Could not find geometry file {geo_source}")
    sys.exit(1)

print(f"--> Calculated required Base Mesh Size: {mesh_size*1000:.3f} mm")

# =====================================================================
# 3. DYNAMIC REGEX UPDATE OF THE .GEO FILE
# =====================================================================
with geo_source.open('r') as file:
    geo_data = file.read()

geom = params['geometry']
spec = geom['specimen_dimensions']
wedge = geom['wedge_dimensions']
notch = geom['notch_dimensions']

# Dictionary mapping the .geo variable names to the YAML values
# Added '^\s*' to safely ignore any tabs or spaces at the start of the line!
replacements = {
    r'^\s*lc\s*=.*': f'lc = {mesh_size:.6f};',
    r'^\s*width\s*=.*': f'width = {spec["specimen_width"]};',
    r'^\s*depth\s*=.*': f'depth = {spec["specimen_depth"]};',
    r'^\s*notch_x\s*=.*': f'notch_x = {notch["notch_x_cord"]};',
    r'^\s*notch_w\s*=.*': f'notch_w = {notch["notch_width"]};',
    r'^\s*notch_h\s*=.*': f'notch_h = {notch["notch_height"]};',
    r'^\s*wedge_x\s*=.*': f'wedge_x = {wedge["wedge_x"]};',
    r'^\s*wedge_y\s*=.*': f'wedge_y = {wedge["wedge_y"]};',
    r'^\s*wedge_l\s*=.*': f'wedge_l = {wedge["wedge_l"]};',
    r'^\s*wedge_h_toe\s*=.*': f'wedge_h_toe = {wedge["wedge_h_toe"]};',
    r'^\s*wedge_l_flat\s*=.*': f'wedge_l_flat = {wedge["wedge_l_flat"]};',
    r'^\s*wedge_angle\s*=.*': f'wedge_angle = {wedge["wedge_angle"]} * Pi / 180.0;'
}

# Replace all geometry variables dynamically
for pattern, replacement in replacements.items():
    geo_data = re.sub(pattern, replacement, geo_data, flags=re.MULTILINE)

# Write the uniquely updated text to the MESH folder
with geo_dest.open('w') as file:
    file.write(geo_data)

# =====================================================================
# 4. GMSH MESHING
# =====================================================================
print(f"--> Generating mesh in: {mesh_dir}")

try:
    subprocess.run(
        [
            "gmsh", geo_dest.name, 
            "-2", "-order", "1", "-format", "msh22", 
            "-o", msh_filename.name
        ],
        check=True,
        cwd=mesh_dir,
        capture_output=True,
        text=True
    )
except subprocess.CalledProcessError as e:
    print("\n❌ GMSH FAILED WITH THE FOLLOWING ERROR:")
    print("--------------------------------------------------")
    print(e.stderr if e.stderr else e.stdout)
    print("--------------------------------------------------")
    sys.exit(1)

# =====================================================================
# 5. SPECFEM2D FORMAT CONVERSION (DYNAMIC BOUNDARIES)
# =====================================================================
convert_script = SPECFEM2D_DIR / "utils" / "Gmsh" / "LibGmsh2Specfem_convert_Gmsh_to_Specfem2D_official.py"

if not convert_script.exists():
    raise FileNotFoundError(
        f"Could not find the Gmsh-to-SPECFEM2D converter at {convert_script}."
    )

print("--> Converting mesh to SPECFEM2D format...")

# Parse boundary conditions from YAML ('free' -> 'F', 'absorbing' -> 'A')
bc_map = {'free': 'F', 'absorbing': 'A'}
try:
    bc_top = bc_map[params['boundaries']['top'].lower()]
    bc_bottom = bc_map[params['boundaries']['bottom'].lower()]
    bc_left = bc_map[params['boundaries']['left'].lower()]
    bc_right = bc_map[params['boundaries']['right'].lower()]
except KeyError as e:
    print(f"❌ Error: Invalid boundary condition found in YAML. Use 'free' or 'absorbing'.")
    sys.exit(1)
    
print(f"--> Boundary conditions set as: Top={bc_top}, Bottom={bc_bottom}, Left={bc_left}, Right={bc_right}")

try:
    subprocess.run(
        [
            sys.executable, str(convert_script), msh_filename.name, 
            "-t", bc_top, "-b", bc_bottom, "-l", bc_left, "-r", bc_right
        ],
        check=True,
        cwd=mesh_dir,
        capture_output=True,
        text=True
    )
except subprocess.CalledProcessError as e:
    print("\n❌ CONVERSION SCRIPT FAILED WITH THE FOLLOWING ERROR:")
    print("--------------------------------------------------")
    print(e.stderr if e.stderr else e.stdout)
    print("--------------------------------------------------")
    sys.exit(1)

print("✅ Mesh generation complete!")