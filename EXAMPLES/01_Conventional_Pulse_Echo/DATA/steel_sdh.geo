SetFactory("OpenCASCADE");

// ----------------------------------------------------
// 1. Mesh Size Definition (Python will overwrite this!)
// ----------------------------------------------------
lc = 0.001;

// ----------------------------------------------------
// 2. Geometry
// ----------------------------------------------------
width = 0.050;
depth = 0.050;

// Base Block
Rectangle(1) = {0, 0, 0, width, depth};

// Side Drilled Hole
Disk(2) = {0.025, 0.025, 0, 0.002};

// Boolean Subtraction
BooleanDifference(3) = { Surface{1}; Delete; } { Surface{2}; Delete; };

// ----------------------------------------------------
// 3. Physical Groups for SPECFEM2D
// ----------------------------------------------------
eps = 1e-4; // Tolerance

Physical Surface("M1") = Surface In BoundingBox{-eps, -eps, -eps, width+eps, depth+eps, eps};

Physical Curve("Bottom") = Curve In BoundingBox{-eps, -eps, -eps, width+eps, eps, eps};
Physical Curve("Right")  = Curve In BoundingBox{width-eps, -eps, -eps, width+eps, depth+eps, eps};
Physical Curve("Top")    = Curve In BoundingBox{-eps, depth-eps, -eps, width+eps, depth+eps, eps};
Physical Curve("Left")   = Curve In BoundingBox{-eps, -eps, -eps, eps, depth+eps, eps};

// ----------------------------------------------------
// 4. Meshing Rules 
// ----------------------------------------------------
// Apply the base mesh size to ALL points in the geometry
MeshSize { PointsOf{Surface{:};} } = lc;

// Grab ONLY the points inside a 10x10mm box around the hole
hole_points() = Point In BoundingBox{0.02, 0.02, -eps, 0.03, 0.03, eps};

// Apply the refined (smaller) mesh size to just those hole points
MeshSize { hole_points() } = lc / 3.0;

// ----------------------------------------------------
// 5. Quadrilateral Generation
// ----------------------------------------------------
Mesh.RecombinationAlgorithm = 1;
Mesh.RecombineAll = 1;
Mesh.Algorithm = 8;
Mesh.ElementOrder = 1;
Mesh.SecondOrderLinear = 1; 
Mesh.MshFileVersion = 2.2;
Mesh.Binary = 0;