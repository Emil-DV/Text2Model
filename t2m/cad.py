"""PartDesign helpers that run *inside* FreeCAD (via the bridge).

They build real, editable features — Body, Sketch (fully constrained),
Pad, Pocket, Hole, Fillet, Chamfer — the same objects the GUI tools create.
"""
import itertools
import math
import os
import re

import FreeCAD as App
import Part
import Sketcher

try:
    import FreeCADGui as Gui
except ImportError:
    Gui = None

V = App.Vector
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "out")

# Printer: FDM, 0.4 mm nozzle, 180 x 180 x 100 mm build volume.
BUILD_VOLUME = (180, 180, 100)
CLEAR_SLIDE = 0.3  # clearance for parts that move against each other
CLEAR_PRESS = 0.2  # interference-ish fit for pressed parts
MIN_WALL = 0.8     # 2 perimeters


# ---------- document / body ----------

def new_doc(name):
    if name in App.listDocuments():
        App.closeDocument(name)
    doc = App.newDocument(name)
    if Gui:
        Gui.activateWorkbench("PartDesignWorkbench")
    return doc


def body(doc, name="Body"):
    b = doc.addObject("PartDesign::Body", name)
    if Gui:
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", b)
    return b


def step(doc):
    """Recompute and repaint so each feature appears as it is made."""
    doc.recompute()
    if Gui:
        Gui.SendMsgToActiveView("ViewFit")
        Gui.updateGui()


# ---------- sketches ----------

_PLANES = {"XY": 0, "XZ": 1, "YZ": 2}


def sketch(b, name, plane="XY", offset=0.0):
    """Sketch on a body origin plane, shifted `offset` along its normal."""
    sk = b.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(b.Origin.OriginFeatures[3 + _PLANES[plane]], "")]
    sk.MapMode = "FlatFace"
    sk.AttachmentOffset = App.Placement(V(0, 0, offset), App.Rotation())
    return sk


def _con(sk, *args):
    return sk.addConstraint(Sketcher.Constraint(*args))


def _dist(sk, kind, g, p, value):
    """Signed distance of point (g,p) from the sketch origin along X or Y."""
    if value >= 0:
        _con(sk, kind, -1, 1, g, p, value)
    else:
        _con(sk, kind, g, p, -1, 1, -value)


def _fix_point(sk, g, p, x, y):
    if x == 0 and y == 0:
        _con(sk, "Coincident", g, p, -1, 1)
        return
    if x == 0:
        _con(sk, "PointOnObject", g, p, -2)  # V axis
    else:
        _dist(sk, "DistanceX", g, p, x)
    if y == 0:
        _con(sk, "PointOnObject", g, p, -1)  # H axis
    else:
        _dist(sk, "DistanceY", g, p, y)


def rect(sk, cx, cy, w, h):
    """Fully constrained rectangle centred at (cx, cy)."""
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    pts = [V(x0, y0, 0), V(x1, y0, 0), V(x1, y1, 0), V(x0, y1, 0)]
    g = [sk.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4])) for i in range(4)]
    for i in range(4):
        _con(sk, "Coincident", g[i], 2, g[(i + 1) % 4], 1)
    _con(sk, "Horizontal", g[0]); _con(sk, "Horizontal", g[2])
    _con(sk, "Vertical", g[1]); _con(sk, "Vertical", g[3])
    _con(sk, "DistanceX", g[0], 1, g[0], 2, w)
    _con(sk, "DistanceY", g[1], 1, g[1], 2, h)
    c = sk.addGeometry(Part.Point(V(cx, cy, 0)), True)
    _con(sk, "Symmetric", g[0], 1, g[1], 2, c, 1)
    _fix_point(sk, c, 1, cx, cy)
    return g


def circle(sk, cx, cy, d):
    """Fully constrained circle of diameter d centred at (cx, cy)."""
    g = sk.addGeometry(Part.Circle(V(cx, cy, 0), V(0, 0, 1), d / 2))
    _con(sk, "Diameter", g, d)
    _fix_point(sk, g, 3, cx, cy)
    return g


# ---------- features ----------

def pad(b, sk, length, name="Pad", reversed=False, midplane=False):
    f = b.newObject("PartDesign::Pad", name)
    f.Profile = sk
    f.Length = length
    f.Reversed = reversed
    f.SideType = "Symmetric" if midplane else "One side"  # 1.1: replaces deprecated Midplane
    sk.Visibility = False
    return f


def pocket(b, sk, depth=None, name="Pocket", midplane=False):
    """Cuts opposite the sketch normal. depth=None -> through all."""
    f = b.newObject("PartDesign::Pocket", name)
    f.Profile = sk
    if midplane:
        f.SideType = "Symmetric"
    if depth is None:
        f.Type = "ThroughAll"
    else:
        f.Length = depth
    sk.Visibility = False
    return f


def hole(b, sk, diameter, depth=None, name="Hole", cut=None):
    """Hole at every circle centre in sk. cut=("Counterbore", dia, depth) etc."""
    b.Document.recompute()  # Hole property setters need a valid, recomputed base feature
    f = b.newObject("PartDesign::Hole", name)
    f.Profile = sk
    f.Diameter = diameter
    if depth is None:
        f.DepthType = "ThroughAll"
    else:
        f.DepthType = "Dimension"
        f.Depth = depth
        f.DrillPoint = "Flat"
    if cut:
        f.HoleCutType, f.HoleCutDiameter, f.HoleCutDepth = cut
    sk.Visibility = False
    return f


def edges(feat, pred):
    """Names ('EdgeN') of edges of feat.Shape matching pred(edge)."""
    return [f"Edge{i + 1}" for i, e in enumerate(feat.Shape.Edges) if pred(e)]


def fillet(b, feat, edge_names, radius, name="Fillet"):
    f = b.newObject("PartDesign::Fillet", name)
    f.Base = (feat, edge_names)
    f.Radius = radius
    return f


def chamfer(b, feat, edge_names, size, name="Chamfer"):
    f = b.newObject("PartDesign::Chamfer", name)
    f.Base = (feat, edge_names)
    f.Size = size
    return f


# edge predicates
def is_vertical(e, tol=1e-6):
    a, c = e.Vertexes[0].Point, e.Vertexes[-1].Point
    return len(e.Vertexes) == 2 and abs(a.x - c.x) < tol and abs(a.y - c.y) < tol


def at_z(z, tol=1e-6):
    return lambda e: all(abs(v.Point.z - z) < tol for v in e.Vertexes)


# ---------- verification / output ----------

def check(doc, b, expect_volume=None, rel_tol=1e-3):
    """Raise if anything is broken; return a short report string."""
    problems = []
    for o in doc.Objects:
        if "Invalid" in o.State or "Error" in o.State:
            problems.append(f"{o.Name}: {o.State}")
        if o.TypeId == "Sketcher::SketchObject" and not o.FullyConstrained:
            problems.append(f"{o.Name}: not fully constrained (DoF={o.solve() or o.DoF})")
    s = b.Shape
    if not s.isValid():
        problems.append("body shape is invalid")
    if len(s.Solids) != 1:
        problems.append(f"body has {len(s.Solids)} solids")
    bb = s.BoundBox
    size = (bb.XLength, bb.YLength, bb.ZLength)
    if not all(a <= v for a, v in zip(sorted(size), sorted(BUILD_VOLUME))):
        problems.append(f"does not fit build volume in any axis-aligned orientation: {size}")
    if expect_volume is not None and abs(s.Volume - expect_volume) > rel_tol * expect_volume:
        problems.append(f"volume {s.Volume:.2f} != expected {expect_volume:.2f}")
    report = f"volume={s.Volume:.2f} mm^3  bbox={size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm"
    if problems:
        raise AssertionError(report + "\n" + "\n".join(problems))
    return report


def export(doc, b, base=None):
    """Save .FCStd, .step and .stl into out/. Returns paths."""
    import Mesh
    import MeshPart
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, base or doc.Name)
    doc.saveAs(base + ".FCStd")
    b.Shape.exportStep(base + ".step")
    mesh = MeshPart.meshFromShape(Shape=b.Shape, LinearDeflection=0.01, AngularDeflection=0.1)
    mesh.write(base + ".stl")
    return [base + ext for ext in (".FCStd", ".step", ".stl")]


def shot(doc, name, view="Isometric", size=(1200, 900)):
    """Screenshot the 3D view into out/<name>.png."""
    path = os.path.join(OUT, name + ".png")
    v = Gui.getDocument(doc.Name).ActiveView
    getattr(v, "view" + view)()
    v.fitAll()
    Gui.updateGui()
    v.saveImage(path, size[0], size[1], "White")
    return path


# ---------- spreadsheet-driven parameters ----------

class Params:
    """Spreadsheet 'Params'. rows: section-title strings or
    (alias, value_or_=formula, unit, description). Inputs are white,
    derived (formula) cells grey. Expressions elsewhere use the aliases."""

    def __init__(self, doc, rows):
        self.sheet = s = doc.addObject("Spreadsheet::Sheet", "Params")
        self.names = []
        s.set("A1", "'Name"); s.set("B1", "'Value"); s.set("C1", "'Unit"); s.set("D1", "'Description")
        s.setStyle("A1:D1", "bold")
        r = 2
        for row in rows:
            if isinstance(row, str):
                r += 1
                s.set(f"A{r}", "'" + row)
                s.setStyle(f"A{r}", "bold")
            else:
                alias, val, unit, desc = row
                s.set(f"A{r}", "'" + alias)
                s.set(f"B{r}", str(val))
                s.setAlias(f"B{r}", alias)
                s.set(f"C{r}", "'" + unit)
                s.set(f"D{r}", "'" + desc)
                if str(val).startswith("="):
                    s.setBackground(f"B{r}", (0.85, 0.85, 0.85))
                else:
                    s.setBackground(f"B{r}", (1.0, 1.0, 0.75))
                self.names.append(alias)
            r += 1
        for col, w in (("A", 140), ("B", 90), ("C", 50), ("D", 560)):
            s.setColumnWidth(col, w)
        doc.recompute()

    def __getitem__(self, name):
        return float(self.sheet.get(name))

    def ev(self, expr):
        """Numeric value of an arithmetic expression over aliases."""
        env = {"sqrt": math.sqrt, "pi": math.pi, "abs": abs, **{n: self[n] for n in self.names}}
        return float(eval(expr, {"__builtins__": {}}, env))

    def fc(self, expr):
        """Same expression in FreeCAD syntax (aliases -> Params.alias)."""
        return re.sub(r"\b[A-Za-z_]\w*\b",
                      lambda m: "Params." + m.group(0) if m.group(0) in self.names else m.group(0),
                      expr)

    def bind(self, obj, prop, expr):
        obj.setExpression(prop, self.fc(str(expr)))


class Sk:
    """Sketch whose every dimension is an expression over Params.

    Coordinates are expressions measured from the sketch origin. A leading
    '~' means "initial position only" (left to other constraints)."""

    def __init__(self, P, b, name, plane="XY", offset=None):
        self.P = P
        self.s = sketch(b, name, plane)
        self.n = 0
        if offset is not None:
            P.bind(self.s, "AttachmentOffset.Base.z", offset)

    def con(self, c, expr=None):
        i = self.s.addConstraint(c)
        if expr is not None:
            self.n += 1
            self.s.renameConstraint(i, f"d{self.n}")
            self.P.bind(self.s, f"Constraints.d{self.n}", expr)
        return i

    def fix(self, g, p, xe, ye):
        for e, kind, axis in ((xe, "DistanceX", -2), (ye, "DistanceY", -1)):
            if e is None:
                continue
            if e == "0":
                self.con(Sketcher.Constraint("PointOnObject", g, p, axis))
            else:
                self.con(Sketcher.Constraint(kind, -1, 1, g, p, self.P.ev(e)), e)

    def path(self, pts, arcs=None):
        """Closed outline through pts [(xe, ye)]. arcs[i] = (cxe, cye, re, ccw)
        makes segment pts[i] -> pts[i+1] an arc about (cx, cy), travelled
        counter-clockwise if ccw else clockwise."""
        arcs = arcs or {}
        n = len(pts)
        num = [V(self.P.ev(x.lstrip("~")), self.P.ev(y.lstrip("~")), 0) for x, y in pts]
        ends = []
        for i in range(n):
            a, z = num[i], num[(i + 1) % n]
            if i in arcs:
                cx, cy, rad, ccw = arcs[i]
                c = V(self.P.ev(cx), self.P.ev(cy), 0)
                r = self.P.ev(rad)
                a1 = math.atan2(a.y - c.y, a.x - c.x)
                a2 = math.atan2(z.y - c.y, z.x - c.x)
                lo, hi = (a1, a2) if ccw else (a2, a1)
                sweep = (hi - lo) % (2 * math.pi)
                g = self.s.addGeometry(Part.ArcOfCircle(Part.Circle(c, V(0, 0, 1), r), lo, lo + sweep))
                ends.append(((g, 1), (g, 2)) if ccw else ((g, 2), (g, 1)))
                self.fix(g, 3, cx, cy)
                self.con(Sketcher.Constraint("Radius", g, r), rad)
            else:
                g = self.s.addGeometry(Part.LineSegment(a, z))
                ends.append(((g, 1), (g, 2)))
        for i in range(n):
            (g1, p1), (g2, p2) = ends[i - 1][1], ends[i][0]
            self.con(Sketcher.Constraint("Coincident", g1, p1, g2, p2))
            x, y = pts[i]
            self.fix(g2, p2, None if x.startswith("~") else x, None if y.startswith("~") else y)
        return self

    def rect(self, x0, y0, x1, y1):
        return self.path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def rounded_rect(self, x0, y0, x1, y1, r):
        """Rectangle with all four corners rounded to radius r (r < half of each side)."""
        x0r, x1r, y0r, y1r = f"{x0} + {r}", f"{x1} - ({r})", f"{y0} + {r}", f"{y1} - ({r})"
        return self.path(
            [(x0r, f"~{y0}"), (x1r, f"~{y0}"), (f"~{x1}", y0r), (f"~{x1}", y1r),
             (x1r, f"~{y1}"), (x0r, f"~{y1}"), (f"~{x0}", y1r), (f"~{x0}", y0r)],
            {1: (x1r, y0r, r, True), 3: (x1r, y1r, r, True), 5: (x0r, y1r, r, True), 7: (x0r, y0r, r, True)})

    def circle(self, cx, cy, d):
        g = self.s.addGeometry(Part.Circle(V(self.P.ev(cx), self.P.ev(cy), 0), V(0, 0, 1),
                                           self.P.ev(d) / 2))
        self.fix(g, 3, cx, cy)
        self.con(Sketcher.Constraint("Diameter", g, self.P.ev(d)), d)
        return self

    def d_shape(self, r, fd):
        """'D' profile: circle radius r with a flat at distance fd below centre."""
        hx = f"sqrt(({r})**2 - ({fd})**2)"
        return self.path([(f"~{hx}", f"-({fd})"), (f"~-{hx}", f"-({fd})")], {0: ("0", "0", r, True)})


def revolve(b, sk, name):
    f = b.newObject("PartDesign::Revolution", name)
    f.Profile = sk
    f.ReferenceAxis = (sk, ["V_Axis"])
    f.Angle = 360
    sk.Visibility = False
    return f


def groove(b, sk, name):
    """Revolved cut (PartDesign Groove) of sketch sk about its V axis."""
    f = b.newObject("PartDesign::Groove", name)
    f.Profile = sk
    f.ReferenceAxis = (sk, ["V_Axis"])
    f.Angle = 360
    sk.Visibility = False
    return f


def polar(b, feats, sk, name):
    """Polar pattern of feats about the normal axis of sketch sk."""
    f = b.newObject("PartDesign::PolarPattern", name)
    f.Originals = feats
    f.Axis = (sk, ["N_Axis"])
    b.Tip = f  # newObject leaves Tip before a pattern; later features would skip it
    return f


def linear(b, feats, direction, name):
    """Linear pattern of feats along direction, e.g. (sketch, ["V_Axis"])."""
    f = b.newObject("PartDesign::LinearPattern", name)
    f.Originals = feats
    f.Direction = direction
    b.Tip = f
    return f


def color(obj, rgb):
    """Set display colour (0-1 floats) via the 1.1 material-based ShapeAppearance."""
    if not Gui:
        return
    m = obj.ViewObject.ShapeAppearance[0]
    m.DiffuseColor = rgb
    obj.ViewObject.ShapeAppearance = (m,)


# ---------- assemblies ----------

def print_shape(b, rot):
    """Body shape in its own frame, turned to print orientation, sitting on z=0."""
    s = b.Shape.copy()
    s.Placement = App.Placement(V(), rot)
    bb = s.optimalBoundingBox()  # .BoundBox is loose on rotated curved faces (tori, B-splines)
    s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


def check_assembly(doc, parts):
    """parts: {name: (body, print_rotation)}. Raises on any problem."""
    problems, lines = [], []
    for o in doc.Objects:
        if "Invalid" in o.State or "Error" in o.State:
            problems.append(f"{o.Label}: {o.State}")
        if o.TypeId == "Sketcher::SketchObject" and not o.FullyConstrained:
            problems.append(f"{o.Label}: not fully constrained")
    for name, (b, rot) in parts.items():
        chain, f = set(), b.Tip
        while f:
            chain.add(f.Name)
            f = f.BaseFeature
        stray = [o.Label for o in b.Group if o.isDerivedFrom("PartDesign::Feature") and o.Name not in chain]
        if stray:
            problems.append(f"{name}: features not in the Tip chain (ignored by the body): {stray}")
        s = b.Shape
        if not s.isValid():
            problems.append(f"{name}: invalid shape")
        if len(s.Solids) != 1:
            problems.append(f"{name}: {len(s.Solids)} solids")
        bb = print_shape(b, rot).optimalBoundingBox()
        size = (bb.XLength, bb.YLength, bb.ZLength)
        if not all(a <= v for a, v in zip(size, BUILD_VOLUME)):
            problems.append(f"{name}: print size {size} exceeds build volume {BUILD_VOLUME}")
        lines.append(f"{name:8s} {size[0]:6.1f} x {size[1]:6.1f} x {size[2]:6.1f} mm  {s.Volume / 1000:6.1f} cm3")
    for (n1, (b1, _)), (n2, (b2, _)) in itertools.combinations(parts.items(), 2):
        if b1.Shape.BoundBox.intersect(b2.Shape.BoundBox):
            v = b1.Shape.common(b2.Shape).Volume
            if v > 1e-3:
                problems.append(f"interference {n1} / {n2}: {v:.3f} mm3")
    report = "\n".join(lines)
    if problems:
        raise AssertionError(report + "\n" + "\n".join(problems))
    return report


def section(doc, view="Front"):
    """Rebuild '<doc>_section': every body cut at y=0 (far half kept), colours kept.
    Saves out/<doc>_section.png and leaves the original document active."""
    name = doc.Name + "_section"
    if name in App.listDocuments():
        App.closeDocument(name)
    sd = App.newDocument(name)
    keep = Part.makeBox(1e4, 1e4, 1e4, V(-5e3, 0, -5e3))  # y >= 0
    for b in doc.findObjects("PartDesign::Body"):
        o = sd.addObject("Part::Feature", b.Label)
        o.Shape = b.Shape.common(keep)
        if Gui:
            color(o, b.ViewObject.ShapeAppearance[0].DiffuseColor[:3])
    sd.recompute()
    path = shot(sd, name, view) if Gui else None
    App.setActiveDocument(doc.Name)
    return path


def export_parts(doc, parts, folder):
    """Assembly .FCStd + .step, and one print-oriented STL per part."""
    import Import
    out = os.path.join(OUT, folder)
    os.makedirs(out, exist_ok=True)
    doc.saveAs(os.path.join(out, doc.Name + ".FCStd"))
    Import.export([b for b, _ in parts.values()], os.path.join(out, doc.Name + ".step"))
    export_stls(parts, folder)
    return out


def write_stl(shape, path, linear=0.005, angular_deg=2.0):
    """Fine STL. linear: max chord deviation (mm); angular_deg: max angle between facets."""
    import MeshPart
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=linear,
                               AngularDeflection=math.radians(angular_deg), Relative=False)
    if not m.isSolid() or m.hasNonManifolds() or m.hasSelfIntersections():
        raise AssertionError(f"{path}: mesh is not a clean closed solid")
    m.write(path)
    err = abs(m.Volume - shape.Volume) / shape.Volume * 100
    return (f"{os.path.basename(path):16s} {m.CountFacets:7d} facets  {os.path.getsize(path) / 1e6:5.2f} MB  "
            f"volume error {err:.3f}%")


def export_stls(parts, folder, **mesh):
    """One print-oriented STL per part in out/<folder>/."""
    out = os.path.join(OUT, folder)
    os.makedirs(out, exist_ok=True)
    report = [write_stl(print_shape(b, rot), os.path.join(out, name + ".stl"), **mesh)
              for name, (b, rot) in parts.items()]
    return out + "\n" + "\n".join(report)


def set_print_rotation(b, rot):
    """Store the print orientation on the body itself (saved in the .FCStd)."""
    if "PrintRotation" not in b.PropertiesList:
        b.addProperty("App::PropertyRotation", "PrintRotation", "Text2Model", "Orientation for printing")
    b.PrintRotation = rot


def parts_of(doc):
    """{label: (body, print_rotation)} for every body with a stored print orientation."""
    return {b.Label: (b, b.PrintRotation) for b in doc.findObjects("PartDesign::Body")
            if "PrintRotation" in b.PropertiesList}


def printability(shape, max_overhang_deg=45):
    """(bed contact area, overhang area) in mm2 for a shape sitting on z=0.
    Overhang = downward faces steeper than max_overhang_deg from vertical, not on the bed
    (includes bridges, which are fine when short)."""
    import MeshPart
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.2, Relative=False)
    limit = -math.cos(math.radians(max_overhang_deg))
    bed = over = 0.0
    for f in m.Facets:
        if f.Normal.z < limit:
            if max(p[2] for p in f.Points) < 1e-3:
                bed += f.Area
            else:
                over += f.Area
    return bed, over


def plate(items, gap=4.0):
    """Lay parts out on the bed. items: [(name, shape_on_bed, x, y, rotz_deg)], x/y = where the
    rotated part's bounding-box corner goes. Raises if a part leaves the bed or is closer than
    gap to another. Returns {name: placed shape}."""
    placed = {}
    for name, s, x, y, rz in items:
        s = s.copy()
        s.rotate(V(), V(0, 0, 1), rz)
        bb = s.optimalBoundingBox()
        s.translate(V(x - bb.XMin, y - bb.YMin, -bb.ZMin))
        placed[name] = s
    problems = []
    for n, s in placed.items():
        bb = s.optimalBoundingBox()
        if min(bb.XMin, bb.YMin) < -1e-6 or bb.XMax > BUILD_VOLUME[0] or bb.YMax > BUILD_VOLUME[1] \
                or bb.ZMax > BUILD_VOLUME[2]:
            problems.append(f"{n} off the bed: {bb}")
    for (n1, s1), (n2, s2) in itertools.combinations(placed.items(), 2):
        dist = s1.distToShape(s2)[0]
        if dist < gap - 1e-6:
            problems.append(f"{n1} / {n2} only {dist:.2f} mm apart")
    if problems:
        raise AssertionError("\n".join(problems))
    return placed
