// ------------------------------------------------------------
// TEMPLATE – Axisymmetric immersion testing mesh
// Placeholders will be replaced by the Python pipeline.
// ------------------------------------------------------------
SetFactory("OpenCASCADE");

lc = @MESH_SIZE@;
Mesh.MeshSizeMin = lc;
Mesh.MeshSizeMax = lc;

pml = @PML_THICKNESS@;
tol = 1e-4;

// --- Geometry parameters (all radii, because AXISYM = true) ---
tank_r = @TANK_RADIUS@;
tank_z = @TANK_DEPTH@;
spec_r = @SPECIMEN_RADIUS@;
spec_z = @SPECIMEN_DEPTH@;
spec_z_start = @SPECIMEN_Z_START@;
trans_r = @TRANSDUCER_RADIUS@;

// ---- 1. Domains ----
Rectangle(1) = {0, spec_z_start, 0, spec_r, spec_z};      // Steel
Rectangle(2) = {0, 0, 0, tank_r, tank_z};                  // Main fluid

// ---- 2. PMLs ----
Rectangle(3) = {0, -pml, 0, tank_r, pml};                  // Bottom PML
Rectangle(4) = {tank_r, 0, 0, pml, tank_z};                // Right PML
Rectangle(5) = {trans_r, tank_z, 0, tank_r - trans_r, pml}; // Top PML (excludes transducer)
Rectangle(6) = {tank_r, -pml, 0, pml, pml};                // Bottom‑right corner
Rectangle(7) = {tank_r, tank_z, 0, pml, pml};              // Top‑right corner

// ---- 3. Merge ----
BooleanFragments{ Surface{:}; Delete; }{}
Coherence;

// ---- 4. Quad mesh ----
Mesh.RecombineAll = 1;
Mesh.Algorithm = 8;
Mesh.RecombinationAlgorithm = 2;
Mesh.SubdivisionAlgorithm = 1;

// ---- 5. Materials ----
steel[] = Surface In BoundingBox{-tol, spec_z_start-tol, -tol, spec_r+tol, spec_z_start+spec_z+tol, tol};
Physical Surface("M2") = steel[];

all_surfs[] = Surface{:};
fluid[] = all_surfs[];
fluid[] -= steel[];
Physical Surface("M1") = fluid[];

// ---- 6. PML surfaces (short names for the converter) ----
bottom_pml[] = Surface In BoundingBox{-tol, -pml-tol, -tol, tank_r+tol, tol, tol};
Physical Surface("B") = bottom_pml[];

right_pml[] = Surface In BoundingBox{tank_r-tol, -tol, -tol, tank_r+pml+tol, tank_z+tol, tol};
Physical Surface("R") = right_pml[];

top_pml[] = Surface In BoundingBox{trans_r-tol, tank_z-tol, -tol, tank_r+tol, tank_z+pml+tol, tol};
Physical Surface("T") = top_pml[];

br_corner[] = Surface In BoundingBox{tank_r-tol, -pml-tol, -tol, tank_r+pml+tol, tol, tol};
Physical Surface("RB") = br_corner[];

tr_corner[] = Surface In BoundingBox{tank_r-tol, tank_z-tol, -tol, tank_r+pml+tol, tank_z+pml+tol, tol};
Physical Surface("RT") = tr_corner[];

// ---- 7. Trigger curves for PML detection ----
outer_bottom[] = Curve In BoundingBox{-tol, -pml-tol, -tol, tank_r+pml+tol, -pml+tol, tol};
Physical Curve("Bottom_PML") = outer_bottom[];

outer_right[] = Curve In BoundingBox{tank_r+pml-tol, -pml-tol, -tol, tank_r+pml+tol, tank_z+pml+tol, tol};
Physical Curve("Right_PML") = outer_right[];

outer_top[] = Curve In BoundingBox{trans_r-tol, tank_z+pml-tol, -tol, tank_r+pml+tol, tank_z+pml+tol, tol};
Physical Curve("Top_PML") = outer_top[];

// ---- 8. Symmetry axis ----
axis_lines[] = Curve In BoundingBox{-tol, -pml-tol, -tol, tol, tank_z+pml+tol, tol};
Physical Curve("Axis") = axis_lines[];