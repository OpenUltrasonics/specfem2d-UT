#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_create_mesh.py – Axisymmetric immersion testing mesh generator.
Reads a Gmsh .geo template, substitutes parameters from YAML, meshes with Gmsh,
and converts to SPECFEM2D format.
"""

import yaml
import os
import sys
import subprocess
from pathlib import Path

# Import the centralized physics brain
from physics_utils import calculate_physics_parameters

# =====================================================================
# 1. PATH RESOLUTION & PHYSICS
# =====================================================================
DATA_DIR = Path(__file__).resolve().parent
SPECFEM2D_DIR = Path(os.environ.get("SPECFEM2D_DIR", DATA_DIR.parents[2])).resolve()

# Calculate mesh size from physics
physics = calculate_physics_parameters(DATA_DIR / "00_parameters.yaml")
mesh_size = physics['mesh_size']
print(f"--> Calculated required Base Mesh Size (lc): {mesh_size*1000:.3f} mm")

# =====================================================================
# 2. LOAD YAML & EXTRACT GEOMETRY PARAMETERS
# =====================================================================
with (DATA_DIR / "00_parameters.yaml").open("r") as f:
    params = yaml.safe_load(f)

geom = params.get('geometry', {})
tank = geom.get('tank_dimensions', {'tank_width': 0.100, 'tank_depth': 0.050})
spec = geom.get('specimen_dimensions', {'specimen_width': 0.060, 'specimen_depth': 0.015})

# In axisymmetry the X coordinate is the radius (half the total width)
tank_radius   = tank['tank_width'] / 2.0
tank_depth    = tank['tank_depth']
spec_radius   = spec['specimen_width'] / 2.0
spec_depth    = spec['specimen_depth']
spec_z_start  = spec.get('z_offset', 0.005)      # vertical offset of specimen above tank bottom

# Transducer radius (starts at X=0, goes to aperture/2)
trans_radius = params['transducer']['aperture'] / 2.0

# PML thickness – can be moved to YAML later if desired
pml_thickness = 0.002   # 2 mm

# =====================================================================
# 3. SETUP OUTPUT PATHS
# =====================================================================
mesh_dir = DATA_DIR / "MESH"
mesh_dir.mkdir(exist_ok=True)

mesh_name = params['simulation']['mesh_name']
geo_dest = mesh_dir / f"{mesh_name}.geo"
msh_filename = mesh_dir / f"{mesh_name}.msh"

# =====================================================================
# 4. READ TEMPLATE & SUBSTITUTE PLACEHOLDERS
# =====================================================================
template_path = DATA_DIR / "template_axisymmetric.geo"
if not template_path.exists():
    print(f"❌ Template file not found: {template_path}")
    sys.exit(1)

with open(template_path, 'r') as f:
    template = f.read()

# Dictionary of placeholder -> formatted numeric value
replacements = {
    '@MESH_SIZE@'          : f'{mesh_size:.6f}',
    '@PML_THICKNESS@'      : f'{pml_thickness:.6f}',
    '@TANK_RADIUS@'        : f'{tank_radius:.6f}',
    '@TANK_DEPTH@'         : f'{tank_depth:.6f}',
    '@SPECIMEN_RADIUS@'    : f'{spec_radius:.6f}',
    '@SPECIMEN_DEPTH@'     : f'{spec_depth:.6f}',
    '@SPECIMEN_Z_START@'   : f'{spec_z_start:.6f}',
    '@TRANSDUCER_RADIUS@'  : f'{trans_radius:.6f}',
}

for token, value in replacements.items():
    template = template.replace(token, value)

# Write the filled .geo file
with open(geo_dest, 'w') as f:
    f.write(template)
print(f"--> Generated .geo file from template: {geo_dest}")

# =====================================================================
# 5. MESH WITH GMSH
# =====================================================================
print(f"--> Meshing geometry via Gmsh...")
try:
    result = subprocess.run(
        ["gmsh", geo_dest.name, "-2", "-order", "1", "-format", "msh22",
         "-o", msh_filename.name],
        check=True,
        cwd=mesh_dir,
        capture_output=True,
        text=True
    )
except subprocess.CalledProcessError as e:
    print("\n❌ GMSH FAILED:")
    print(e.stderr if e.stderr else e.stdout)
    sys.exit(1)

# =====================================================================
# 6. CONVERT TO SPECFEM2D FORMAT
# =====================================================================
convert_script = DATA_DIR / "Gmsh2Specfem_convert.py"
if not convert_script.exists():
    print(f"❌ Converter script not found: {convert_script}")
    sys.exit(1)

print("--> Converting mesh to SPECFEM2D format...")

# Boundary conditions from YAML (only Top/Bottom/Right used, Left is symmetry)
bc_map = {'free': 'F', 'absorbing': 'A', 'pml': 'A'}
bc_top = bc_map[params['boundaries'].get('top', 'absorbing').lower()]
bc_bottom = bc_map[params['boundaries'].get('bottom', 'absorbing').lower()]
bc_left = bc_map[params['boundaries'].get('left', 'absorbing').lower()]   # not used but passed
bc_right = bc_map[params['boundaries'].get('right', 'absorbing').lower()]

try:
    result = subprocess.run(
        [sys.executable, str(convert_script), msh_filename.name,
         "-t", bc_top, "-b", bc_bottom, "-l", bc_left, "-r", bc_right],
        check=True,
        cwd=mesh_dir,
        capture_output=True,
        text=True
    )
except subprocess.CalledProcessError as e:
    print("\n❌ CONVERSION SCRIPT FAILED:")
    print(e.stderr if e.stderr else e.stdout)
    sys.exit(1)

# Print any conversion script output for logging
if result.stdout:
    print(result.stdout)
if result.stderr:
    print(result.stderr)

print("✅ Mesh generation and conversion complete!")