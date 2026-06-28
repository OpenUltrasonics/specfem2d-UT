import yaml
import os
import sys
import subprocess
from pathlib import Path

# Import the centralized physics brain
from physics_utils import calculate_physics_parameters

# =====================================================================
# 1. ROBUST PATH RESOLUTION & PHYSICS
# =====================================================================
DATA_DIR = Path(__file__).resolve().parent
SPECFEM2D_DIR = Path(os.environ.get("SPECFEM2D_DIR", DATA_DIR.parents[2])).resolve()

# Calculate the precise mesh_size based on frequencies and velocities
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")
mesh_size = physics['mesh_size']

print(f"--> Calculated required Base Mesh Size (lc): {mesh_size*1000:.3f} mm")

# =====================================================================
# 2. EXTRACT GEOMETRY FROM YAML
# =====================================================================
with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

geom = params.get('geometry', {})
tank = geom.get('tank_dimensions', {'tank_width': 0.100, 'tank_depth': 0.050})
spec = geom.get('specimen_dimensions', {'specimen_width': 0.060, 'specimen_depth': 0.015})

# In Axisymmetry, the X-axis is the radius (half the total width)
tank_r = tank['tank_width'] / 2.0
tank_z = tank['tank_depth']

spec_r = spec['specimen_width'] / 2.0
spec_z = spec['specimen_depth']

# How high the steel specimen sits above the bottom of the water tank
# (Defaulting to 5mm if not explicitly set in YAML)
spec_z_start = spec.get('z_offset', 0.005) 

# Transducer radius (Starts at X=0, goes to aperture/2)
trans_r = params['transducer']['aperture'] / 2.0
pml = 0.002 # Standard 2mm PML layer

mesh_dir = DATA_DIR / "MESH"
mesh_dir.mkdir(exist_ok=True)
mesh_name = params['simulation']['mesh_name']
geo_dest = mesh_dir / f"{mesh_name}.geo"
msh_filename = mesh_dir / f"{mesh_name}.msh"

# =====================================================================
# 3. DYNAMICALLY WRITE THE .GEO FILE (No templates needed!)
# =====================================================================
# Note: Double brackets {{ }} are used to escape Gmsh syntax in Python f-strings
geo_content = f"""// ------------------------------------------------------------
// DYNAMIC AXISYMMETRIC MESH
// Generated automatically by Python from 00_parameters.yaml
// ------------------------------------------------------------
SetFactory("OpenCASCADE");

lc = {mesh_size:.6f};
Mesh.MeshSizeMin = lc;
Mesh.MeshSizeMax = lc;

pml = {pml:.6f};
tol = 1e-4;

// --- Geometric Variables ---
tank_r = {tank_r:.6f};
tank_z = {tank_z:.6f};
spec_r = {spec_r:.6f};
spec_z = {spec_z:.6f};
spec_z_start = {spec_z_start:.6f};
trans_r = {trans_r:.6f};

// ---- 1. Define Domains ----
// Steel Specimen
Rectangle(1) = {{0, spec_z_start, 0, spec_r, spec_z}};

// Fluid Main Tank
Rectangle(2) = {{0, 0, 0, tank_r, tank_z}};

// ---- 2. Define PMLs ----
Rectangle(3) = {{0, -pml, 0, tank_r, pml}};                          // Bottom PML
Rectangle(4) = {{tank_r, 0, 0, pml, tank_z}};                         // Right PML
Rectangle(5) = {{trans_r, tank_z, 0, tank_r - trans_r, pml}};         // Top PML (Excludes Transducer!)
Rectangle(6) = {{tank_r, -pml, 0, pml, pml}};                        // Bottom-Right Corner
Rectangle(7) = {{tank_r, tank_z, 0, pml, pml}};                       // Top-Right Corner

// ---- 3. Merge Everything Flawlessly ----
BooleanFragments{{ Surface{{:}}; Delete; }}{{}}
Coherence; 

// ---- 4. Force Quadrilaterals ----
Mesh.RecombineAll = 1;
Mesh.Algorithm = 8; 
Mesh.RecombinationAlgorithm = 2; 
Mesh.SubdivisionAlgorithm = 1; 

// ---- 5. Physical Materials ----
steel[] = Surface In BoundingBox{{-tol, spec_z_start-tol, -tol, spec_r+tol, spec_z_start+spec_z+tol, tol}};
Physical Surface("M2") = steel[];

all_surfs[] = Surface{{:}};
fluid[] = all_surfs[];
fluid[] -= steel[];
Physical Surface("M1") = fluid[];

// ---- 6. Define PML Regions ----
bottom_pml[] = Surface In BoundingBox{{-tol, -pml-tol, -tol, tank_r+tol, tol, tol}};
Physical Surface("B") = bottom_pml[];

right_pml[] = Surface In BoundingBox{{tank_r-tol, -tol, -tol, tank_r+pml+tol, tank_z+tol, tol}};
Physical Surface("R") = right_pml[];

top_pml[] = Surface In BoundingBox{{trans_r-tol, tank_z-tol, -tol, tank_r+tol, tank_z+pml+tol, tol}};
Physical Surface("T") = top_pml[];

br_corner[] = Surface In BoundingBox{{tank_r-tol, -pml-tol, -tol, tank_r+pml+tol, tol, tol}};
Physical Surface("RB") = br_corner[];

tr_corner[] = Surface In BoundingBox{{tank_r-tol, tank_z-tol, -tol, tank_r+pml+tol, tank_z+pml+tol, tol}};
Physical Surface("RT") = tr_corner[];

// ---- 7. Triggers for Python Converter ----
outer_bottom[] = Curve In BoundingBox{{-tol, -pml-tol, -tol, tank_r+pml+tol, -pml+tol, tol}};
Physical Curve("Bottom_PML") = outer_bottom[];

outer_right[] = Curve In BoundingBox{{tank_r+pml-tol, -pml-tol, -tol, tank_r+pml+tol, tank_z+pml+tol, tol}};
Physical Curve("Right_PML") = outer_right[];

outer_top[] = Curve In BoundingBox{{trans_r-tol, tank_z+pml-tol, -tol, tank_r+pml+tol, tank_z+pml+tol, tol}};
Physical Curve("Top_PML") = outer_top[];

// Symmetry Axis (X=0)
axis_lines[] = Curve In BoundingBox{{-tol, -pml-tol, -tol, tol, tank_z+pml+tol, tol}};
Physical Curve("Axis") = axis_lines[];
"""

with geo_dest.open('w') as file:
    file.write(geo_content)

print(f"--> Successfully generated dynamic .geo file at {geo_dest}")

# =====================================================================
# 4. GMSH MESHING
# =====================================================================
print(f"--> Meshing geometry via Gmsh...")
try:
    subprocess.run(
        ["gmsh", geo_dest.name, "-2", "-order", "1", "-format", "msh22", "-o", msh_filename.name],
        check=True, cwd=mesh_dir, capture_output=True, text=True
    )
except subprocess.CalledProcessError as e:
    print("\n❌ GMSH FAILED:")
    print(e.stderr if e.stderr else e.stdout)
    sys.exit(1)

# =====================================================================
# 5. SPECFEM2D FORMAT CONVERSION (DYNAMIC BOUNDARIES)
# =====================================================================
convert_script = DATA_DIR / "Gmsh2Specfem_convert.py"

print("--> Converting mesh to SPECFEM2D format...")

bc_map = {'free': 'F', 'absorbing': 'A', 'pml': 'A'}
bc_top = bc_map[params['boundaries'].get('top', 'absorbing').lower()]
bc_bottom = bc_map[params['boundaries'].get('bottom', 'absorbing').lower()]
bc_left = bc_map[params['boundaries'].get('left', 'absorbing').lower()]
bc_right = bc_map[params['boundaries'].get('right', 'absorbing').lower()]

try:
    subprocess.run(
        [sys.executable, str(convert_script), msh_filename.name, 
         "-t", bc_top, "-b", bc_bottom, "-l", bc_left, "-r", bc_right],
        check=True, cwd=mesh_dir, capture_output=True, text=True
    )
except subprocess.CalledProcessError as e:
    print("\n❌ CONVERSION SCRIPT FAILED:")
    print(e.stderr if e.stderr else e.stdout)
    sys.exit(1)

print("✅ Complete Pipeline Successful!")