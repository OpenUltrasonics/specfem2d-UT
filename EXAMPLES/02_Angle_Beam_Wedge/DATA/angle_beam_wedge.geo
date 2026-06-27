SetFactory("OpenCASCADE");

// ----------------------------------------------------
// 1. Mesh Size Definition
// ----------------------------------------------------
lc = 0.001;
eps = 1e-4;

// ----------------------------------------------------
// 2. Geometry Parameters
// ----------------------------------------------------
width = 0.100;
depth = 0.050;

// ----------------------------------------------------
// 3. Steel Block
// ----------------------------------------------------
Rectangle(1) = {0, 0, 0, width, depth};

// ----------------------------------------------------
// 4. EDM Notch
// ----------------------------------------------------
// *Updated Notch X to 0.0798 (See Physics Note Below!)*
notch_x = 0.0798;
notch_w = 0.0005;
notch_h = 0.005;

Rectangle(2) = {notch_x - notch_w/2, 0, 0, notch_w, notch_h};
BooleanDifference(3) = { Surface{1}; Delete; } { Surface{2}; Delete; };

// ----------------------------------------------------
// 5. Rexolite Wedge (Classic "Shoe" Shape)
// Slanted face aiming DOWN-RIGHT towards the notch
// ----------------------------------------------------
wedge_x = 0.010;
wedge_y = depth;

wedge_l = 0.030;
wedge_h_toe = 0.005;     // Short vertical face on the left
wedge_l_flat = 0.005;    // Flat horizontal top section on the right

wedge_angle = 30.6 * Pi / 180.0;

// Calculate the horizontal length of the slant
slant_dx = wedge_l - wedge_l_flat;

// Calculate Height of the Heel mathematically
wedge_h_heel = wedge_h_toe + slant_dx * Tan(wedge_angle);

// Geometry Matches your ASCII:
//      104---------105
//       /          |
//      /           |
//     /            |
//    /             |
// 103              |
//  |               |
//  |               |
// 100-------------101

Point(100) = {wedge_x, wedge_y, 0};                           // Bottom-Left (Toe base)
Point(101) = {wedge_x + wedge_l, wedge_y, 0};                 // Bottom-Right (Heel base)
Point(105) = {wedge_x + wedge_l, wedge_y + wedge_h_heel, 0};  // Top-Right (Heel top)
Point(104) = {wedge_x + slant_dx, wedge_y + wedge_h_heel, 0}; // Top-Left (Start of slant)
Point(103) = {wedge_x, wedge_y + wedge_h_toe, 0};             // Mid-Left (Toe top)

Line(100) = {100, 101}; // Bottom contact with steel
Line(101) = {101, 105}; // Right vertical heel
Line(102) = {105, 104}; // Top flat
Line(103) = {104, 103}; // Slanted transducer face!
Line(104) = {103, 100}; // Left short toe

Curve Loop(100) = {100, 101, 102, 103, 104};
Plane Surface(4) = {100};

// ----------------------------------------------------
// 6. Conformal Interface
// ----------------------------------------------------
BooleanFragments{ Surface{:}; Delete; }{}

// ----------------------------------------------------
// 7. Physical Groups
// ----------------------------------------------------
// Materials MUST be named exactly M1, M2, etc. No underscores!
Physical Surface("M1") = Surface In BoundingBox{-eps, -eps, -eps, width + eps, depth + eps, eps};

Physical Surface("M2") = Surface In BoundingBox{-eps, depth - eps, -eps, width + eps, depth + wedge_h_heel + eps, eps};

// Boundaries MUST be named Bottom, Left, Right, and Top
Physical Curve("Bottom") = Curve In BoundingBox{-eps, -eps, -eps, width + eps, eps, eps};
Physical Curve("Left")   = Curve In BoundingBox{-eps, -eps, -eps, eps, depth + eps, eps};
Physical Curve("Right")  = Curve In BoundingBox{width - eps, -eps, -eps, width + eps, depth + eps, eps};

// We rename "Transducer" to "Top" so the conversion script doesn't crash.
// SPECFEM2D will automatically treat all other unassigned outer edges as free surfaces.
Physical Curve("Top") = {103};

// ----------------------------------------------------
// 8. Mesh Refinement
// ----------------------------------------------------
MeshSize { PointsOf{Surface{:};} } = lc;

// Notch refinement (Gmsh arrays MUST use [])
notch_pts[] = 
Point In BoundingBox
{
  notch_x - 0.01,
  -eps,
  -eps,
  notch_x + 0.01,
  notch_h + 0.01,
  eps
};
MeshSize { notch_pts[] } = lc/3.0;

// Wedge refinement
wedge_pts[] = 
Point In BoundingBox
{
  wedge_x - eps,
  depth - eps,
  -eps,
  wedge_x + wedge_l + eps,
  depth + wedge_h_heel + eps,
  eps
};
MeshSize { wedge_pts[] } = lc/2.0;

// Extra refinement specifically on the slanted transducer face
// (Gmsh expects raw point tags here, do not use the 'Point' keyword)
MeshSize { 103, 104 } = lc/4.0;
// ----------------------------------------------------
// 9. Quad Mesh Generation
// ----------------------------------------------------
Mesh.RecombinationAlgorithm = 1;
Mesh.RecombineAll = 1;
Mesh.Algorithm = 8;
Mesh.ElementOrder = 1;
Mesh.SecondOrderLinear = 1;
Mesh.MshFileVersion = 2.2;
Mesh.Binary = 0;