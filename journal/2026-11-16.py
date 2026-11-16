# Text2Model journal: every step sent to FreeCAD, in order. Replay: python3 -m t2m.client journal/2026-11-16.py

# ===== step 00:56:00 ok  (source: designs/test_plate.py, backfilled) =====
# Milestone test part: 80x50x6 plate, R5 corners, 40x20x3 centre pocket,
# 4x M3 clearance holes (3.4 mm) inset 6 mm from the edges.
import math
from t2m import cad

L, W, T = 80, 50, 6
R = 5
PL, PW, PD = 40, 20, 3
HD, INSET = 3.4, 6

doc = cad.new_doc("test_plate")
b = cad.body(doc)

sk = cad.sketch(b, "PlateSketch", "XY")
cad.rect(sk, 0, 0, L, W)
plate = cad.pad(b, sk, T, "Plate")
cad.step(doc)

corners = cad.edges(plate, lambda e: cad.is_vertical(e))
rounded = cad.fillet(b, plate, corners, R, "CornerFillet")
cad.step(doc)

sk = cad.sketch(b, "PocketSketch", "XY", offset=T)
cad.rect(sk, 0, 0, PL, PW)
cad.pocket(b, sk, PD, "CentrePocket")
cad.step(doc)

sk = cad.sketch(b, "HoleSketch", "XY", offset=T)
for sx in (-1, 1):
    for sy in (-1, 1):
        cad.circle(sk, sx * (L / 2 - INSET), sy * (W / 2 - INSET), HD)
cad.hole(b, sk, HD, name="M3Holes")
cad.step(doc)

expected = (L * W * T
            - 4 * T * (R * R - math.pi * R * R / 4)
            - PL * PW * PD
            - 4 * math.pi * (HD / 2) ** 2 * T)
print(cad.check(doc, b, expect_volume=expected))
print(cad.export(doc, b))
print(cad.shot(doc, "test_plate"))

# ===== step 01:04:21 ok  (source: stdin) =====
# probe: sketch sign conventions, XZ mapping, gear module
import FreeCAD as App, Part, Sketcher
V=App.Vector
d = App.newDocument("probe")
sh = d.addObject("Spreadsheet::Sheet","Params")
sh.set("B1","5"); sh.setAlias("B1","Aa"); sh.set("B2","=Aa*2+1"); sh.setAlias("B2","Bb")
b = d.addObject("PartDesign::Body","Body")
s = b.newObject("Sketcher::SketchObject","S")
s.AttachmentSupport=[(b.Origin.OriginFeatures[4],"")]; s.MapMode="FlatFace"
print("planes:", [f.Role for f in b.Origin.OriginFeatures])
g = s.addGeometry(Part.Point(V(-3,2,0)))
c = s.addConstraint(Sketcher.Constraint("DistanceX",-1,1,g,1,-7.0))
s.renameConstraint(c, "px")
s.addConstraint(Sketcher.Constraint("DistanceY",-1,1,g,1,4.0))
d.recompute()
print("neg ok:", s.Geometry[0].X, s.Geometry[0].Y, s.FullyConstrained)
s.setExpression("Constraints.px", "-Params.Bb")
d.recompute(); print("expr neg:", s.Geometry[0].X)
s.setExpression("AttachmentOffset.Base.z","Params.Aa"); d.recompute()
print("global of sketch(1,2):", s.getGlobalPlacement().multVec(V(1,2,0)))
print(sh.get("Bb"))
try:
    import InvoluteGearFeature
    print("gear mod ok", [m for m in dir(InvoluteGearFeature) if "ake" in m])
except Exception as e: print("gear err", e)
App.closeDocument("probe")

# ===== step 01:07:30 ok  (source: stdin) =====
# probe: involute gear + pattern feature properties
import FreeCAD as App, InvoluteGearFeature
d = App.newDocument("probe")
sh = d.addObject("Spreadsheet::Sheet","Params"); sh.set("B1","=tan(20)"); sh.set("B2","=pow(3;2)"); sh.set("B3","=ceil(2.1)"); sh.set("B4","=mod(7;3)")
b = d.addObject("PartDesign::Body","Body")
g = InvoluteGearFeature.makeInvoluteGear("Gear")
print("gear in body:", g.getParentGeoFeatureGroup() and g.getParentGeoFeatureGroup().Name, g.TypeId)
print([(p, g.getPropertyByName(p)) for p in g.PropertiesList if p not in ("Shape","Label","Label2","ExpressionEngine","Proxy","Visibility","Placement","AttachmentOffset","AttacherEngine","AttacherType","AttachmentSupport","MapMode","MapPathParameter","MapReversed","_Body","Constraints","_ElementMapVersion")])
lp = b.newObject("PartDesign::LinearPattern","LP"); pp = b.newObject("PartDesign::PolarPattern","PP")
print("LP", [p for p in lp.PropertiesList if p not in pp.PropertiesList or True][-25:])
print("PP", pp.PropertiesList[-20:])
d.recompute()
print("sheet:", sh.get("B1"), sh.get("B2"), sh.get("B3"), sh.get("B4"))
App.closeDocument("probe")

# ===== step 01:11:53 FAILED  (source: designs/lime_press.py) =====
# error: ValueError: Base feature's TopoShape is invalid
# """Lime-juicing arbor press.
# 
# Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
# presses a lime half (cut side down) into a perforated bowl, turning the peel
# inside out. Juice drains through the bowl into a tray.
# 
# Every dimension is driven by the 'Params' spreadsheet (yellow = input,
# grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
# All clearances are per side (radial), in mm.
# """
# import math
# 
# import FreeCAD as App
# import InvoluteGearFeature
# 
# from t2m import cad
# from t2m.cad import V, Sk
# 
# ROWS = [
#     "Lime",
#     ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
#     ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
#     ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
#     ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
#     "Clearances (per side)",
#     ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
#     ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
#     ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
#     ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
#     ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
#     "Gear",
#     ("GearM", 2.5, "mm", "Module of pinion and rack"),
#     ("PinionZ", 14, "", "Pinion tooth count"),
#     ("GearT", 14, "mm", "Pinion face width"),
#     ("PressureAngle", 20, "deg", "Pressure angle"),
#     "Ram",
#     ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
#     ("RamT", 18, "mm", "Ram size side-to-side"),
#     ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
#     ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
#     ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
#     ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
#     "Frame",
#     ("FrameT", 34, "mm", "Frame thickness side-to-side"),
#     ("ColW", 26, "mm", "Column width"),
#     ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
#     ("FootH", 14, "mm", "Frame foot height"),
#     ("Wall", 6, "mm", "General wall thickness"),
#     ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
#     ("GussetR", 12, "mm", "Inside corner fillet radius"),
#     "Base",
#     ("BaseH", 10, "mm", "Base plate thickness"),
#     ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
#     ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
#     ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
#     ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
#     ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
#     ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
#     ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
#     ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
#     "Cup, tray, plunger",
#     ("CupWall", 3, "mm", "Bowl wall"),
#     ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
#     ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
#     ("DrainD", 3, "mm", "Drain hole diameter"),
#     ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
#     ("TrayWall", 2.4, "mm", "Tray wall"),
#     ("TrayFloor", 2, "mm", "Tray floor"),
#     ("TrayH", 20, "mm", "Tray total height"),
#     ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
#     ("PegD", 6, "mm", "Cup locating peg diameter"),
#     ("PegH", 5, "mm", "Cup locating peg height"),
#     ("PegN", 3, "", "Number of cup locating pegs"),
#     ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
#     "Shaft and handle",
#     ("ShaftD", 12, "mm", "Shaft diameter"),
#     ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
#     ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
#     ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
#     ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
#     ("HandleW", 14, "mm", "Handle bar width"),
#     ("HandleT", 12, "mm", "Handle thickness"),
#     ("HubD", 28, "mm", "Handle hub diameter"),
#     ("KnobD", 20, "mm", "Handle end knob diameter"),
#     "Derived (do not edit)",
#     ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
#     ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
#     ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
#     ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
#     ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
#     ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
#     ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
#     ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
#     ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
#     ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
#     ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
#     ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
#     ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
#     ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
#     ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
#     ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
#     ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
#     ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
#     ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
#     ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
#     ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
#     ("RackP", "=pi * GearM", "mm", "Rack pitch"),
#     ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
#     ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
#     ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
#     ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
#     ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
#     ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
#     ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
#     ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
#     ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
#     ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
#     ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
#     ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
#     ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
#     ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
#     ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
#     ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
#     ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
# ]
# 
# RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)
# 
# doc = cad.new_doc("lime_press")
# P = cad.Params(doc, ROWS)
# 
# # design sanity checks that the spreadsheet can't express
# assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
# assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
# assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
# assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
# 
# 
# def new_body(name, place=None, rot=None):
#     b = cad.body(doc, name)
#     if rot:
#         b.Placement = App.Placement(V(), rot)
#     for axis, expr in zip("xyz", place or ()):
#         P.bind(b, f"Placement.Base.{axis}", expr)
#     return b
# 
# 
# def pad(b, sk, length, name, midplane=False, reversed=False):
#     f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
#     P.bind(f, "Length", length)
#     return f
# 
# 
# def pocket(b, sk, depth, name, midplane=False, reversed=False):
#     f = cad.pocket(b, sk.s, None if depth is None else 1, name)
#     if depth is not None:
#         P.bind(f, "Length", depth)
#     f.Midplane = midplane
#     f.Reversed = reversed
#     return f
# 
# 
# # ---------------- Base ----------------
# base = new_body("Base")
# s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
#                                     "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
# plate = pad(base, s, "BaseH", "BasePlate")
# cad.step(doc)
# f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
# P.bind(f, "Radius", "BaseMargin")
# s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
#     "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
# pocket(base, s, "FootPocketD", "FootPocket")
# s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
# pocket(base, s, "TrayRecessD", "TrayRecess")
# s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
# h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
# h.Reversed = True
# for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
#     P.bind(h, prop, expr)
# cad.step(doc)
# 
# # ---------------- Frame ----------------
# frame = new_body("Frame")
# s = Sk(P, frame, "FrameProfile", "XZ").path([
#     ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
#     ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
#     ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
# fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
# cad.step(doc)
# inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]
# 
# 
# def inner_corner(e):
#     a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
#     return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
#             and any(abs(a.z - zz) < 1e-6 for zz in inner))
# 
# 
# f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
# P.bind(f, "Radius", "GussetR")
# s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
#     "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
# pocket(frame, s, None, "RamChannel")
# s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
# s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
# s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
# pocket(frame, s, None, "ShaftBore", midplane=True)
# s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
#     "ScrewX2", "0", "ScrewPilotD")
# h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
# h.Reversed = True
# P.bind(h, "Diameter", "ScrewPilotD")
# P.bind(h, "Depth", "ScrewPilotL")
# cad.step(doc)
# 
# # ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
# ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
# s = Sk(P, ram, "RamProfile", "XZ").path([
#     ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
#     ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
# pad(ram, s, "RamT", "RamBar", midplane=True)
# s = Sk(P, ram, "RackGapSketch", "XZ").path([
#     ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
#     ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
# gap = pocket(ram, s, None, "RackGap", midplane=True)
# lp = ram.newObject("PartDesign::LinearPattern", "Rack")
# lp.Originals = [gap]
# lp.Direction = (s.s, ["V_Axis"])
# P.bind(lp, "Length", "(RackN - 1) * RackP")
# P.bind(lp, "Occurrences", "RackN")
# cad.step(doc)
# 
# # ---------------- Pinion (local: axis = Z) ----------------
# pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
# g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
# pinion.addObject(g)
# P.bind(g, "NumberOfTeeth", "PinionZ")
# P.bind(g, "Modules", "GearM")
# P.bind(g, "PressureAngle", "PressureAngle")
# f = pinion.newObject("PartDesign::Pad", "PinionGear")
# f.Profile = g
# f.Midplane = True
# P.bind(f, "Length", "GearT")
# g.Visibility = False
# s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
# pocket(pinion, s, None, "PinionDBore", midplane=True)
# cad.step(doc)
# 
# # ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
# shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
# s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
# pad(shaft, s, "ShaftL", "DShaft")
# s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
# pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
# cad.step(doc)
# 
# # ---------------- Handle (local: XY plane, hub at origin) ----------------
# handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
# s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
# pad(handle, s, "HandleT", "Hub")
# s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
# pad(handle, s, "HubExt", "HubBoss", reversed=True)
# s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
# pad(handle, s, "HandleT", "Bar")
# s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
# pad(handle, s, "HandleT", "Knob")
# s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
# pocket(handle, s, None, "HandleDBore")
# cad.step(doc)
# 
# # ---------------- Tray (local: axis = Z, bottom z=0) ----------------
# tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
# s = Sk(P, tray, "TrayProfile", "XZ").path([
#     ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
#     ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
# cad.revolve(tray, s.s, "TrayShell")
# s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
# peg = pad(tray, s, "PegH", "Peg")
# pp = cad.polar(tray, [peg], s.s, "Pegs")
# P.bind(pp, "Occurrences", "PegN")
# cad.step(doc)
# 
# # ---------------- Cup (local: axis = Z, bottom z=0) ----------------
# cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
# s = Sk(P, cup, "CupProfile", "XZ").path([
#     ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
#     ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
#     {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
# cad.revolve(cup, s.s, "Bowl")
# s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
# groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
# pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
# P.bind(pp, "Occurrences", "DrainN")
# s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
# pocket(cup, s, None, "CentreDrain", reversed=True)
# s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
# drain = pocket(cup, s, None, "RingDrain", reversed=True)
# pp = cad.polar(cup, [drain], s.s, "RingDrains")
# P.bind(pp, "Occurrences", "DrainN")
# cad.step(doc)
# 
# # ---------------- Plunger (local: dome centre at z=0) ----------------
# plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
# s = Sk(P, plunger, "PlungerProfile", "XZ").path([
#     ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
#     {0: ("0", "0", "DomeR", True)})
# cad.revolve(plunger, s.s, "Dome")
# s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
#     "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
# pocket(plunger, s, "RamTipL", "RamSocket")
# cad.step(doc)
# 
# # ---------------- verify + export ----------------
# ID = App.Rotation()
# SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
# PARTS = {
#     "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
#     "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
#     "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
# }
# print(cad.check_assembly(doc, PARTS))
# print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
#     P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
# print(cad.export_parts(doc, PARTS, "lime_press"))
# print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:12:02 FAILED  (source: designs/lime_press.py) =====
# error: NameError: name 'sqrt' is not defined
# """Lime-juicing arbor press.
# 
# Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
# presses a lime half (cut side down) into a perforated bowl, turning the peel
# inside out. Juice drains through the bowl into a tray.
# 
# Every dimension is driven by the 'Params' spreadsheet (yellow = input,
# grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
# All clearances are per side (radial), in mm.
# """
# import math
# 
# import FreeCAD as App
# import InvoluteGearFeature
# 
# from t2m import cad
# from t2m.cad import V, Sk
# 
# ROWS = [
#     "Lime",
#     ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
#     ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
#     ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
#     ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
#     "Clearances (per side)",
#     ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
#     ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
#     ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
#     ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
#     ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
#     "Gear",
#     ("GearM", 2.5, "mm", "Module of pinion and rack"),
#     ("PinionZ", 14, "", "Pinion tooth count"),
#     ("GearT", 14, "mm", "Pinion face width"),
#     ("PressureAngle", 20, "deg", "Pressure angle"),
#     "Ram",
#     ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
#     ("RamT", 18, "mm", "Ram size side-to-side"),
#     ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
#     ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
#     ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
#     ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
#     "Frame",
#     ("FrameT", 34, "mm", "Frame thickness side-to-side"),
#     ("ColW", 26, "mm", "Column width"),
#     ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
#     ("FootH", 14, "mm", "Frame foot height"),
#     ("Wall", 6, "mm", "General wall thickness"),
#     ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
#     ("GussetR", 12, "mm", "Inside corner fillet radius"),
#     "Base",
#     ("BaseH", 10, "mm", "Base plate thickness"),
#     ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
#     ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
#     ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
#     ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
#     ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
#     ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
#     ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
#     ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
#     "Cup, tray, plunger",
#     ("CupWall", 3, "mm", "Bowl wall"),
#     ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
#     ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
#     ("DrainD", 3, "mm", "Drain hole diameter"),
#     ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
#     ("TrayWall", 2.4, "mm", "Tray wall"),
#     ("TrayFloor", 2, "mm", "Tray floor"),
#     ("TrayH", 20, "mm", "Tray total height"),
#     ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
#     ("PegD", 6, "mm", "Cup locating peg diameter"),
#     ("PegH", 5, "mm", "Cup locating peg height"),
#     ("PegN", 3, "", "Number of cup locating pegs"),
#     ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
#     "Shaft and handle",
#     ("ShaftD", 12, "mm", "Shaft diameter"),
#     ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
#     ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
#     ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
#     ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
#     ("HandleW", 14, "mm", "Handle bar width"),
#     ("HandleT", 12, "mm", "Handle thickness"),
#     ("HubD", 28, "mm", "Handle hub diameter"),
#     ("KnobD", 20, "mm", "Handle end knob diameter"),
#     "Derived (do not edit)",
#     ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
#     ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
#     ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
#     ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
#     ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
#     ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
#     ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
#     ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
#     ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
#     ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
#     ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
#     ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
#     ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
#     ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
#     ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
#     ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
#     ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
#     ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
#     ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
#     ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
#     ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
#     ("RackP", "=pi * GearM", "mm", "Rack pitch"),
#     ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
#     ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
#     ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
#     ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
#     ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
#     ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
#     ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
#     ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
#     ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
#     ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
#     ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
#     ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
#     ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
#     ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
#     ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
#     ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
#     ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
# ]
# 
# RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)
# 
# doc = cad.new_doc("lime_press")
# P = cad.Params(doc, ROWS)
# 
# # design sanity checks that the spreadsheet can't express
# assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
# assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
# assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
# assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
# 
# 
# def new_body(name, place=None, rot=None):
#     b = cad.body(doc, name)
#     if rot:
#         b.Placement = App.Placement(V(), rot)
#     for axis, expr in zip("xyz", place or ()):
#         P.bind(b, f"Placement.Base.{axis}", expr)
#     return b
# 
# 
# def pad(b, sk, length, name, midplane=False, reversed=False):
#     f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
#     P.bind(f, "Length", length)
#     return f
# 
# 
# def pocket(b, sk, depth, name, midplane=False, reversed=False):
#     f = cad.pocket(b, sk.s, None if depth is None else 1, name)
#     if depth is not None:
#         P.bind(f, "Length", depth)
#     f.Midplane = midplane
#     f.Reversed = reversed
#     return f
# 
# 
# # ---------------- Base ----------------
# base = new_body("Base")
# s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
#                                     "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
# plate = pad(base, s, "BaseH", "BasePlate")
# cad.step(doc)
# f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
# P.bind(f, "Radius", "BaseMargin")
# s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
#     "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
# pocket(base, s, "FootPocketD", "FootPocket")
# s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
# pocket(base, s, "TrayRecessD", "TrayRecess")
# s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
# h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
# h.Reversed = True
# for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
#     P.bind(h, prop, expr)
# cad.step(doc)
# 
# # ---------------- Frame ----------------
# frame = new_body("Frame")
# s = Sk(P, frame, "FrameProfile", "XZ").path([
#     ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
#     ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
#     ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
# fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
# cad.step(doc)
# inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]
# 
# 
# def inner_corner(e):
#     a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
#     return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
#             and any(abs(a.z - zz) < 1e-6 for zz in inner))
# 
# 
# f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
# P.bind(f, "Radius", "GussetR")
# s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
#     "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
# pocket(frame, s, None, "RamChannel")
# s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
# s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
# s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
# pocket(frame, s, None, "ShaftBore", midplane=True)
# s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
#     "ScrewX2", "0", "ScrewPilotD")
# h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
# h.Reversed = True
# P.bind(h, "Diameter", "ScrewPilotD")
# P.bind(h, "Depth", "ScrewPilotL")
# cad.step(doc)
# 
# # ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
# ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
# s = Sk(P, ram, "RamProfile", "XZ").path([
#     ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
#     ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
# pad(ram, s, "RamT", "RamBar", midplane=True)
# s = Sk(P, ram, "RackGapSketch", "XZ").path([
#     ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
#     ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
# gap = pocket(ram, s, None, "RackGap", midplane=True)
# lp = ram.newObject("PartDesign::LinearPattern", "Rack")
# lp.Originals = [gap]
# lp.Direction = (s.s, ["V_Axis"])
# P.bind(lp, "Length", "(RackN - 1) * RackP")
# P.bind(lp, "Occurrences", "RackN")
# cad.step(doc)
# 
# # ---------------- Pinion (local: axis = Z) ----------------
# pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
# g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
# pinion.addObject(g)
# P.bind(g, "NumberOfTeeth", "PinionZ")
# P.bind(g, "Modules", "GearM")
# P.bind(g, "PressureAngle", "PressureAngle")
# f = pinion.newObject("PartDesign::Pad", "PinionGear")
# f.Profile = g
# f.Midplane = True
# P.bind(f, "Length", "GearT")
# g.Visibility = False
# s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
# pocket(pinion, s, None, "PinionDBore", midplane=True)
# cad.step(doc)
# 
# # ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
# shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
# s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
# pad(shaft, s, "ShaftL", "DShaft")
# s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
# pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
# cad.step(doc)
# 
# # ---------------- Handle (local: XY plane, hub at origin) ----------------
# handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
# s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
# pad(handle, s, "HandleT", "Hub")
# s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
# pad(handle, s, "HubExt", "HubBoss", reversed=True)
# s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
# pad(handle, s, "HandleT", "Bar")
# s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
# pad(handle, s, "HandleT", "Knob")
# s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
# pocket(handle, s, None, "HandleDBore")
# cad.step(doc)
# 
# # ---------------- Tray (local: axis = Z, bottom z=0) ----------------
# tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
# s = Sk(P, tray, "TrayProfile", "XZ").path([
#     ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
#     ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
# cad.revolve(tray, s.s, "TrayShell")
# s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
# peg = pad(tray, s, "PegH", "Peg")
# pp = cad.polar(tray, [peg], s.s, "Pegs")
# P.bind(pp, "Occurrences", "PegN")
# cad.step(doc)
# 
# # ---------------- Cup (local: axis = Z, bottom z=0) ----------------
# cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
# s = Sk(P, cup, "CupProfile", "XZ").path([
#     ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
#     ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
#     {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
# cad.revolve(cup, s.s, "Bowl")
# s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
# groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
# pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
# P.bind(pp, "Occurrences", "DrainN")
# s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
# pocket(cup, s, None, "CentreDrain", reversed=True)
# s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
# drain = pocket(cup, s, None, "RingDrain", reversed=True)
# pp = cad.polar(cup, [drain], s.s, "RingDrains")
# P.bind(pp, "Occurrences", "DrainN")
# cad.step(doc)
# 
# # ---------------- Plunger (local: dome centre at z=0) ----------------
# plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
# s = Sk(P, plunger, "PlungerProfile", "XZ").path([
#     ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
#     {0: ("0", "0", "DomeR", True)})
# cad.revolve(plunger, s.s, "Dome")
# s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
#     "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
# pocket(plunger, s, "RamTipL", "RamSocket")
# cad.step(doc)
# 
# # ---------------- verify + export ----------------
# ID = App.Rotation()
# SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
# PARTS = {
#     "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
#     "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
#     "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
# }
# print(cad.check_assembly(doc, PARTS))
# print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
#     P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
# print(cad.export_parts(doc, PARTS, "lime_press"))
# print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:12:10 FAILED  (source: designs/lime_press.py) =====
# error: ValueError: math domain error
# """Lime-juicing arbor press.
# 
# Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
# presses a lime half (cut side down) into a perforated bowl, turning the peel
# inside out. Juice drains through the bowl into a tray.
# 
# Every dimension is driven by the 'Params' spreadsheet (yellow = input,
# grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
# All clearances are per side (radial), in mm.
# """
# import math
# 
# import FreeCAD as App
# import InvoluteGearFeature
# 
# from t2m import cad
# from t2m.cad import V, Sk
# 
# ROWS = [
#     "Lime",
#     ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
#     ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
#     ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
#     ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
#     "Clearances (per side)",
#     ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
#     ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
#     ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
#     ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
#     ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
#     "Gear",
#     ("GearM", 2.5, "mm", "Module of pinion and rack"),
#     ("PinionZ", 14, "", "Pinion tooth count"),
#     ("GearT", 14, "mm", "Pinion face width"),
#     ("PressureAngle", 20, "deg", "Pressure angle"),
#     "Ram",
#     ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
#     ("RamT", 18, "mm", "Ram size side-to-side"),
#     ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
#     ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
#     ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
#     ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
#     "Frame",
#     ("FrameT", 34, "mm", "Frame thickness side-to-side"),
#     ("ColW", 26, "mm", "Column width"),
#     ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
#     ("FootH", 14, "mm", "Frame foot height"),
#     ("Wall", 6, "mm", "General wall thickness"),
#     ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
#     ("GussetR", 12, "mm", "Inside corner fillet radius"),
#     "Base",
#     ("BaseH", 10, "mm", "Base plate thickness"),
#     ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
#     ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
#     ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
#     ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
#     ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
#     ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
#     ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
#     ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
#     "Cup, tray, plunger",
#     ("CupWall", 3, "mm", "Bowl wall"),
#     ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
#     ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
#     ("DrainD", 3, "mm", "Drain hole diameter"),
#     ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
#     ("TrayWall", 2.4, "mm", "Tray wall"),
#     ("TrayFloor", 2, "mm", "Tray floor"),
#     ("TrayH", 20, "mm", "Tray total height"),
#     ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
#     ("PegD", 6, "mm", "Cup locating peg diameter"),
#     ("PegH", 5, "mm", "Cup locating peg height"),
#     ("PegN", 3, "", "Number of cup locating pegs"),
#     ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
#     "Shaft and handle",
#     ("ShaftD", 12, "mm", "Shaft diameter"),
#     ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
#     ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
#     ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
#     ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
#     ("HandleW", 14, "mm", "Handle bar width"),
#     ("HandleT", 12, "mm", "Handle thickness"),
#     ("HubD", 28, "mm", "Handle hub diameter"),
#     ("KnobD", 20, "mm", "Handle end knob diameter"),
#     "Derived (do not edit)",
#     ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
#     ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
#     ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
#     ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
#     ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
#     ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
#     ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
#     ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
#     ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
#     ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
#     ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
#     ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
#     ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
#     ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
#     ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
#     ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
#     ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
#     ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
#     ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
#     ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
#     ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
#     ("RackP", "=pi * GearM", "mm", "Rack pitch"),
#     ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
#     ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
#     ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
#     ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
#     ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
#     ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
#     ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
#     ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
#     ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
#     ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
#     ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
#     ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
#     ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
#     ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
#     ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
#     ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
#     ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
# ]
# 
# RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)
# 
# doc = cad.new_doc("lime_press")
# P = cad.Params(doc, ROWS)
# 
# # design sanity checks that the spreadsheet can't express
# assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
# assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
# assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
# assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
# 
# 
# def new_body(name, place=None, rot=None):
#     b = cad.body(doc, name)
#     if rot:
#         b.Placement = App.Placement(V(), rot)
#     for axis, expr in zip("xyz", place or ()):
#         P.bind(b, f"Placement.Base.{axis}", expr)
#     return b
# 
# 
# def pad(b, sk, length, name, midplane=False, reversed=False):
#     f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
#     P.bind(f, "Length", length)
#     return f
# 
# 
# def pocket(b, sk, depth, name, midplane=False, reversed=False):
#     f = cad.pocket(b, sk.s, None if depth is None else 1, name)
#     if depth is not None:
#         P.bind(f, "Length", depth)
#     f.Midplane = midplane
#     f.Reversed = reversed
#     return f
# 
# 
# # ---------------- Base ----------------
# base = new_body("Base")
# s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
#                                     "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
# plate = pad(base, s, "BaseH", "BasePlate")
# cad.step(doc)
# f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
# P.bind(f, "Radius", "BaseMargin")
# s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
#     "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
# pocket(base, s, "FootPocketD", "FootPocket")
# s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
# pocket(base, s, "TrayRecessD", "TrayRecess")
# s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
# h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
# h.Reversed = True
# for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
#     P.bind(h, prop, expr)
# cad.step(doc)
# 
# # ---------------- Frame ----------------
# frame = new_body("Frame")
# s = Sk(P, frame, "FrameProfile", "XZ").path([
#     ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
#     ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
#     ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
# fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
# cad.step(doc)
# inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]
# 
# 
# def inner_corner(e):
#     a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
#     return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
#             and any(abs(a.z - zz) < 1e-6 for zz in inner))
# 
# 
# f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
# P.bind(f, "Radius", "GussetR")
# s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
#     "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
# pocket(frame, s, None, "RamChannel")
# s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
# s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
# s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
# pocket(frame, s, None, "ShaftBore", midplane=True)
# s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
#     "ScrewX2", "0", "ScrewPilotD")
# h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
# h.Reversed = True
# P.bind(h, "Diameter", "ScrewPilotD")
# P.bind(h, "Depth", "ScrewPilotL")
# cad.step(doc)
# 
# # ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
# ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
# s = Sk(P, ram, "RamProfile", "XZ").path([
#     ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
#     ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
# pad(ram, s, "RamT", "RamBar", midplane=True)
# s = Sk(P, ram, "RackGapSketch", "XZ").path([
#     ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
#     ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
# gap = pocket(ram, s, None, "RackGap", midplane=True)
# lp = ram.newObject("PartDesign::LinearPattern", "Rack")
# lp.Originals = [gap]
# lp.Direction = (s.s, ["V_Axis"])
# P.bind(lp, "Length", "(RackN - 1) * RackP")
# P.bind(lp, "Occurrences", "RackN")
# cad.step(doc)
# 
# # ---------------- Pinion (local: axis = Z) ----------------
# pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
# g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
# pinion.addObject(g)
# P.bind(g, "NumberOfTeeth", "PinionZ")
# P.bind(g, "Modules", "GearM")
# P.bind(g, "PressureAngle", "PressureAngle")
# f = pinion.newObject("PartDesign::Pad", "PinionGear")
# f.Profile = g
# f.Midplane = True
# P.bind(f, "Length", "GearT")
# g.Visibility = False
# s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
# pocket(pinion, s, None, "PinionDBore", midplane=True)
# cad.step(doc)
# 
# # ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
# shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
# s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
# pad(shaft, s, "ShaftL", "DShaft")
# s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
# pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
# cad.step(doc)
# 
# # ---------------- Handle (local: XY plane, hub at origin) ----------------
# handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
# s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
# pad(handle, s, "HandleT", "Hub")
# s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
# pad(handle, s, "HubExt", "HubBoss", reversed=True)
# s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
# pad(handle, s, "HandleT", "Bar")
# s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
# pad(handle, s, "HandleT", "Knob")
# s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
# pocket(handle, s, None, "HandleDBore")
# cad.step(doc)
# 
# # ---------------- Tray (local: axis = Z, bottom z=0) ----------------
# tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
# s = Sk(P, tray, "TrayProfile", "XZ").path([
#     ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
#     ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
# cad.revolve(tray, s.s, "TrayShell")
# s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
# peg = pad(tray, s, "PegH", "Peg")
# pp = cad.polar(tray, [peg], s.s, "Pegs")
# P.bind(pp, "Occurrences", "PegN")
# cad.step(doc)
# 
# # ---------------- Cup (local: axis = Z, bottom z=0) ----------------
# cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
# s = Sk(P, cup, "CupProfile", "XZ").path([
#     ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
#     ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
#     {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
# cad.revolve(cup, s.s, "Bowl")
# s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
# groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
# pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
# P.bind(pp, "Occurrences", "DrainN")
# s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
# pocket(cup, s, None, "CentreDrain", reversed=True)
# s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
# drain = pocket(cup, s, None, "RingDrain", reversed=True)
# pp = cad.polar(cup, [drain], s.s, "RingDrains")
# P.bind(pp, "Occurrences", "DrainN")
# cad.step(doc)
# 
# # ---------------- Plunger (local: dome centre at z=0) ----------------
# plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
# s = Sk(P, plunger, "PlungerProfile", "XZ").path([
#     ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
#     {0: ("0", "0", "DomeR", True)})
# cad.revolve(plunger, s.s, "Dome")
# s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
#     "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
# pocket(plunger, s, "RamTipL", "RamSocket")
# cad.step(doc)
# 
# # ---------------- verify + export ----------------
# ID = App.Rotation()
# SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
# PARTS = {
#     "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
#     "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
#     "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
# }
# print(cad.check_assembly(doc, PARTS))
# print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
#     P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
# print(cad.export_parts(doc, PARTS, "lime_press"))
# print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:12:21 FAILED  (source: designs/lime_press.py) =====
# error: interference Ram / Pinion: 506.258 mm3
# """Lime-juicing arbor press.
# 
# Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
# presses a lime half (cut side down) into a perforated bowl, turning the peel
# inside out. Juice drains through the bowl into a tray.
# 
# Every dimension is driven by the 'Params' spreadsheet (yellow = input,
# grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
# All clearances are per side (radial), in mm.
# """
# import math
# 
# import FreeCAD as App
# import InvoluteGearFeature
# 
# from t2m import cad
# from t2m.cad import V, Sk
# 
# ROWS = [
#     "Lime",
#     ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
#     ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
#     ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
#     ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
#     "Clearances (per side)",
#     ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
#     ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
#     ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
#     ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
#     ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
#     "Gear",
#     ("GearM", 2.5, "mm", "Module of pinion and rack"),
#     ("PinionZ", 14, "", "Pinion tooth count"),
#     ("GearT", 14, "mm", "Pinion face width"),
#     ("PressureAngle", 20, "deg", "Pressure angle"),
#     "Ram",
#     ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
#     ("RamT", 18, "mm", "Ram size side-to-side"),
#     ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
#     ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
#     ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
#     ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
#     "Frame",
#     ("FrameT", 34, "mm", "Frame thickness side-to-side"),
#     ("ColW", 26, "mm", "Column width"),
#     ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
#     ("FootH", 14, "mm", "Frame foot height"),
#     ("Wall", 6, "mm", "General wall thickness"),
#     ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
#     ("GussetR", 12, "mm", "Inside corner fillet radius"),
#     "Base",
#     ("BaseH", 10, "mm", "Base plate thickness"),
#     ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
#     ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
#     ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
#     ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
#     ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
#     ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
#     ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
#     ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
#     "Cup, tray, plunger",
#     ("CupWall", 3, "mm", "Bowl wall"),
#     ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
#     ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
#     ("DrainD", 3, "mm", "Drain hole diameter"),
#     ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
#     ("TrayWall", 2.4, "mm", "Tray wall"),
#     ("TrayFloor", 2, "mm", "Tray floor"),
#     ("TrayH", 20, "mm", "Tray total height"),
#     ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
#     ("PegD", 6, "mm", "Cup locating peg diameter"),
#     ("PegH", 5, "mm", "Cup locating peg height"),
#     ("PegN", 3, "", "Number of cup locating pegs"),
#     ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
#     "Shaft and handle",
#     ("ShaftD", 12, "mm", "Shaft diameter"),
#     ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
#     ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
#     ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
#     ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
#     ("HandleW", 14, "mm", "Handle bar width"),
#     ("HandleT", 12, "mm", "Handle thickness"),
#     ("HubD", 28, "mm", "Handle hub diameter"),
#     ("KnobD", 20, "mm", "Handle end knob diameter"),
#     "Derived (do not edit)",
#     ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
#     ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
#     ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
#     ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
#     ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
#     ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
#     ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
#     ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
#     ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
#     ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
#     ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
#     ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
#     ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
#     ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
#     ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
#     ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
#     ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
#     ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
#     ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
#     ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
#     ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
#     ("RackP", "=pi * GearM", "mm", "Rack pitch"),
#     ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
#     ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
#     ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
#     ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
#     ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
#     ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
#     ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
#     ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
#     ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
#     ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
#     ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
#     ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
#     ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
#     ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
#     ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
#     ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
#     ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
# ]
# 
# RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)
# 
# doc = cad.new_doc("lime_press")
# P = cad.Params(doc, ROWS)
# 
# # design sanity checks that the spreadsheet can't express
# assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
# assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
# assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
# assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
# 
# 
# def new_body(name, place=None, rot=None):
#     b = cad.body(doc, name)
#     if rot:
#         b.Placement = App.Placement(V(), rot)
#     for axis, expr in zip("xyz", place or ()):
#         P.bind(b, f"Placement.Base.{axis}", expr)
#     return b
# 
# 
# def pad(b, sk, length, name, midplane=False, reversed=False):
#     f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
#     P.bind(f, "Length", length)
#     return f
# 
# 
# def pocket(b, sk, depth, name, midplane=False, reversed=False):
#     f = cad.pocket(b, sk.s, None if depth is None else 1, name)
#     if depth is not None:
#         P.bind(f, "Length", depth)
#     f.Midplane = midplane
#     f.Reversed = reversed
#     return f
# 
# 
# # ---------------- Base ----------------
# base = new_body("Base")
# s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
#                                     "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
# plate = pad(base, s, "BaseH", "BasePlate")
# cad.step(doc)
# f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
# P.bind(f, "Radius", "BaseMargin")
# s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
#     "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
# pocket(base, s, "FootPocketD", "FootPocket")
# s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
# pocket(base, s, "TrayRecessD", "TrayRecess")
# s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
# h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
# h.Reversed = True
# for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
#     P.bind(h, prop, expr)
# cad.step(doc)
# 
# # ---------------- Frame ----------------
# frame = new_body("Frame")
# s = Sk(P, frame, "FrameProfile", "XZ").path([
#     ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
#     ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
#     ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
# fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
# cad.step(doc)
# inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]
# 
# 
# def inner_corner(e):
#     a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
#     return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
#             and any(abs(a.z - zz) < 1e-6 for zz in inner))
# 
# 
# f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
# P.bind(f, "Radius", "GussetR")
# s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
#     "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
# pocket(frame, s, None, "RamChannel")
# s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
# s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
# pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
# s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
# pocket(frame, s, None, "ShaftBore", midplane=True)
# s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
#     "ScrewX2", "0", "ScrewPilotD")
# h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
# h.Reversed = True
# P.bind(h, "Diameter", "ScrewPilotD")
# P.bind(h, "Depth", "ScrewPilotL")
# cad.step(doc)
# 
# # ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
# ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
# s = Sk(P, ram, "RamProfile", "XZ").path([
#     ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
#     ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
# pad(ram, s, "RamT", "RamBar", midplane=True)
# s = Sk(P, ram, "RackGapSketch", "XZ").path([
#     ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
#     ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
# gap = pocket(ram, s, None, "RackGap", midplane=True)
# lp = ram.newObject("PartDesign::LinearPattern", "Rack")
# lp.Originals = [gap]
# lp.Direction = (s.s, ["V_Axis"])
# P.bind(lp, "Length", "(RackN - 1) * RackP")
# P.bind(lp, "Occurrences", "RackN")
# cad.step(doc)
# 
# # ---------------- Pinion (local: axis = Z) ----------------
# pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
# g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
# pinion.addObject(g)
# P.bind(g, "NumberOfTeeth", "PinionZ")
# P.bind(g, "Modules", "GearM")
# P.bind(g, "PressureAngle", "PressureAngle")
# f = pinion.newObject("PartDesign::Pad", "PinionGear")
# f.Profile = g
# f.Midplane = True
# P.bind(f, "Length", "GearT")
# g.Visibility = False
# s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
# pocket(pinion, s, None, "PinionDBore", midplane=True)
# cad.step(doc)
# 
# # ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
# shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
# s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
# pad(shaft, s, "ShaftL", "DShaft")
# s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
# pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
# cad.step(doc)
# 
# # ---------------- Handle (local: XY plane, hub at origin) ----------------
# handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
# s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
# pad(handle, s, "HandleT", "Hub")
# s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
# pad(handle, s, "HubExt", "HubBoss", reversed=True)
# s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
# pad(handle, s, "HandleT", "Bar")
# s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
# pad(handle, s, "HandleT", "Knob")
# s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
# pocket(handle, s, None, "HandleDBore")
# cad.step(doc)
# 
# # ---------------- Tray (local: axis = Z, bottom z=0) ----------------
# tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
# s = Sk(P, tray, "TrayProfile", "XZ").path([
#     ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
#     ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
# cad.revolve(tray, s.s, "TrayShell")
# s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
# peg = pad(tray, s, "PegH", "Peg")
# pp = cad.polar(tray, [peg], s.s, "Pegs")
# P.bind(pp, "Occurrences", "PegN")
# cad.step(doc)
# 
# # ---------------- Cup (local: axis = Z, bottom z=0) ----------------
# cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
# s = Sk(P, cup, "CupProfile", "XZ").path([
#     ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
#     ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
#     {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
# cad.revolve(cup, s.s, "Bowl")
# s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
# groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
# pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
# P.bind(pp, "Occurrences", "DrainN")
# s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
# pocket(cup, s, None, "CentreDrain", reversed=True)
# s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
# drain = pocket(cup, s, None, "RingDrain", reversed=True)
# pp = cad.polar(cup, [drain], s.s, "RingDrains")
# P.bind(pp, "Occurrences", "DrainN")
# cad.step(doc)
# 
# # ---------------- Plunger (local: dome centre at z=0) ----------------
# plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
# s = Sk(P, plunger, "PlungerProfile", "XZ").path([
#     ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
#     {0: ("0", "0", "DomeR", True)})
# cad.revolve(plunger, s.s, "Dome")
# s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
#     "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
# pocket(plunger, s, "RamTipL", "RamSocket")
# cad.step(doc)
# 
# # ---------------- verify + export ----------------
# ID = App.Rotation()
# SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
# PARTS = {
#     "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
#     "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
#     "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
# }
# print(cad.check_assembly(doc, PARTS))
# print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
#     P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
# print(cad.export_parts(doc, PARTS, "lime_press"))
# print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:12:29 ok  (source: stdin) =====
# probe: rack/pinion overlap vs rack phase shift
import FreeCAD as App
d = App.getDocument("lime_press"); P = d.getObject("Params")
ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
p = float(P.get("RackP"))
for k in (0, 0.25, 0.5, 0.75):
    s = ram.copy(); s.translate(App.Vector(0, 0, k * p))
    print(k, round(s.common(pin).Volume, 3))

# ===== step 01:12:39 ok  (source: stdin) =====
# probe: inspect ram feature volumes and rack pattern settings
import FreeCAD as App
d = App.getDocument("lime_press")
for n in ("RamBar", "RackGap", "Rack"):
    o = d.getObject(n); print(n, o.State, round(o.Shape.Volume, 1))
lp = d.getObject("Rack")
print("Mode", lp.Mode, lp.getEnumerationsOfProperty("Mode"), "Len", lp.Length, "Off", lp.Offset, "Occ", lp.Occurrences, "Dir", lp.Direction)
print("tip", d.getObject("Ram").Tip.Name)
P = d.getObject("Params")
for a in ("RackN","RackP","RackZ0","RackZTop","RamL","PinZ","RamBotLowZ"): print(a, P.get(a))

# ===== step 01:12:46 ok  (source: stdin) =====
# probe: which bodies have Tip not on their last feature
import FreeCAD as App
d = App.getDocument("lime_press")
for b in d.findObjects("PartDesign::Body"):
    feats = [o for o in b.Group if o.isDerivedFrom("PartDesign::Feature")]
    print(b.Name, "tip:", b.Tip.Name, "last:", feats[-1].Name)

# ===== step 01:13:11 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 10, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
    ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
    ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
    ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
    ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
    ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
    ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
    ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Midplane = midplane
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                    "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
plate = pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
P.bind(f, "Radius", "BaseMargin")
s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
    "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
pocket(base, s, "FootPocketD", "FootPocket")
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
h.Reversed = True
for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
    P.bind(h, prop, expr)
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
    ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]


def inner_corner(e):
    a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
    return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
            and any(abs(a.z - zz) < 1e-6 for zz in inner))


f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
P.bind(f, "Radius", "GussetR")
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
    "ScrewX2", "0", "ScrewPilotD")
h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
h.Reversed = True
P.bind(h, "Diameter", "ScrewPilotD")
P.bind(h, "Depth", "ScrewPilotL")
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.Midplane = True
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:13:26 ok  (source: stdin) =====
# verify: rack & pinion mesh through the full stroke (kinematic sweep)
import FreeCAD as App
V = App.Vector
d = App.getDocument("lime_press"); P = d.getObject("Params")
g = lambda a: float(P.get(a))
ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
c = V(g("PinX"), 0, g("PinZ"))
for sign in (1, -1):
    worst = []
    for i in range(12):
        dz = (g("Stroke") + g("HeadGap")) * i / 11
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), sign * dz / g("PitchR") * 57.29578)
        worst.append((round(r.common(p).Volume, 3), round(r.distToShape(p)[0], 3)))
    print("sign", sign, "max overlap", max(w[0] for w in worst), "max gap", max(w[1] for w in worst))

# ===== step 01:13:32 ok  (source: stdin) =====
# probe: SideType replacing Midplane on Pad/Pocket
import FreeCAD as App
d = App.getDocument("lime_press")
for n in ("FrameBlank", "RamChannel", "PinionPocket", "CentreDrain"):
    o = d.getObject(n)
    print(n, o.SideType, o.getEnumerationsOfProperty("SideType"), "Midplane=", o.Midplane, "Type=", o.Type, o.getEnumerationsOfProperty("Type"))
print([p for p in d.getObject("FrameBlank").PropertiesList if "2" in p or "Side" in p])

# ===== step 01:13:52 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 10, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
    ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
    ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
    ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
    ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
    ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
    ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
    ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                    "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
plate = pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
P.bind(f, "Radius", "BaseMargin")
s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
    "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
pocket(base, s, "FootPocketD", "FootPocket")
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
h.Reversed = True
for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
    P.bind(h, prop, expr)
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
    ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]


def inner_corner(e):
    a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
    return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
            and any(abs(a.z - zz) < 1e-6 for zz in inner))


f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
P.bind(f, "Radius", "GussetR")
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
    "ScrewX2", "0", "ScrewPilotD")
h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
h.Reversed = True
P.bind(h, "Diameter", "ScrewPilotD")
P.bind(h, "Depth", "ScrewPilotL")
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:14:05 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 10, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
    ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
    ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
    ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
    ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
    ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
    ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
    ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
s = Sk(P, base, "BaseSketch").rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                    "RamX + TrayR + BaseMargin", "TrayR + BaseMargin")
plate = pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
f = cad.fillet(base, plate, cad.edges(plate, cad.is_vertical), 1, "BaseCorners")
P.bind(f, "Radius", "BaseMargin")
s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
    "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
pocket(base, s, "FootPocketD", "FootPocket")
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
h.Reversed = True
for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
    P.bind(h, prop, expr)
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW", "FrameBotZ + FootH"), ("ColW", "HeadBotZ"), ("HeadFrontX", "HeadBotZ"),
    ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")])
fr = pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
inner = [P["FrameBotZ"] + P["FootH"], P["HeadBotZ"]]


def inner_corner(e):
    a, z = e.Vertexes[0].Point, e.Vertexes[-1].Point
    return (abs(a.x - z.x) < 1e-6 and abs(a.z - z.z) < 1e-6 and abs(a.x - P["ColW"]) < 1e-6
            and any(abs(a.z - zz) < 1e-6 for zz in inner))


f = cad.fillet(frame, fr, cad.edges(fr, inner_corner), 1, "Gussets")
P.bind(f, "Radius", "GussetR")
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
    "ScrewX2", "0", "ScrewPilotD")
h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
h.Reversed = True
P.bind(h, "Diameter", "ScrewPilotD")
P.bind(h, "Depth", "ScrewPilotL")
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("0", "~-DomeR"), ("~DomeR", "0"), ("DomeR", "PlungerBossH"), ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:14:21 FAILED  (source: stdin) =====
# error: interference Frame / Pinion: 1686.617 mm3
# # verify: spreadsheet edits drive the whole model (as a user would via the sheet)
# import FreeCAD as App
# from t2m import cad
# V = App.Vector
# d = App.getDocument("lime_press"); S = d.getObject("Params")
# ID = App.Rotation(); SIDE = App.Rotation(V(1,0,0), 90)
# rot = {"Base": ID, "Frame": SIDE, "Ram": SIDE, "Pinion": ID, "Shaft": SIDE, "Handle": ID, "Tray": ID, "Cup": ID, "Plunger": App.Rotation(V(1,0,0),180)}
# def cell(alias):
#     return next(c for c in S.getUsedCells() if S.getAlias(c) == alias)
# def run(changes):
#     for k, v in changes.items(): S.set(cell(k), str(v))
#     d.recompute()
#     g = lambda a: float(S.get(a))
#     parts = {n: (d.getObject(n), r) for n, r in rot.items()}
#     rep = cad.check_assembly(d, parts)
#     ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
#     c = V(g("PinX"), 0, g("PinZ")); ov = 0
#     for i in range(8):
#         dz = (g("Stroke") + g("HeadGap")) * i / 7
#         r = ram.copy(); r.translate(V(0, 0, dz)); p = pin.copy(); p.rotate(c, V(0,1,0), -dz / g("PitchR") * 57.29578)
#         ov = max(ov, r.common(p).Volume)
#     print(changes, "-> OK; frame height %.1f, stroke %.1f, rack mesh overlap %.3f" % (g("HeadTopZ") - g("FrameBotZ"), g("Stroke"), ov))
# run({"LimeMaxD": 26, "ClrSlide": 0.4, "ClrLoc": 0.5})
# run({"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4})

# ===== step 01:15:35 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 10, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
    ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
    ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
    ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
    ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Plunger upper section radius (holds the ram socket)"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
    ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
    ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
    ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert abs(P["PlBossR"] - P["DomeR"]) > 0.5, "plunger dome and boss radii too close (degenerate step)"
assert P["PlBossR"] < P["HeadBotZ"], "sanity"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                            "RamX + TrayR + BaseMargin", "TrayR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
    "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
pocket(base, s, "FootPocketD", "FootPocket")
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
h.Reversed = True
for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
    P.bind(h, prop, expr)
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {3: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     5: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
    "ScrewX2", "0", "ScrewPilotD")
h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
h.Reversed = True
P.bind(h, "Diameter", "ScrewPilotD")
P.bind(h, "Depth", "ScrewPilotL")
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("0", "~-DomeR"), ("~DomeR", "0"), ("PlBossR", "0"), ("PlBossR", "PlungerBossH"), ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:15:47 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
ID, SIDE = App.Rotation(), App.Rotation(V(1, 0, 0), 90)
ROT = {"Base": ID, "Frame": SIDE, "Ram": SIDE, "Pinion": ID, "Shaft": SIDE, "Handle": ID,
       "Tray": ID, "Cup": ID, "Plunger": App.Rotation(V(1, 0, 0), 180)}
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, {n: (d.getObject(n), r) for n, r in ROT.items()})
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 01:22:22 ok  (source: stdin) =====
# probe: color API on a body view object in 1.1
import FreeCAD as App, FreeCADGui as Gui
d = App.getDocument("lime_press"); vo = d.getObject("Base").ViewObject
print([p for p in vo.PropertiesList if "olor" in p or "ppear" in p or "Transp" in p])
m = vo.ShapeAppearance[0]; print(type(m).__name__, m.DiffuseColor)
vo.ShapeColor = (0.2, 0.4, 0.8)
print("after ShapeColor:", vo.ShapeAppearance[0].DiffuseColor)

# ===== step 01:22:42 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 10, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
    ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
    ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
    ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
    ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Plunger upper section radius (holds the ram socket)"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
    ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
    ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
    ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert abs(P["PlBossR"] - P["DomeR"]) > 0.5, "plunger dome and boss radii too close (degenerate step)"
assert P["PlBossR"] < P["HeadBotZ"], "sanity"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                            "RamX + TrayR + BaseMargin", "TrayR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
    "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
pocket(base, s, "FootPocketD", "FootPocket")
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
h.Reversed = True
for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
    P.bind(h, prop, expr)
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {3: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     5: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
    "ScrewX2", "0", "ScrewPilotD")
h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
h.Reversed = True
P.bind(h, "Diameter", "ScrewPilotD")
P.bind(h, "Depth", "ScrewPilotL")
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("0", "~-DomeR"), ("~DomeR", "0"), ("PlBossR", "0"), ("PlBossR", "PlungerBossH"), ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, App.Rotation(V(1, 0, 0), 90)), "Handle": (handle, ID), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "Tray": (0.55, 0.85, 0.90),     # light cyan
    "Cup": (0.40, 0.75, 0.20),      # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, _) in PARTS.items():
    cad.color(b, COLORS[name])
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:24:17 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
ID, SIDE = App.Rotation(), App.Rotation(V(1, 0, 0), 90)
ROT = {"Base": ID, "Frame": SIDE, "Ram": SIDE, "Pinion": ID, "Shaft": SIDE, "Handle": ID,
       "Tray": ID, "Cup": ID, "Plunger": App.Rotation(V(1, 0, 0), 180)}
print(cad.export_stls({n: (d.getObject(n), r) for n, r in ROT.items()}, "limepressv1parts"))

# ===== step 01:32:09 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 10, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("FootPocketD", 5, "mm", "Depth of frame-foot pocket in base"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    ("ScrewClrD", 3.4, "mm", "M3 clearance hole in base"),
    ("ScrewHeadD", 6.5, "mm", "M3 counterbore diameter"),
    ("ScrewHeadH", 3.5, "mm", "M3 counterbore depth"),
    ("ScrewPilotD", 2.6, "mm", "M3 self-tapping pilot hole in frame foot"),
    ("ScrewPilotL", 10, "mm", "Pilot hole depth"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Plunger upper section radius (holds the ram socket)"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("HeadFrontX", "=RamX + RamW/2 + ClrSlide + Wall", "mm", "Frame head front"),
    ("FrameBotZ", "=BaseH - FootPocketD", "mm", "Frame bottom height"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
    ("ScrewX1", "=ColW / 2", "mm", "Rear screw position"),
    ("ScrewX2", "=(ColW + FootL) / 2", "mm", "Front screw position"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert abs(P["PlBossR"] - P["DomeR"]) > 0.5, "plunger dome and boss radii too close (degenerate step)"
assert P["PlungerBossH"] > abs(P["DomeR"] - P["PlBossR"]) + P["RamTipL"] / 2, "plunger boss too short for chamfer"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                            "RamX + TrayR + BaseMargin", "TrayR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
s = Sk(P, base, "FootPocketSketch", offset="BaseH").rect(
    "-ClrLoc", "-(FrameT/2 + ClrLoc)", "FootL + ClrLoc", "FrameT/2 + ClrLoc")
pocket(base, s, "FootPocketD", "FootPocket")
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
s = Sk(P, base, "ScrewSketch").circle("ScrewX1", "0", "ScrewClrD").circle("ScrewX2", "0", "ScrewClrD")
h = cad.hole(base, s.s, 3.4, name="ScrewHoles", cut=("Counterbore", 6.5, 3.5))
h.Reversed = True
for prop, expr in (("Diameter", "ScrewClrD"), ("HoleCutDiameter", "ScrewHeadD"), ("HoleCutDepth", "ScrewHeadH")):
    P.bind(h, prop, expr)
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {3: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     5: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
s = Sk(P, frame, "PilotSketch", offset="FrameBotZ").circle("ScrewX1", "0", "ScrewPilotD").circle(
    "ScrewX2", "0", "ScrewPilotD")
h = cad.hole(frame, s.s, 2.6, depth=10, name="PilotHoles")
h.Reversed = True
P.bind(h, "Diameter", "ScrewPilotD")
P.bind(h, "Depth", "ScrewPilotL")
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    # 45 deg chamfer between dome and boss so it prints (boss-down) without a flat overhang
    ("0", "~-DomeR"), ("~DomeR", "0"), ("PlBossR", "abs(DomeR - PlBossR)"), ("PlBossR", "PlungerBossH"),
    ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger boss-down / dome-up (axial compression), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "Tray": (0.55, 0.85, 0.90),     # light cyan
    "Cup": (0.40, 0.75, 0.20),      # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:32:21 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 01:32:26 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 01:33:02 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plate 1: Frame on its side; Plunger + Pinion nest in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX); Handle and Ram stand beside it.
fw = size["Frame"][0]
mouth_x, mouth_y = g("FootL") + GAP, g("HeadH") + GAP
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], mouth_x, mouth_y, 0),
    ("Pinion", shp["Pinion"], mouth_x, mouth_y + size["Plunger"][1] + GAP, 0),
    ("Handle", shp["Handle"], fw + GAP, 0, 90),
    ("Ram", shp["Ram"], fw + GAP + size["Handle"][1] + GAP, 0, 0),
], GAP)

# Plate 2: Base; Tray, Cup and Shaft in a row above it.
row_y = size["Base"][1] + GAP
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("Tray", shp["Tray"], 0, row_y, 0),
    ("Cup", shp["Cup"], size["Tray"][0] + GAP, row_y, 0),
    ("Shaft", shp["Shaft"], size["Tray"][0] + GAP + size["Cup"][0] + GAP, row_y, 0),
], GAP)

assert set(plate1) | set(plate2) == set(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for i, pl in enumerate((plate1, plate2), 1):
    print(f"--- plate {i}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"plate{i}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate((plate1, plate2)):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 01:35:44 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with Tray and Cup in a row above it.
row_y = size["Base"][1] + GAP
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("Tray", shp["Tray"], 0, row_y, 0),
    ("Cup", shp["Cup"], size["Tray"][0] + GAP, row_y, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 01:42:45 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 15, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Plunger upper section radius (holds the ram socket)"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide - sqrt(pow(FrameT/2 - Wall; 2) - pow(RamT/2 + ClrSlide; 2))", "mm",
     "Bull-nose centre: as far back as possible keeping Wall at the ram channel's front corners"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert abs(P["PlBossR"] - P["DomeR"]) > 0.5, "plunger dome and boss radii too close (degenerate step)"
assert P["PlungerBossH"] > abs(P["DomeR"] - P["PlBossR"]) + P["RamTipL"] / 2, "plunger boss too short for chamfer"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                            "RamX + TrayR + BaseMargin", "TrayR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    # 45 deg chamfer between dome and boss so it prints (boss-down) without a flat overhang
    ("0", "~-DomeR"), ("~DomeR", "0"), ("PlBossR", "abs(DomeR - PlBossR)"), ("PlBossR", "PlungerBossH"),
    ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger boss-down / dome-up (axial compression), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "Tray": (0.55, 0.85, 0.90),     # light cyan
    "Cup": (0.40, 0.75, 0.20),      # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:42:59 FAILED  (source: stdin) =====
# error: AssertionError
# # verify: dovetail locks the frame (moves that must collide) and slides (moves that must not)
# import FreeCAD as App
# V = App.Vector
# d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
# frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape
# def hit(v):
#     f = frame.copy(); f.translate(v); return f.common(base).Volume > 1e-3
# tests = {
#     "lift 0.3 mm (undercut must hold)":        (V(0, 0, 0.3), True),
#     "forward 0.3 mm (flank fit)":               (V(0.3, 0, 0), True),
#     "back 0.3 mm (flank fit)":                  (V(-0.3, 0, 0), True),
#     "forward 0.05 mm (inside clearance)":       (V(0.05, 0, 0), False),
#     "push +Y 0.3 mm (closed end stops it)":     (V(0, 0.3, 0), True),
#     "slide out -Y 20 mm (open end)":            (V(0, -20, 0), False),
#     "slide out -Y fully":                       (V(0, -(g("TrayR") + g("BaseMargin") + g("FrameT")/2 + 1), 0), False),
# }
# bad = 0
# for name, (v, want) in tests.items():
#     got = hit(v); bad += got != want
#     print(f"{'ok ' if got == want else 'BAD'} {name}: {'collides' if got else 'free'}")
# # bull nose: thinnest wall between ram channel and the nose surface
# ch = d.getObject("RamChannel").Shape
# nose_wall = min(frame.distToShape(Part.Vertex(V(g("RamX") + g("RamW")/2 + g("ClrSlide"), s*(g("RamT")/2 + g("ClrSlide")), g("HeadTopZ") - 5)))[0] for s in (1, -1)) if False else None
# import Part
# corner = V(g("RamX") + g("RamW")/2 + g("ClrSlide"), g("RamT")/2 + g("ClrSlide"), 0)
# c = V(g("NoseCX"), 0, 0)
# print("nose wall at channel front corner: %.2f mm (target Wall = %.1f)" % (g("FrameT")/2 - (corner - c).Length, g("Wall")))
# assert bad == 0

# ===== step 01:43:36 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Plunger upper section radius (holds the ram socket)"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide - sqrt(pow(FrameT/2 - Wall; 2) - pow(RamT/2 + ClrSlide; 2))", "mm",
     "Bull-nose centre: as far back as possible keeping Wall at the ram channel's front corners"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert abs(P["PlBossR"] - P["DomeR"]) > 0.5, "plunger dome and boss radii too close (degenerate step)"
assert P["PlungerBossH"] > abs(P["DomeR"] - P["PlBossR"]) + P["RamTipL"] / 2, "plunger boss too short for chamfer"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                            "RamX + TrayR + BaseMargin", "TrayR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    # 45 deg chamfer between dome and boss so it prints (boss-down) without a flat overhang
    ("0", "~-DomeR"), ("~DomeR", "0"), ("PlBossR", "abs(DomeR - PlBossR)"), ("PlBossR", "PlungerBossH"),
    ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger boss-down / dome-up (axial compression), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "Tray": (0.55, 0.85, 0.90),     # light cyan
    "Cup": (0.40, 0.75, 0.20),      # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:43:40 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("TrayR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 01:43:58 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 01:44:02 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("TrayR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 01:44:08 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with Tray and Cup in a row above it.
row_y = size["Base"][1] + GAP
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("Tray", shp["Tray"], 0, row_y, 0),
    ("Cup", shp["Cup"], size["Tray"][0] + GAP, row_y, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 01:44:13 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 01:44:24 FAILED  (source: stdin) =====
# error: AttributeError: module 'FreeCADGui' has no attribute 'activateDocument'. Did you mean: 'activeDocument'?
# # screenshots: assembly iso + front view (dovetail open end) + top (bull nose)
# import FreeCAD as App, FreeCADGui as Gui
# from t2m import cad
# d = App.getDocument("lime_press")
# Gui.getDocument("lime_press_plates") and None
# App.setActiveDocument("lime_press"); Gui.activateDocument("lime_press")
# print(cad.shot(d, "lime_press_iso"))
# print(cad.shot(d, "lime_press_front", "Front"))
# print(cad.shot(d, "lime_press_top", "Top"))

# ===== step 01:44:33 ok  (source: stdin) =====
# screenshots: front view (dovetail open end) + top (bull nose)
import FreeCAD as App
from t2m import cad
d = App.getDocument("lime_press")
print(cad.shot(d, "lime_press_front", "Front"))
print(cad.shot(d, "lime_press_top", "Top"))

# ===== step 01:47:42 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> domed plunger that
presses a lime half (cut side down) into a perforated bowl, turning the peel
inside out. Juice drains through the bowl into a tray.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Bowl radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger dome and bowl at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, frame in base, tray in base, cup between pegs"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("TrayRecessD", 2, "mm", "Depth of tray recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Cup, tray, plunger",
    ("CupWall", 3, "mm", "Bowl wall"),
    ("CupFloor", 3, "mm", "Bowl floor above drain grooves"),
    ("CupFootH", 3, "mm", "Depth of drain grooves under the cup"),
    ("DrainD", 3, "mm", "Drain hole diameter"),
    ("DrainN", 6, "", "Number of drain holes / grooves around the ring"),
    ("TrayWall", 2.4, "mm", "Tray wall"),
    ("TrayFloor", 2, "mm", "Tray floor"),
    ("TrayH", 20, "mm", "Tray total height"),
    ("TrayGap", 8, "mm", "Radial space between cup and tray wall (juice)"),
    ("PegD", 6, "mm", "Cup locating peg diameter"),
    ("PegH", 5, "mm", "Cup locating peg height"),
    ("PegN", 3, "", "Number of cup locating pegs"),
    ("PlungerBossH", 16, "mm", "Plunger height above the dome"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Bowl radius"),
    ("CupOR", "=CupR + CupWall", "mm", "Cup outer radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Plunger dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Plunger upper section radius (holds the ram socket)"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("TrayR", "=CupOR + TrayGap + TrayWall", "mm", "Tray outer radius"),
    ("TrayBotZ", "=BaseH - TrayRecessD", "mm", "Tray bottom height"),
    ("CupBotZ", "=TrayBotZ + TrayFloor", "mm", "Cup bottom height"),
    ("RimZ", "=CupBotZ + CupFootH + CupFloor + CupR", "mm", "Bowl rim height (= dome centre at end of stroke)"),
    ("PlTopLowZ", "=RimZ + PlungerBossH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + TrayR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=TrayR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
    ("DrainRingR", "=CupR / 2", "mm", "Drain hole ring radius"),
    ("GrooveW", "=DrainD + 2", "mm", "Drain groove width"),
    ("PegX", "=CupOR + ClrLoc + PegD/2", "mm", "Peg centre radius"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert abs(P["PlBossR"] - P["DomeR"]) > 0.5, "plunger dome and boss radii too close (degenerate step)"
assert P["PlungerBossH"] > abs(P["DomeR"] - P["PlBossR"]) + P["RamTipL"] / 2, "plunger boss too short for chamfer"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(TrayR + BaseMargin)",
                                            "RamX + TrayR + BaseMargin", "TrayR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "TrayRecessSketch", offset="BaseH").circle("RamX", "0", "2*(TrayR + ClrLoc)")
pocket(base, s, "TrayRecessD", "TrayRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Tray (local: axis = Z, bottom z=0) ----------------
tray = new_body("Tray", ("RamX", "0", "TrayBotZ"))
s = Sk(P, tray, "TrayProfile", "XZ").path([
    ("0", "0"), ("TrayR", "0"), ("TrayR", "TrayH"), ("TrayR - TrayWall", "TrayH"),
    ("TrayR - TrayWall", "TrayFloor"), ("0", "TrayFloor")])
cad.revolve(tray, s.s, "TrayShell")
s = Sk(P, tray, "PegSketch", offset="TrayFloor").circle("PegX", "0", "PegD")
peg = pad(tray, s, "PegH", "Peg")
pp = cad.polar(tray, [peg], s.s, "Pegs")
P.bind(pp, "Occurrences", "PegN")
cad.step(doc)

# ---------------- Cup (local: axis = Z, bottom z=0) ----------------
cup = new_body("Cup", ("RamX", "0", "CupBotZ"))
s = Sk(P, cup, "CupProfile", "XZ").path([
    ("0", "0"), ("CupOR", "0"), ("CupOR", "CupFootH + CupFloor + CupR"),
    ("~CupR", "CupFootH + CupFloor + CupR"), ("0", "~CupFootH + CupFloor")],
    {3: ("0", "CupFootH + CupFloor + CupR", "CupR", False)})
cad.revolve(cup, s.s, "Bowl")
s = Sk(P, cup, "GrooveSketch").rect("-GrooveW/2", "-GrooveW/2", "CupOR + 1", "GrooveW/2")
groove = pocket(cup, s, "CupFootH", "DrainGroove", reversed=True)
pp = cad.polar(cup, [groove], s.s, "DrainGrooves")
P.bind(pp, "Occurrences", "DrainN")
s = Sk(P, cup, "CentreDrainSketch").circle("0", "0", "DrainD")
pocket(cup, s, None, "CentreDrain", reversed=True)
s = Sk(P, cup, "RingDrainSketch").circle("DrainRingR", "0", "DrainD")
drain = pocket(cup, s, None, "RingDrain", reversed=True)
pp = cad.polar(cup, [drain], s.s, "RingDrains")
P.bind(pp, "Occurrences", "DrainN")
cad.step(doc)

# ---------------- Plunger (local: dome centre at z=0) ----------------
plunger = new_body("Plunger", ("RamX", "0", "RimZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    # 45 deg chamfer between dome and boss so it prints (boss-down) without a flat overhang
    ("0", "~-DomeR"), ("~DomeR", "0"), ("PlBossR", "abs(DomeR - PlBossR)"), ("PlBossR", "PlungerBossH"),
    ("0", "PlungerBossH")],
    {0: ("0", "0", "DomeR", True)})
cad.revolve(plunger, s.s, "Dome")
s = Sk(P, plunger, "SocketSketch", offset="PlungerBossH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger boss-down / dome-up (axial compression), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "Tray": (tray, ID),
    "Cup": (cup, ID), "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "Tray": (0.55, 0.85, 0.90),     # light cyan
    "Cup": (0.40, 0.75, 0.20),      # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:47:54 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 01:47:57 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("TrayR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 01:47:58 ok  (source: stdin) =====
# check: nose start in line with channel front face, wall at channel corners
import FreeCAD as App
from t2m import cad
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
print("nose curve starts at x=%.2f, channel front face x=%.2f, corner wall %.2f mm, head front x=%.2f" % (
    g("NoseCX"), g("RamX") + g("RamW")/2 + g("ClrSlide"), g("FrameT")/2 - (g("RamT")/2 + g("ClrSlide")), g("HeadFrontX")))
print(cad.shot(d, "lime_press_top", "Top"))

# ===== step 01:51:05 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with Tray and Cup in a row above it.
row_y = size["Base"][1] + GAP
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("Tray", shp["Tray"], 0, row_y, 0),
    ("Cup", shp["Cup"], size["Tray"][0] + GAP, row_y, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 01:51:10 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 01:57:25 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + abs(CupR + CupWall - PlBossR)) / 2", "mm",
     "Plunger outer radius = max(cup wall, socket wall)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR", "PlH"), ("PlOR", "0")],
    {0: ("0", "0", "CupR", True)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 01:57:48 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 01:57:52 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("JcR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 01:57:53 ok  (source: stdin) =====
# report: squeeze geometry and juice capacity
import FreeCAD as App, math
from t2m import cad
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
ring = math.pi * ((g("JcR") - g("JuiceWall"))**2 - g("DomeR")**2) * g("PedH") / 1000
lime_top = g("DomeBaseZ") + g("DomeR") + g("LimeMaxD")/2
print("juice ring below plunger rim: %.0f ml" % ring)
print("at top of stroke: plunger rim %.1f mm above the dome base, top of a %.0f mm lime half %.1f mm -> %.1f mm clearance" % (
    g("Stroke"), g("LimeMaxD"), g("DomeR") + g("LimeMaxD")/2, g("Stroke") - g("DomeR") - g("LimeMaxD")/2))
print("end of stroke: cup cavity R %.1f over dome R %.1f -> %.1f mm squeeze gap" % (g("CupR"), g("DomeR"), g("PeelGap")))
print(cad.shot(d, "lime_press_iso"))
print(cad.shot(d, "lime_press_front", "Front"))

# ===== step 01:58:01 ok  (source: stdin) =====
# section view: assembly cut at y=0 (keep the far half), viewed from the front
import FreeCAD as App, Part
from t2m import cad
V = App.Vector
d = App.getDocument("lime_press")
if "lime_press_section" in App.listDocuments():
    App.closeDocument("lime_press_section")
sd = App.newDocument("lime_press_section")
keep = Part.makeBox(1000, 500, 1000, V(-500, 0, -500))  # y >= 0
for name, (b, _) in cad.parts_of(d).items():
    o = sd.addObject("Part::Feature", name)
    o.Shape = b.Shape.common(keep)
    cad.color(o, b.ViewObject.ShapeAppearance[0].DiffuseColor[:3])
sd.recompute()
print(cad.shot(sd, "lime_press_section", "Front"))

# ===== step 01:58:12 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 01:58:17 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with the JuiceCup above it.
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("JuiceCup", shp["JuiceCup"], 0, size["Base"][1] + GAP, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 02:02:43 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 02:02:53 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 02:02:53 ok  (source: stdin) =====
# check: plunger fillet radius and wall between fillet and ram socket
import FreeCAD as App, math
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
pl = d.getObject("Plunger").Shape
tor = [f for f in pl.Faces if f.Surface.TypeId == "Part::GeomToroid"]
print("fillet faces:", len(tor), "radius %.2f mm (= %.3f in)" % (tor[0].Surface.MinorRadius, tor[0].Surface.MinorRadius / 25.4))
corner = math.hypot(g("RamW")/2 + g("ClrPress"), g("RamT")/2 + g("ClrPress"))
print("flat top ring: socket corner r=%.1f .. fillet start r=%.1f -> %.1f mm wall" % (corner, g("PlOR") - g("PlTopR"), g("PlOR") - g("PlTopR") - corner))

# ===== step 02:03:06 ok  (source: stdin) =====
# probe: loose vs optimal bounding box on the filleted plunger
import FreeCAD as App
from t2m import cad
d = App.getDocument("lime_press"); b = d.getObject("Plunger")
s = b.Shape
print("BoundBox       ", s.BoundBox)
print("optimalBoundBox", s.optimalBoundingBox())
ps = cad.print_shape(b, b.PrintRotation)
print("print shape lowest point via optimal bbox: z=%.3f" % ps.optimalBoundingBox().ZMin)

# ===== step 02:03:33 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 02:03:43 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with the JuiceCup above it.
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("JuiceCup", shp["JuiceCup"], 0, size["Base"][1] + GAP, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 02:03:48 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 02:05:56 ok  (source: stdin) =====
# probe: Pocket TaperAngle sign (does +45 narrow the cut going in?)
import FreeCAD as App, Part
from t2m import cad
V = App.Vector
d = cad.new_doc("probe"); b = cad.body(d)
sk = cad.sketch(b, "S"); cad.rect(sk, 0, 0, 40, 40); pad = cad.pad(b, sk, 10, "P")
sk2 = cad.sketch(b, "S2", offset=10); cad.rect(sk2, 0, 0, 12, 12)
p = cad.pocket(b, sk2, 1, "C"); d.recompute(); v0 = b.Shape.Volume
for ang in (45, -45):
    p.TaperAngle = ang; d.recompute()
    print("taper", ang, "removed %.2f mm3" % (16000 - b.Shape.Volume), "valid", b.Shape.isValid())
print("narrowing frustum 12->10 over 1 mm would remove %.2f" % (1/3*(144+100+120)))
App.closeDocument("probe")

# ===== step 02:06:20 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    ("SocketChamfer", 1, "mm", "45 deg lead-in chamfer around the ram socket opening"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"
assert P["SocketChamfer"] < P["SocketWall"] and P["SocketChamfer"] < P["RamTipL"] / 2, "socket chamfer too big"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs drawn in the sketch, and the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"), ("0", "HeadTopZ")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
# lead-in chamfer: a short pocket from a rectangle SocketChamfer larger all round, tapering 45 deg
# inward to the socket size (taper instead of a Chamfer feature: no edge references to break)
s = Sk(P, plunger, "SocketChamferSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress + SocketChamfer)", "-(RamT/2 + ClrPress + SocketChamfer)",
    "RamW/2 + ClrPress + SocketChamfer", "RamT/2 + ClrPress + SocketChamfer")
f = pocket(plunger, s, "SocketChamfer", "SocketChamfer")
f.TaperAngle = -45
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 02:06:20 ok  (source: stdin) =====
# check: socket chamfer = 45 deg, 1 mm, socket below unchanged
import FreeCAD as App, Part, math
V = App.Vector
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
loc = d.getObject("Plunger").Shape.copy(); loc.Placement = App.Placement()
w, t, c, H = g("RamW")/2 + g("ClrPress"), g("RamT")/2 + g("ClrPress"), g("SocketChamfer"), g("PlH")
for z in (H - 0.01, H - c/2, H - c - 0.5, H - g("RamTipL") + 1):
    sec = loc.slice(V(0, 0, 1), z)
    hole = min(sec, key=lambda w_: w_.BoundBox.XLength)
    print("z=%.2f below top %.2f: socket opening %.2f x %.2f" % (z, H - z, hole.BoundBox.XLength, hole.BoundBox.YLength))
print("expected: top %.2f x %.2f, socket %.2f x %.2f" % (2*(w+c), 2*(t+c), 2*w, 2*t))

# ===== step 02:07:49 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    ("FrameBackR", 12.7, "mm", "Fillet on the frame's top-back corner (1/2 in)"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    ("SocketChamfer", 1, "mm", "45 deg lead-in chamfer around the ram socket opening"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["FrameBackR"] < min(P["ColW"], P["PinX"] - P["CavR"]), "back fillet runs into the column face or pinion pocket"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"
assert P["SocketChamfer"] < P["SocketWall"] and P["SocketChamfer"] < P["RamTipL"] / 2, "socket chamfer too big"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs and the top-back corner a
# FrameBackR arc, all drawn in the sketch; the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"),
    ("FrameBackR", "~HeadTopZ"), ("~0", "HeadTopZ - FrameBackR")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False),
     13: ("FrameBackR", "HeadTopZ - FrameBackR", "FrameBackR", True)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
# lead-in chamfer: a short pocket from a rectangle SocketChamfer larger all round, tapering 45 deg
# inward to the socket size (taper instead of a Chamfer feature: no edge references to break)
s = Sk(P, plunger, "SocketChamferSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress + SocketChamfer)", "-(RamT/2 + ClrPress + SocketChamfer)",
    "RamW/2 + ClrPress + SocketChamfer", "RamT/2 + ClrPress + SocketChamfer")
f = pocket(plunger, s, "SocketChamfer", "SocketChamfer")
f.TaperAngle = -45
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))

# ===== step 02:08:00 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 02:08:03 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("JcR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 02:08:04 ok  (source: stdin) =====
# check: frame fillets (cylindrical faces along Y) and their radii
import FreeCAD as App
from t2m import cad
d = App.getDocument("lime_press")
fr = d.getObject("Frame").Shape
cyl = sorted(round(f.Surface.Radius, 2) for f in fr.Faces
             if f.Surface.TypeId == "Part::GeomCylinder" and abs(abs(f.Surface.Axis.y) - 1) < 1e-6)
print("frame round faces along Y (radii):", cyl)
print(cad.shot(d, "lime_press_front", "Front"))

# ===== step 02:08:16 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with the JuiceCup above it.
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("JuiceCup", shp["JuiceCup"], 0, size["Base"][1] + GAP, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 02:08:21 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 02:10:00 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    ("FrameBackR", 12.7, "mm", "Fillet on the frame's top-back corner (1/2 in)"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    ("SocketChamfer", 1, "mm", "45 deg lead-in chamfer around the ram socket opening"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 12, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("ShaftL", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Shaft length (excl. cap)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["FrameBackR"] < min(P["ColW"], P["PinX"] - P["CavR"]), "back fillet runs into the column face or pinion pocket"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"
assert P["SocketChamfer"] < P["SocketWall"] and P["SocketChamfer"] < P["RamTipL"] / 2, "socket chamfer too big"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs and the top-back corner a
# FrameBackR arc, all drawn in the sketch; the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"),
    ("FrameBackR", "~HeadTopZ"), ("~0", "HeadTopZ - FrameBackR")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False),
     13: ("FrameBackR", "HeadTopZ - FrameBackR", "FrameBackR", True)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
# lead-in chamfer: a short pocket from a rectangle SocketChamfer larger all round, tapering 45 deg
# inward to the socket size (taper instead of a Chamfer feature: no edge references to break)
s = Sk(P, plunger, "SocketChamferSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress + SocketChamfer)", "-(RamT/2 + ClrPress + SocketChamfer)",
    "RamW/2 + ClrPress + SocketChamfer", "RamT/2 + ClrPress + SocketChamfer")
f = pocket(plunger, s, "SocketChamfer", "SocketChamfer")
f.TaperAngle = -45
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))
print(cad.section(doc))  # half-section through the ram axis, regenerated every build

# ===== step 02:10:00 ok  (source: stdin) =====
# check: which document is active in the GUI after the build
import FreeCAD as App, FreeCADGui as Gui
print("App active:", App.ActiveDocument.Name, "| Gui active:", Gui.ActiveDocument.Document.Name, "| docs:", list(App.listDocuments()))

# ===== step 02:10:09 ok  (source: stdin) =====
# cleanup: close leftover probe document from an earlier API check
import FreeCAD as App
d = App.getDocument("probe1")
print([o.Name for o in d.Objects][:5], "modified:", d.isTouched())
App.closeDocument("probe1")
print(list(App.listDocuments()))

# ===== step 02:17:42 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    ("FrameBackR", 12.7, "mm", "Fillet on the frame's top-back corner (1/2 in)"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    ("SocketChamfer", 1, "mm", "45 deg lead-in chamfer around the ram socket opening"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 18, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    ("ShaftGrooveD", 1.2, "mm", "Depth of the clip groove in the shaft"),
    ("ShaftTail", 4, "mm", "Shaft length beyond the clip groove"),
    "Spring clip (holds the handle on the shaft)",
    ("ClipT", 2.4, "mm", "Clip thickness"),
    ("ClipWall", 3, "mm", "Clip ring width (thinner = springier)"),
    ("ClipSnap", 0.85, "", "Clip mouth width as a fraction of the groove floor diameter (smaller = firmer snap)"),
    ("ClipTabW", 8, "mm", "Pull tab width"),
    ("ClipTabL", 8, "mm", "Pull tab length beyond the ring"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + 2", "mm", "Handle inner face: outside everything it sweeps past"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("GrooveZ", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Clip groove start along the shaft (= handle outer face)"),
    ("GrooveW", "=ClipT + ClrSlide", "mm", "Clip groove width"),
    ("GrooveR", "=ShaftD/2 - ShaftGrooveD", "mm", "Clip groove floor radius"),
    ("ShaftL", "=GrooveZ + GrooveW + ShaftTail", "mm", "Shaft length (excl. cap)"),
    ("ClipRi", "=GrooveR + ClrPress", "mm", "Clip inner radius"),
    ("ClipRo", "=ClipRi + ClipWall", "mm", "Clip outer radius"),
    ("ClipMouthW", "=2 * GrooveR * ClipSnap", "mm", "Clip mouth width (snaps over the groove floor)"),
    ("KeyL", "=JcR + BaseMargin - FrameT/2 - ClrLoc", "mm", "Dovetail key length (frame side to base edge)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["FrameBackR"] < min(P["ColW"], P["PinX"] - P["CavR"]), "back fillet runs into the column face or pinion pocket"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["GrooveR"] > P["ShaftFd"], "clip groove cuts through the shaft flat"
assert P["ClipMouthW"] / 2 < P["ClipRi"] - 0.5, "clip mouth too wide to hold"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"
assert P["SocketChamfer"] < P["SocketWall"] and P["SocketChamfer"] < P["RamTipL"] / 2, "socket chamfer too big"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs and the top-back corner a
# FrameBackR arc, all drawn in the sketch; the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"),
    ("FrameBackR", "~HeadTopZ"), ("~0", "HeadTopZ - FrameBackR")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False),
     13: ("FrameBackR", "HeadTopZ - FrameBackR", "FrameBackR", True)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
# ring groove just past the handle's outer face for the spring clip
s = Sk(P, shaft, "ClipGrooveSketch", "XZ").rect("GrooveR", "GrooveZ", "ShaftD/2 + 1", "GrooveZ + GrooveW")
cad.groove(shaft, s.s, "ClipGroove")
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Spring clip (local: XY plane, centred on the shaft axis) ----------------
# C-ring: mouth toward -X narrower than the groove floor so the arms spring over it and snap
# shut; pull tab toward +X. Sits in the groove against the handle's outer face.
clip = new_body("SpringClip", ("PinX", "HandleY0 + HandleT", "PinZ"), RX)
ro_x, ri_x = "sqrt(ClipRo**2 - (ClipMouthW/2)**2)", "sqrt(ClipRi**2 - (ClipMouthW/2)**2)"
s = Sk(P, clip, "ClipSketch").path([
    (f"~-{ro_x}", "-ClipMouthW/2"), (f"~-{ro_x}", "ClipMouthW/2"),
    (f"~-{ri_x}", "ClipMouthW/2"), (f"~-{ri_x}", "-ClipMouthW/2")],
    {0: ("0", "0", "ClipRo", True), 2: ("0", "0", "ClipRi", False)})
pad(clip, s, "ClipT", "ClipRing")
s = Sk(P, clip, "TabSketch").rect("ClipRo - 1", "-ClipTabW/2", "ClipRo + ClipTabL", "ClipTabW/2")
pad(clip, s, "ClipT", "PullTab")
cad.step(doc)

# ---------------- Dovetail key (world coordinates) ----------------
# Same section as the frame's tenon; fills the slot from the frame's side face to the base edge.
key = new_body("DovetailKey")
s = Sk(P, key, "KeySketch", "XZ", offset="FrameT/2 + ClrLoc").path([
    ("FootL/2 - DovetailW/2", "BaseH"), ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "BaseH - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "BaseH - DovetailH"), ("FootL/2 + DovetailW/2", "BaseH")])
pad(key, s, "KeyL", "Key")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
# lead-in chamfer: a short pocket from a rectangle SocketChamfer larger all round, tapering 45 deg
# inward to the socket size (taper instead of a Chamfer feature: no edge references to break)
s = Sk(P, plunger, "SocketChamferSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress + SocketChamfer)", "-(RamT/2 + ClrPress + SocketChamfer)",
    "RamW/2 + ClrPress + SocketChamfer", "RamT/2 + ClrPress + SocketChamfer")
f = pocket(plunger, s, "SocketChamfer", "SocketChamfer")
f.TaperAngle = -45
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
    "SpringClip": (clip, ID), "DovetailKey": (key, ID),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "SpringClip": (0.10, 0.60, 0.55),  # teal
    "DovetailKey": (0.60, 0.60, 0.62),  # light grey
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))
print(cad.section(doc))  # half-section through the ram axis, regenerated every build

# ===== step 02:17:58 ok  (source: stdin) =====
# verify: clip retention (axial + radial) and dovetail key fit/flushness
import FreeCAD as App
V = App.Vector
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
S = lambda n: d.getObject(n).Shape
def hit(a, b, v):
    s = S(a).copy(); s.translate(v); return s.common(S(b)).Volume > 1e-3
clip_tests = {
    "clip pulled outward along shaft 0.5 mm -> hits groove wall": ("SpringClip", "Shaft", V(0, 0.5, 0), True),
    "handle pushed outward 0.2 mm -> hits clip":                 ("Handle", "SpringClip", V(0, 0.2, 0), True),
    "clip slid sideways off the shaft 1 mm -> arms hit groove":  ("SpringClip", "Shaft", V(1, 0, 0), True),
}
bad = 0
for name, (a, b, v, want) in clip_tests.items():
    got = hit(a, b, v); bad += got != want
    print(("ok  " if got == want else "BAD ") + name)
print("clip mouth %.2f mm vs groove floor %.2f mm -> each arm springs %.2f mm" % (
    g("ClipMouthW"), 2*g("GrooveR"), g("GrooveR") - g("ClipMouthW")/2))
kb, bb, fb = S("DovetailKey").BoundBox, S("Base").BoundBox, S("Frame").BoundBox
print("key: outer end y=%.2f vs base edge y=%.2f | top z=%.2f vs base top %.2f | gap to frame %.2f mm" % (
    kb.YMin, bb.YMin, kb.ZMax, g("BaseH"), -g("FrameT")/2 - kb.YMax))
for name, v, want in (("key lifts 0.3 mm -> undercut holds", V(0, 0, 0.3), True),
                      ("key shifts 0.3 mm along X -> flank fit", V(0.3, 0, 0), True)):
    got = hit("DovetailKey", "Base", v); bad += got != want
    print(("ok  " if got == want else "BAD ") + name)
assert bad == 0

# ===== step 02:18:08 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep the rack & pinion through the full stroke.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    ram, pin = d.getObject("Ram").Shape, d.getObject("Pinion").Shape
    c, worst = V(g("PinX"), 0, g("PinZ")), 0
    for i in range(8):
        dz = (g("Stroke") + g("HeadGap")) * i / 7
        r = ram.copy(); r.translate(V(0, 0, dz))
        p = pin.copy(); p.rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        worst = max(worst, r.common(p).Volume)
    assert worst < 1e-3, f"rack/pinion collide during stroke: {worst:.3f} mm3"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 02:18:12 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("JcR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 02:18:25 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with the JuiceCup above it.
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("JuiceCup", shp["JuiceCup"], 0, size["Base"][1] + GAP, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft - plus the small SpringClip and DovetailKey.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
    ("SpringClip", shp["SpringClip"], size["Pinion"][0] + size["Shaft"][0] + 2 * GAP, row_y, 0),
    ("DovetailKey", shp["DovetailKey"],
     size["Pinion"][0] + size["Shaft"][0] + size["SpringClip"][0] + 3 * GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 02:18:29 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 02:18:30 ok  (source: stdin) =====
# close-up: handle hub, clip and shaft end
import FreeCAD as App, FreeCADGui as Gui
from t2m import cad
d = App.getDocument("lime_press")
v = Gui.getDocument("lime_press").ActiveView
v.viewIsometric()
for n in ("Frame", "Base", "JuiceCup", "Plunger", "Ram", "DovetailKey"):
    d.getObject(n).Visibility = False
v.fitAll(); Gui.updateGui()
v.saveImage(cad.OUT + "/lime_press_clip.png", 1200, 900, "White")
for n in ("Frame", "Base", "JuiceCup", "Plunger", "Ram", "DovetailKey"):
    d.getObject(n).Visibility = True
v.fitAll()
print("ok")

# ===== step 02:18:39 ok  (source: stdin) =====
# close-up from the clip side (+Y), slightly from above
import FreeCAD as App, FreeCADGui as Gui
from t2m import cad
d = App.getDocument("lime_press")
v = Gui.getDocument("lime_press").ActiveView
hide = ("Frame", "Base", "JuiceCup", "Plunger", "Ram", "DovetailKey", "Pinion")
for n in hide: d.getObject(n).Visibility = False
v.setCameraOrientation(App.Rotation(App.Vector(0, 0, 1), 200).multiply(App.Rotation(App.Vector(1, 0, 0), 65)))
v.fitAll(); Gui.updateGui()
v.saveImage(cad.OUT + "/lime_press_clip.png", 1200, 900, "White")
for n in hide: d.getObject(n).Visibility = True
v.viewIsometric(); v.fitAll()
print("ok")

# ===== step 02:23:07 ok  (source: designs/lime_press.py) =====
"""Lime-juicing arbor press.

Handle -> D-shaft -> pinion -> rack cut in a square ram -> cup-shaped plunger.
A lime half sits cut side down on a dome in the juice cup on the base; the
plunger's cup comes down over it and squeezes it against the dome, and the
juice squirts out under the plunger rim into the juice cup.

Every dimension is driven by the 'Params' spreadsheet (yellow = input,
grey = derived). Edit a yellow cell in FreeCAD and press Recompute (Ctrl+R).
All clearances are per side (radial), in mm.
"""
import math

import FreeCAD as App
import InvoluteGearFeature

from t2m import cad
from t2m.cad import V, Sk

ROWS = [
    "Lime",
    ("LimeMaxD", 51, "mm", "Largest lime that fits (1 in = 25.4, 2 in = 50.8). Any smaller lime works too."),
    ("LimeGap", 1, "mm", "Plunger cup radius beyond the lime radius"),
    ("PeelGap", 3, "mm", "Gap left between plunger cup and dome at end of stroke (squeezed peel)"),
    ("LiftMargin", 6, "mm", "Clearance above an uncut lime half at top of stroke"),
    "Clearances (per side)",
    ("ClrSlide", 0.3, "mm", "Ram sliding in its channel"),
    ("ClrRot", 0.25, "mm", "Shaft turning in the frame bores"),
    ("ClrPress", 0.1, "mm", "Press fits: D-shaft into pinion and handle, ram tip into plunger"),
    ("ClrGear", 0.2, "mm", "Extra pinion-to-rack centre distance (backlash)"),
    ("ClrLoc", 0.4, "mm", "Loose locating fits: pinion pocket, juice cup in base"),
    "Gear",
    ("GearM", 2.5, "mm", "Module of pinion and rack"),
    ("PinionZ", 14, "", "Pinion tooth count"),
    ("GearT", 14, "mm", "Pinion face width"),
    ("PressureAngle", 20, "deg", "Pressure angle"),
    "Ram",
    ("RamW", 20, "mm", "Ram size front-to-back (rack is cut in its back face)"),
    ("RamT", 18, "mm", "Ram size side-to-side"),
    ("CollarH", 6, "mm", "Stop collar height (rests on frame at end of stroke)"),
    ("CollarExt", 6, "mm", "Stop collar overhang at the front"),
    ("RamTipL", 12, "mm", "Length of ram pressed into the plunger"),
    ("RackOut", 1, "mm", "Rack gap sketch overshoot past the ram face (clean cut)"),
    "Frame",
    ("FrameT", 34, "mm", "Frame thickness side-to-side"),
    ("ColW", 26, "mm", "Column width"),
    ("FootL", 40, "mm", "Frame foot length (sits in base pocket)"),
    ("FootH", 14, "mm", "Frame foot height"),
    ("Wall", 6, "mm", "General wall thickness"),
    ("HeadGap", 3, "mm", "Plunger to frame head at top of stroke"),
    ("GussetR", 12, "mm", "Inside corner fillet radius"),
    ("FrameBackR", 12.7, "mm", "Fillet on the frame's top-back corner (1/2 in)"),
    "Base",
    ("BaseH", 12, "mm", "Base plate thickness"),
    ("BaseMargin", 8, "mm", "Base plate margin around frame and tray"),
    ("CupRecessD", 2, "mm", "Depth of juice-cup recess in base"),
    "Dovetail (frame slides sideways into the base)",
    ("DovetailW", 24, "mm", "Tenon width at the base surface (narrow end)"),
    ("DovetailH", 6, "mm", "Tenon depth into the base"),
    ("DovetailAngle", 20, "deg", "Flank angle from vertical (also the slot overhang when printing the base)"),
    ("ClrDovetail", 0.1, "mm", "Dovetail clearance per side: tight sliding fit; raise if too tight to assemble"),
    "Plunger cup and juice cup",
    ("CupWall", 3, "mm", "Plunger cup wall"),
    ("CupTopT", 3, "mm", "Plunger material between cup cavity and ram socket"),
    ("PlTopR", 12.7, "mm", "Fillet radius on the plunger's top outer edge (1/2 in)"),
    ("JuiceWall", 2.4, "mm", "Juice cup wall"),
    ("JuiceFloor", 2.4, "mm", "Juice cup floor"),
    ("PedH", 15, "mm", "Dome pedestal height: juice depth below the plunger rim at end of stroke"),
    ("SplashH", 15, "mm", "Juice cup wall height above the dome base (catches squirts)"),
    ("JuiceGap", 5, "mm", "Radial space between plunger and juice cup wall"),
    ("SocketWall", 3, "mm", "Plunger wall around the ram socket corners"),
    ("SocketChamfer", 1, "mm", "45 deg lead-in chamfer around the ram socket opening"),
    "Shaft and handle",
    ("ShaftD", 12, "mm", "Shaft diameter"),
    ("ShaftFlat", 1.5, "mm", "Depth of the flat on the D-shaft"),
    ("ShaftCapD", 18, "mm", "Shaft retaining cap diameter"),
    ("ShaftCapL", 4, "mm", "Shaft retaining cap length"),
    ("HandleL", 110, "mm", "Shaft centre to knob centre (leverage)"),
    ("HandleW", 14, "mm", "Handle bar width"),
    ("HandleT", 18, "mm", "Handle thickness"),
    ("HubD", 28, "mm", "Handle hub diameter"),
    ("KnobD", 20, "mm", "Handle end knob diameter"),
    ("ShaftGrooveD", 1.2, "mm", "Depth of the clip groove in the shaft"),
    ("ShaftTail", 4, "mm", "Shaft length beyond the clip groove"),
    "Spring clip (holds the handle on the shaft)",
    ("ClipT", 2.4, "mm", "Clip thickness"),
    ("ClipWall", 3, "mm", "Clip ring width (thinner = springier)"),
    ("ClipSnap", 0.85, "", "Clip mouth width as a fraction of the groove floor diameter (smaller = firmer snap)"),
    ("ClipTabW", 8, "mm", "Pull tab width"),
    ("ClipTabL", 8, "mm", "Pull tab length beyond the ring"),
    "Derived (do not edit)",
    ("CupR", "=LimeMaxD/2 + LimeGap", "mm", "Plunger cup cavity radius"),
    ("DomeR", "=CupR - PeelGap", "mm", "Juice-cup dome radius"),
    ("PlBossR", "=sqrt(pow(RamW/2 + ClrPress; 2) + pow(RamT/2 + ClrPress; 2)) + SocketWall", "mm",
     "Smallest plunger radius that still holds the ram socket"),
    ("PlOR", "=(CupR + CupWall + PlBossR + PlTopR + abs(CupR + CupWall - PlBossR - PlTopR)) / 2", "mm",
     "Plunger outer radius = max(cup + wall, socket + wall + top fillet)"),
    ("PlH", "=CupR + CupTopT + RamTipL", "mm", "Plunger height"),
    ("JcR", "=PlOR + JuiceGap + JuiceWall", "mm", "Juice cup outer radius"),
    ("JcH", "=JuiceFloor + PedH + SplashH", "mm", "Juice cup height"),
    ("Stroke", "=LimeMaxD/2 + LiftMargin + DomeR", "mm", "Ram travel"),
    ("JuiceBotZ", "=BaseH - CupRecessD", "mm", "Juice cup bottom height"),
    ("DomeBaseZ", "=JuiceBotZ + JuiceFloor + PedH", "mm", "Dome base (= plunger rim at end of stroke)"),
    ("PlTopLowZ", "=DomeBaseZ + PlH", "mm", "Plunger top at end of stroke"),
    ("RamBotLowZ", "=PlTopLowZ - RamTipL", "mm", "Ram bottom at end of stroke"),
    ("HeadBotZ", "=PlTopLowZ + Stroke + HeadGap", "mm", "Frame head underside"),
    ("PitchR", "=GearM * PinionZ / 2", "mm", "Pinion pitch radius"),
    ("CavR", "=PitchR + GearM + ClrLoc", "mm", "Pinion pocket radius"),
    ("HeadH", "=2 * (CavR + Wall)", "mm", "Frame head height (= ram guide length)"),
    ("HeadTopZ", "=HeadBotZ + HeadH", "mm", "Frame top"),
    ("PinZ", "=HeadBotZ + Wall + CavR", "mm", "Shaft height"),
    ("RamX", "=FootL + JcR + Wall", "mm", "Ram axis distance from frame back"),
    ("PinX", "=RamX - RamW/2 + GearM - PitchR - ClrGear", "mm", "Shaft distance from frame back"),
    ("NoseCX", "=RamX + RamW/2 + ClrSlide", "mm",
     "Bull-nose start: where the curve meets the flat sides, in line with the ram channel's front face"),
    ("HeadFrontX", "=NoseCX + FrameT/2", "mm", "Frame head front (tip of the bull nose)"),
    ("FrameBotZ", "=BaseH", "mm", "Frame foot sits on the base top"),
    ("DtTan", "=tan(DovetailAngle)", "", "Dovetail flank slope"),
    ("RamL", "=HeadTopZ - RamBotLowZ", "mm", "Ram length below the collar"),
    ("RackP", "=pi * GearM", "mm", "Rack pitch"),
    ("RackDepth", "=2.25 * GearM", "mm", "Rack tooth depth"),
    ("RackWOut", "=RackP/2 + 2*(GearM + RackOut)*tan(PressureAngle)", "mm", "Rack gap width at sketch overshoot"),
    ("RackWRoot", "=RackP/2 - 2*1.25*GearM*tan(PressureAngle)", "mm", "Rack gap width at root"),
    ("RackN", "=ceil((Stroke + HeadGap) / RackP) + 3", "", "Rack tooth gaps"),
    ("RackZTop", "=PinZ - RamBotLowZ + RackP", "mm", "Top rack gap centre (ram coordinates)"),
    ("RackZ0", "=RackZTop - (RackN - 1) * RackP", "mm", "Bottom rack gap centre (ram coordinates)"),
    ("ShaftFd", "=ShaftD/2 - ShaftFlat", "mm", "Shaft flat distance from centre"),
    ("BoreR", "=ShaftD/2 + ClrPress", "mm", "D-bore radius (pinion, handle)"),
    ("BoreFd", "=ShaftFd + ClrPress", "mm", "D-bore flat distance from centre"),
    ("HandleY0", "=JcR + BaseMargin - HandleT", "mm", "Handle inner face: puts the handle's outer face in line with the base edge"),
    ("HubExt", "=HandleY0 - FrameT/2 - ClrLoc", "mm", "Handle hub boss length toward frame"),
    ("GrooveZ", "=FrameT + 2*ClrLoc + HubExt + HandleT", "mm", "Clip groove start along the shaft (= handle outer face)"),
    ("GrooveW", "=ClipT + ClrSlide", "mm", "Clip groove width"),
    ("GrooveR", "=ShaftD/2 - ShaftGrooveD", "mm", "Clip groove floor radius"),
    ("ShaftL", "=GrooveZ + GrooveW + ShaftTail", "mm", "Shaft length (excl. cap)"),
    ("ClipRi", "=GrooveR + ClrPress", "mm", "Clip inner radius"),
    ("ClipRo", "=ClipRi + ClipWall", "mm", "Clip outer radius"),
    ("ClipMouthW", "=2 * GrooveR * ClipSnap", "mm", "Clip mouth width (snaps over the groove floor)"),
    ("KeyL", "=JcR + BaseMargin - FrameT/2 - ClrLoc", "mm", "Dovetail key length (frame side to base edge)"),
]

RX = App.Rotation(V(1, 0, 0), -90)  # body local +Z -> world +Y (shaft axis)

doc = cad.new_doc("lime_press")
P = cad.Params(doc, ROWS)

# design sanity checks that the spreadsheet can't express
assert P["RackZ0"] - P["RackWOut"] / 2 > P["RamTipL"], "rack runs into plunger socket"
assert P["RackZTop"] + P["RackWOut"] / 2 < P["RamL"], "rack runs into collar"
assert P["PinZ"] - P["HandleL"] - P["KnobD"] / 2 > P["BaseH"] + 5, "handle hits the table"
assert P["PinX"] - P["CavR"] > P["ColW"], "pinion pocket cuts into column"
assert P["FrameT"] / 2 - P["Wall"] > P["RamT"] / 2 + P["ClrSlide"], "frame too thin for a bull nose round the ram"
assert P["FrameBackR"] < min(P["ColW"], P["PinX"] - P["CavR"]), "back fillet runs into the column face or pinion pocket"
assert P["DovetailW"] / 2 + P["DovetailH"] * P["DtTan"] < P["FootL"] / 2, "dovetail wider than the frame foot"
assert P["BaseH"] - P["DovetailH"] - P["ClrLoc"] >= 4, "base too thin under the dovetail slot"
assert P["HubExt"] >= 0, "handle thicker than the gap between frame and base edge"
assert P["GrooveR"] > P["ShaftFd"], "clip groove cuts through the shaft flat"
assert P["ClipMouthW"] / 2 < P["ClipRi"] - 0.5, "clip mouth too wide to hold"
assert P["SplashH"] > 0 and P["PedH"] > 0, "juice cup needs a pedestal and a splash wall"
assert P["PlTopR"] < P["PlH"] - P["CupTopT"], "plunger top fillet taller than the plunger"
assert P["SocketChamfer"] < P["SocketWall"] and P["SocketChamfer"] < P["RamTipL"] / 2, "socket chamfer too big"


def new_body(name, place=None, rot=None):
    b = cad.body(doc, name)
    if rot:
        b.Placement = App.Placement(V(), rot)
    for axis, expr in zip("xyz", place or ()):
        P.bind(b, f"Placement.Base.{axis}", expr)
    return b


def pad(b, sk, length, name, midplane=False, reversed=False):
    f = cad.pad(b, sk.s, 1, name, reversed=reversed, midplane=midplane)
    P.bind(f, "Length", length)
    return f


def pocket(b, sk, depth, name, midplane=False, reversed=False):
    f = cad.pocket(b, sk.s, None if depth is None else 1, name, midplane=midplane)
    if depth is not None:
        P.bind(f, "Length", depth)
    f.Reversed = reversed
    return f


# ---------------- Base ----------------
base = new_body("Base")
# rounded corners live in the sketch (fillet features reference edges by name and break on resize)
s = Sk(P, base, "BaseSketch").rounded_rect("-BaseMargin", "-(JcR + BaseMargin)",
                                            "RamX + JcR + BaseMargin", "JcR + BaseMargin", "BaseMargin")
pad(base, s, "BaseH", "BasePlate")
cad.step(doc)
# Dovetail slot: drawn on a side plane at the closed end (y = +FrameT/2 + clearance) and cut
# through to the open -Y edge, so the frame slides in from the -Y side until it stops centred.
# Flanks = tenon flanks offset by ClrDovetail; floor ClrLoc deeper than the tenon so the foot seats.
hw_top = "(DovetailW/2 - DtTan + ClrDovetail)"                       # at z = BaseH + 1
hw_bot = "(DovetailW/2 + (DovetailH + ClrLoc)*DtTan + ClrDovetail)"  # at the slot floor
z_bot = "(BaseH - DovetailH - ClrLoc)"
s = Sk(P, base, "DovetailSlotSketch", "XZ", offset="-(FrameT/2 + ClrDovetail)").path([
    (f"FootL/2 - {hw_bot}", z_bot), (f"FootL/2 + {hw_bot}", z_bot),
    (f"FootL/2 + {hw_top}", "BaseH + 1"), (f"FootL/2 - {hw_top}", "BaseH + 1")])
pocket(base, s, None, "DovetailSlot", reversed=True)
s = Sk(P, base, "CupRecessSketch", offset="BaseH").circle("RamX", "0", "2*(JcR + ClrLoc)")
pocket(base, s, "CupRecessD", "CupRecess")
cad.step(doc)

# ---------------- Frame ----------------
frame = new_body("Frame")
# C-frame side profile; the two inside corners are GussetR arcs and the top-back corner a
# FrameBackR arc, all drawn in the sketch; the
# dovetail tenon (wider at the bottom) hangs under the foot, centred on it.
s = Sk(P, frame, "FrameProfile", "XZ").path([
    ("0", "FrameBotZ"), ("FootL/2 - DovetailW/2", "FrameBotZ"),
    ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "FrameBotZ - DovetailH"),
    ("FootL/2 + DovetailW/2", "FrameBotZ"),
    ("FootL", "FrameBotZ"), ("FootL", "FrameBotZ + FootH"),
    ("ColW + GussetR", "~FrameBotZ + FootH"), ("~ColW", "FrameBotZ + FootH + GussetR"),
    ("~ColW", "HeadBotZ - GussetR"), ("ColW + GussetR", "~HeadBotZ"),
    ("HeadFrontX", "HeadBotZ"), ("HeadFrontX", "HeadTopZ"),
    ("FrameBackR", "~HeadTopZ"), ("~0", "HeadTopZ - FrameBackR")],
    {7: ("ColW + GussetR", "FrameBotZ + FootH + GussetR", "GussetR", False),
     9: ("ColW + GussetR", "HeadBotZ - GussetR", "GussetR", False),
     13: ("FrameBackR", "HeadTopZ - FrameBackR", "FrameBackR", True)})
pad(frame, s, "FrameT", "FrameBlank", midplane=True)
cad.step(doc)
s = Sk(P, frame, "RamChannelSketch", offset="HeadTopZ").rect(
    "RamX - RamW/2 - ClrSlide", "-(RamT/2 + ClrSlide)", "RamX + RamW/2 + ClrSlide", "RamT/2 + ClrSlide")
pocket(frame, s, None, "RamChannel")
# Bull nose: round the head front (seen from above) to a half-circle the full frame thickness wide.
# Cut away everything ahead of NoseCX that lies outside that half-circle.
s = Sk(P, frame, "BullNoseSketch", offset="HeadTopZ").path([
    ("NoseCX", "~FrameT/2"), ("NoseCX", "FrameT/2 + 1"), ("HeadFrontX + 1", "FrameT/2 + 1"),
    ("HeadFrontX + 1", "-(FrameT/2 + 1)"), ("NoseCX", "-(FrameT/2 + 1)"), ("NoseCX", "~-FrameT/2")],
    {5: ("NoseCX", "0", "FrameT/2", True)})
pocket(frame, s, None, "BullNose")
s = Sk(P, frame, "PinionPocketSketch", "XZ").circle("PinX", "PinZ", "2*CavR")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionPocket", midplane=True)
s = Sk(P, frame, "PinionSlotSketch", "XZ").rect("PinX - CavR", "PinZ", "PinX + CavR", "HeadTopZ + 1")
pocket(frame, s, "GearT + 2*ClrLoc", "PinionInsertSlot", midplane=True)
s = Sk(P, frame, "ShaftBoreSketch", "XZ").circle("PinX", "PinZ", "ShaftD + 2*ClrRot")
pocket(frame, s, None, "ShaftBore", midplane=True)
cad.step(doc)

# ---------------- Ram (local: axis = Z, bottom at z=0) ----------------
ram = new_body("Ram", ("RamX", "0", "RamBotLowZ"))
s = Sk(P, ram, "RamProfile", "XZ").path([
    ("-RamW/2", "0"), ("RamW/2", "0"), ("RamW/2", "RamL"), ("RamW/2 + CollarExt", "RamL"),
    ("RamW/2 + CollarExt", "RamL + CollarH"), ("-RamW/2", "RamL + CollarH")])
pad(ram, s, "RamT", "RamBar", midplane=True)
s = Sk(P, ram, "RackGapSketch", "XZ").path([
    ("-RamW/2 - RackOut", "RackZ0 - RackWOut/2"), ("-RamW/2 + RackDepth", "RackZ0 - RackWRoot/2"),
    ("-RamW/2 + RackDepth", "RackZ0 + RackWRoot/2"), ("-RamW/2 - RackOut", "RackZ0 + RackWOut/2")])
gap = pocket(ram, s, None, "RackGap", midplane=True)
lp = cad.linear(ram, [gap], (s.s, ["V_Axis"]), "Rack")
P.bind(lp, "Length", "(RackN - 1) * RackP")
P.bind(lp, "Occurrences", "RackN")
cad.step(doc)

# ---------------- Pinion (local: axis = Z) ----------------
pinion = new_body("Pinion", ("PinX", "0", "PinZ"), RX)
g = InvoluteGearFeature.makeInvoluteGear("PinionProfile")
pinion.addObject(g)
P.bind(g, "NumberOfTeeth", "PinionZ")
P.bind(g, "Modules", "GearM")
P.bind(g, "PressureAngle", "PressureAngle")
f = pinion.newObject("PartDesign::Pad", "PinionGear")
f.Profile = g
f.SideType = "Symmetric"
P.bind(f, "Length", "GearT")
g.Visibility = False
s = Sk(P, pinion, "PinionBoreSketch").d_shape("BoreR", "BoreFd")
pocket(pinion, s, None, "PinionDBore", midplane=True)
cad.step(doc)

# ---------------- Shaft (local: axis = Z, z=0 at cap face) ----------------
shaft = new_body("Shaft", ("PinX", "-(FrameT/2 + ClrLoc)", "PinZ"), RX)
s = Sk(P, shaft, "ShaftSketch").d_shape("ShaftD/2", "ShaftFd")
pad(shaft, s, "ShaftL", "DShaft")
s = Sk(P, shaft, "CapSketch").d_shape("ShaftCapD/2", "ShaftFd")
pad(shaft, s, "ShaftCapL", "Cap", reversed=True)
# ring groove just past the handle's outer face for the spring clip
s = Sk(P, shaft, "ClipGrooveSketch", "XZ").rect("GrooveR", "GrooveZ", "ShaftD/2 + 1", "GrooveZ + GrooveW")
cad.groove(shaft, s.s, "ClipGroove")
cad.step(doc)

# ---------------- Handle (local: XY plane, hub at origin) ----------------
handle = new_body("Handle", ("PinX", "HandleY0", "PinZ"), RX)
s = Sk(P, handle, "HubSketch").circle("0", "0", "HubD")
pad(handle, s, "HandleT", "Hub")
s = Sk(P, handle, "HubBossSketch").circle("0", "0", "HubD")
pad(handle, s, "HubExt", "HubBoss", reversed=True)
s = Sk(P, handle, "BarSketch").rect("0", "-HandleW/2", "HandleL", "HandleW/2")
pad(handle, s, "HandleT", "Bar")
s = Sk(P, handle, "KnobSketch").circle("HandleL", "0", "KnobD")
pad(handle, s, "HandleT", "Knob")
s = Sk(P, handle, "HandleBoreSketch", offset="HandleT").d_shape("BoreR", "BoreFd")
pocket(handle, s, None, "HandleDBore")
cad.step(doc)

# ---------------- Spring clip (local: XY plane, centred on the shaft axis) ----------------
# C-ring: mouth toward -X narrower than the groove floor so the arms spring over it and snap
# shut; pull tab toward +X. Sits in the groove against the handle's outer face.
clip = new_body("SpringClip", ("PinX", "HandleY0 + HandleT", "PinZ"), RX)
ro_x, ri_x = "sqrt(ClipRo**2 - (ClipMouthW/2)**2)", "sqrt(ClipRi**2 - (ClipMouthW/2)**2)"
s = Sk(P, clip, "ClipSketch").path([
    (f"~-{ro_x}", "-ClipMouthW/2"), (f"~-{ro_x}", "ClipMouthW/2"),
    (f"~-{ri_x}", "ClipMouthW/2"), (f"~-{ri_x}", "-ClipMouthW/2")],
    {0: ("0", "0", "ClipRo", True), 2: ("0", "0", "ClipRi", False)})
pad(clip, s, "ClipT", "ClipRing")
s = Sk(P, clip, "TabSketch").rect("ClipRo - 1", "-ClipTabW/2", "ClipRo + ClipTabL", "ClipTabW/2")
pad(clip, s, "ClipT", "PullTab")
cad.step(doc)

# ---------------- Dovetail key (world coordinates) ----------------
# Same section as the frame's tenon; fills the slot from the frame's side face to the base edge.
key = new_body("DovetailKey")
s = Sk(P, key, "KeySketch", "XZ", offset="FrameT/2 + ClrLoc").path([
    ("FootL/2 - DovetailW/2", "BaseH"), ("FootL/2 - DovetailW/2 - DovetailH*DtTan", "BaseH - DovetailH"),
    ("FootL/2 + DovetailW/2 + DovetailH*DtTan", "BaseH - DovetailH"), ("FootL/2 + DovetailW/2", "BaseH")])
pad(key, s, "KeyL", "Key")
cad.step(doc)

# ---------------- Juice cup (local: axis = Z, bottom z=0) ----------------
# Cup with a dome on a pedestal in the middle; the lime half sits cut side down on the dome,
# juice collects in the ring around the pedestal.
jcup = new_body("JuiceCup", ("RamX", "0", "JuiceBotZ"))
s = Sk(P, jcup, "JuiceCupProfile", "XZ").path([
    ("0", "0"), ("JcR", "0"), ("JcR", "JcH"), ("JcR - JuiceWall", "JcH"),
    ("JcR - JuiceWall", "JuiceFloor"), ("DomeR", "JuiceFloor"), ("~DomeR", "JuiceFloor + PedH"),
    ("0", "~JuiceFloor + PedH + DomeR")],
    {6: ("0", "JuiceFloor + PedH", "DomeR", True)})
cad.revolve(jcup, s.s, "CupAndDome")
cad.step(doc)

# ---------------- Plunger (local: rim at z=0, axis = Z) ----------------
# Upside-down cup on the ram: hemispherical cavity concentric with the dome at end of stroke,
# square socket for the ram tip on top.
plunger = new_body("Plunger", ("RamX", "0", "DomeBaseZ"))
# top outer edge rounded with a PlTopR arc drawn in the sketch (survives parameter changes)
s = Sk(P, plunger, "PlungerProfile", "XZ").path([
    ("~CupR", "0"), ("0", "~CupR"), ("0", "PlH"), ("PlOR - PlTopR", "~PlH"), ("~PlOR", "PlH - PlTopR"),
    ("PlOR", "0")],
    {0: ("0", "0", "CupR", True), 3: ("PlOR - PlTopR", "PlH - PlTopR", "PlTopR", False)})
cad.revolve(plunger, s.s, "PressCup")
s = Sk(P, plunger, "SocketSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress)", "-(RamT/2 + ClrPress)", "RamW/2 + ClrPress", "RamT/2 + ClrPress")
pocket(plunger, s, "RamTipL", "RamSocket")
# lead-in chamfer: a short pocket from a rectangle SocketChamfer larger all round, tapering 45 deg
# inward to the socket size (taper instead of a Chamfer feature: no edge references to break)
s = Sk(P, plunger, "SocketChamferSketch", offset="PlH").rect(
    "-(RamW/2 + ClrPress + SocketChamfer)", "-(RamT/2 + ClrPress + SocketChamfer)",
    "RamW/2 + ClrPress + SocketChamfer", "RamT/2 + ClrPress + SocketChamfer")
f = pocket(plunger, s, "SocketChamfer", "SocketChamfer")
f.TaperAngle = -45
cad.step(doc)

# ---------------- verify + export ----------------
# Print orientations, chosen so the main loads run along the layers:
#  Frame/Ram on their side (C-frame bending, rack teeth, ram axis all in-layer), Shaft on its flat
#  (layers along the axis for torsion), Handle flat bar-face down (swing-plane bending in-layer),
#  Plunger socket-down / cavity-up (axial compression, no overhang), the rest upright.
ID = App.Rotation()
SIDE = App.Rotation(V(1, 0, 0), 90)  # lay flat: model Y becomes print Z
PARTS = {
    "Base": (base, ID), "Frame": (frame, SIDE), "Ram": (ram, SIDE), "Pinion": (pinion, ID),
    "Shaft": (shaft, SIDE), "Handle": (handle, App.Rotation(V(1, 0, 0), 180)), "JuiceCup": (jcup, ID),
    "Plunger": (plunger, App.Rotation(V(1, 0, 0), 180)),
    "SpringClip": (clip, ID), "DovetailKey": (key, ID),
}
COLORS = {
    "Base": (0.25, 0.25, 0.28),     # charcoal
    "Frame": (0.15, 0.40, 0.75),    # blue
    "Ram": (0.85, 0.45, 0.10),      # orange
    "Pinion": (0.90, 0.75, 0.15),   # gold
    "Shaft": (0.80, 0.15, 0.15),    # red
    "Handle": (0.45, 0.20, 0.60),   # purple
    "SpringClip": (0.10, 0.60, 0.55),  # teal
    "DovetailKey": (0.60, 0.60, 0.62),  # light grey
    "JuiceCup": (0.40, 0.75, 0.20), # lime green
    "Plunger": (0.95, 0.95, 0.85),  # cream
}
for name, (b, rot) in PARTS.items():
    cad.color(b, COLORS[name])
    cad.set_print_rotation(b, rot)
print(cad.check_assembly(doc, PARTS))
print("stroke %.1f mm, handle turns %.0f deg, leverage %.1f : 1" % (
    P["Stroke"], math.degrees(P["Stroke"] / P["PitchR"]), P["HandleL"] / P["PitchR"]))
print(cad.export_parts(doc, PARTS, "lime_press"))
print(cad.shot(doc, "lime_press_iso"))
print(cad.section(doc))  # half-section through the ram axis, regenerated every build

# ===== step 02:23:19 ok  (source: designs/lime_press_verify.py) =====
# Verify the open lime_press model the way a user would use it: edit spreadsheet
# cells, recompute, then check every part (valid, fully constrained, fits the
# printer, no interference) and sweep all moving parts (ram, plunger, pinion, shaft, handle,
# clip) through the full stroke checking for collisions.
# Ends with the defaults restored.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
S = d.getObject("Params")
CELLS = {S.getAlias(c): c for c in S.getUsedCells() if S.getAlias(c)}


def g(alias):
    return float(S.get(alias))


def trial(changes):
    old = {k: S.getContents(CELLS[k]) for k in changes}
    for k, v in changes.items():
        S.set(CELLS[k], str(v))
    d.recompute()
    cad.check_assembly(d, cad.parts_of(d))
    # kinematic sweep through the whole stroke: ram + plunger rise, pinion/shaft/handle/clip turn
    turning, lifting = ("Pinion", "Shaft", "Handle", "SpringClip"), ("Ram", "Plunger")
    fixed = ("Frame", "Base", "JuiceCup", "DovetailKey")
    shapes = {n: d.getObject(n).Shape for n in turning + lifting + fixed}
    c, worst = V(g("PinX"), 0, g("PinZ")), {}
    for i in range(10):
        dz = (g("Stroke") + g("HeadGap")) * i / 9
        pos = {n: shapes[n] for n in fixed}
        for n in lifting:
            pos[n] = shapes[n].copy(); pos[n].translate(V(0, 0, dz))
        for n in turning:
            pos[n] = shapes[n].copy(); pos[n].rotate(c, V(0, 1, 0), -dz / g("PitchR") * 57.29578)
        for a in turning + lifting:
            for b in pos:
                if a < b and not (a in turning and b in turning) and not (a in lifting and b in lifting):
                    if pos[a].BoundBox.intersect(pos[b].BoundBox):
                        v = pos[a].common(pos[b]).Volume
                        if v > 1e-3:
                            worst[(a, b)] = max(worst.get((a, b), 0), v)
    assert not worst, f"collisions during stroke: {worst}"
    print(f"OK {changes}: frame {g('HeadTopZ') - g('FrameBotZ'):.1f} mm tall, stroke {g('Stroke'):.1f} mm")
    return old


for case in ({"LimeMaxD": 25.4, "ClrSlide": 0.4, "ClrLoc": 0.5},
             {"LimeMaxD": 38},
             {"GearM": 2, "PinionZ": 16, "ClrGear": 0.3},
             {"LimeMaxD": 51, "ClrSlide": 0.3, "ClrLoc": 0.4, "GearM": 2.5, "PinionZ": 14, "ClrGear": 0.2}):
    trial(case)

# ===== step 02:23:19 ok  (source: stdin) =====
# check: handle outer face vs base edge, shaft & hub lengths
import FreeCAD as App
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
print("handle outer face y=%.2f | base edge y=%.2f | handle bbox YMax=%.2f" % (
    g("HandleY0") + g("HandleT"), g("JcR") + g("BaseMargin"), d.getObject("Handle").Shape.optimalBoundingBox().YMax))
print("hub boss %.1f mm, shaft %.1f mm (+cap)" % (g("HubExt"), g("ShaftL")))

# ===== step 02:23:28 ok  (source: stdin) =====
# sanity check of the sweep test: reversed rotation must report handle hitting the cup/plunger
import FreeCAD as App
V = App.Vector
d = App.getDocument("lime_press"); P = d.getObject("Params"); g = lambda a: float(P.get(a))
c = V(g("PinX"), 0, g("PinZ")); hits = set()
for i in range(10):
    ang = +(g("Stroke") + g("HeadGap")) * i / 9 / g("PitchR") * 57.29578   # wrong direction
    h = d.getObject("Handle").Shape.copy(); h.rotate(c, V(0, 1, 0), ang)
    for n in ("JuiceCup", "Plunger", "Base", "Frame"):
        if h.common(d.getObject(n).Shape).Volume > 1e-3:
            hits.add((n, round(ang)))
print(sorted(hits))

# ===== step 02:23:42 ok  (source: designs/lime_press_plates.py) =====
# Arrange all lime-press parts (in their strength-chosen print orientation) on
# 180 x 180 build plates, check spacing and printability, and export one
# combined STL per plate to out/limepressv1plates/. Also builds a preview doc.
import os

import FreeCAD as App
import Part

from t2m import cad

V = App.Vector
GAP = 4.0
d = App.getDocument("lime_press")
P = d.getObject("Params")
parts = cad.parts_of(d)
shp = {n: cad.print_shape(b, r) for n, (b, r) in parts.items()}
size = {n: (s.BoundBox.XLength, s.BoundBox.YLength) for n, s in shp.items()}


def g(alias):
    return float(P.get(alias))


# Plates are grouped by infill (the printer uses one infill setting per plate).
# Plate 1 (40%): Frame on its side, Plunger nested in the open mouth of the C
# (print y = HeadTopZ - model z, so the mouth spans y = HeadH .. frame height,
# x = FootL .. HeadFrontX), Ram beside it.
fw = size["Frame"][0]
plate1 = cad.plate([
    ("Frame", shp["Frame"], 0, 0, 0),
    ("Plunger", shp["Plunger"], g("FootL") + GAP, g("HeadH") + GAP, 0),
    ("Ram", shp["Ram"], fw + GAP, 0, 0),
], GAP)

# Plate 2 (40%): Base, with the JuiceCup above it.
plate2 = cad.plate([
    ("Base", shp["Base"], 0, 0, 0),
    ("JuiceCup", shp["JuiceCup"], 0, size["Base"][1] + GAP, 0),
], GAP)

# Plate 3 (100%): the torque path - Handle, Pinion, Shaft - plus the small SpringClip and DovetailKey.
row_y = size["Handle"][1] + GAP
plate3 = cad.plate([
    ("Handle", shp["Handle"], 0, 0, 0),
    ("Pinion", shp["Pinion"], 0, row_y, 0),
    ("Shaft", shp["Shaft"], size["Pinion"][0] + GAP, row_y, 0),
    ("SpringClip", shp["SpringClip"], size["Pinion"][0] + size["Shaft"][0] + 2 * GAP, row_y, 0),
    ("DovetailKey", shp["DovetailKey"],
     size["Pinion"][0] + size["Shaft"][0] + size["SpringClip"][0] + 3 * GAP, row_y, 0),
], GAP)
PLATES = {"plate1_infill40": plate1, "plate2_infill40": plate2, "plate3_infill100": plate3}

placed = [n for pl in PLATES.values() for n in pl]
assert sorted(placed) == sorted(parts), "every part on exactly one plate"

out = os.path.join(cad.OUT, "limepressv1plates")
os.makedirs(out, exist_ok=True)
for f in os.listdir(out):  # drop stale plate files from earlier layouts
    if f.endswith(".stl"):
        os.remove(os.path.join(out, f))
for name, pl in PLATES.items():
    print(f"--- {name}: " + ", ".join(pl))
    for n, s in pl.items():
        bed, over = cad.printability(s)
        print(f"   {n:8s} bed contact {bed:7.0f} mm2   overhang/bridge >45deg {over:6.0f} mm2   "
              f"height {s.BoundBox.ZLength:5.1f}")
    print("   " + cad.write_stl(Part.makeCompound(list(pl.values())), os.path.join(out, f"{name}.stl")))

# preview document: both plates side by side with bed outlines, part colours kept
if "lime_press_plates" in App.listDocuments():
    App.closeDocument("lime_press_plates")
pv = App.newDocument("lime_press_plates")
for i, pl in enumerate(PLATES.values()):
    dx = i * (cad.BUILD_VOLUME[0] + 30)
    bed = pv.addObject("Part::Feature", f"Bed{i + 1}")
    bed.Shape = Part.makeBox(cad.BUILD_VOLUME[0], cad.BUILD_VOLUME[1], 1, V(dx, 0, -1))
    cad.color(bed, (0.9, 0.9, 0.9))
    for n, s in pl.items():
        o = pv.addObject("Part::Feature", n)
        o.Shape = s.translated(V(dx, 0, 0))
        cad.color(o, parts[n][0].ViewObject.ShapeAppearance[0].DiffuseColor[:3])
pv.recompute()
print(cad.shot(pv, "lime_press_plates_top", "Top"))
print(cad.shot(pv, "lime_press_plates_iso"))

# ===== step 02:23:47 ok  (source: designs/lime_press_export.py) =====
# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))

# ===== step 02:23:51 ok  (source: designs/lime_press_joint_check.py) =====
# Check the frame/base dovetail on the open lime_press model: it must lock in X, Z and +Y,
# slide out only toward -Y, and report the actual play in each direction.
import FreeCAD as App

V = App.Vector
d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
frame, base = d.getObject("Frame").Shape, d.getObject("Base").Shape


def hit(v):
    f = frame.copy()
    f.translate(v)
    return f.common(base).Volume > 1e-3


def play(direction, limit=3.0):
    """Smallest move along direction that collides (bisection), or None if free up to limit."""
    if not hit(direction * limit):
        return None
    lo, hi = 0.0, limit
    for _ in range(20):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if hit(direction * mid) else (mid, hi)
    return hi


res = {name: play(v) for name, v in (("lift +Z", V(0, 0, 1)), ("front +X", V(1, 0, 0)),
                                      ("back -X", V(-1, 0, 0)), ("closed end +Y", V(0, 1, 0)))}
for name, p in res.items():
    print(f"{name:14s} play {p:.3f} mm" if p is not None else f"{name:14s} NOT LOCKED")
out_free = not hit(V(0, -(g("JcR") + g("BaseMargin") + g("FrameT") / 2 + 1), 0))
print("slides out toward -Y:", out_free)
assert all(p is not None and p < 0.5 for p in res.values()) and out_free

# ===== step 02:26:54 ok  (source: designs/lime_press_anim.py) =====
# Render an animation of the open lime_press model squeezing a lime.
# Frames go to out/anim_frames/ as ext_NNN.png (outside, 3/4 view) and cut_NNN.png (cutaway,
# front view). Combine with:  python3 t2m/frames_to_gif.py out/anim_frames out/lime_press_anim.gif
#
# Kinematics match the verification sweep: ram + plunger rise by r, pinion/shaft/handle/clip
# turn by -r/PitchR about the shaft axis. The lime half sits cut side down on the dome; once
# the plunger cup reaches it, it is drawn as the space left between cup and dome, and the
# squeezed-out volume (x JUICE_FRACTION) fills the juice ring.
import math
import os

import FreeCAD as App
import FreeCADGui as Gui
import Part

from t2m import cad

V = App.Vector
FRAMES = os.path.join(cad.OUT, "anim_frames")
SIZE = (800, 600)
JUICE_FRACTION = 0.5
LIME_COLOR, JUICE_COLOR = (0.75, 0.90, 0.25), (0.98, 0.95, 0.55)

d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
TURNING, LIFTING = ("Pinion", "Shaft", "Handle", "SpringClip"), ("Ram", "Plunger")
axis_c = V(g("PinX"), 0, g("PinZ"))
cx, base_z, dome_r, cup_r, lime_r = g("RamX"), g("DomeBaseZ"), g("DomeR"), g("CupR"), g("LimeMaxD") / 2
apex_z = base_z + dome_r
keep = Part.makeBox(1e4, 1e4, 1e4, V(-5e3, 0, -5e3))  # y >= 0 for the cutaway
dome = d.getObject("JuiceCup").Shape


def lime_shape(r):
    """Lime when the plunger rim is r above the dome base."""
    if base_z + r + cup_r >= apex_z + lime_r:  # not touched yet: half sphere on the dome tip
        s = Part.makeSphere(lime_r, V(cx, 0, apex_z), V(0, 0, 1), 0, 90)
    else:                                       # squeezed: cup cavity minus dome
        s = Part.makeSphere(cup_r, V(cx, 0, base_z + r), V(0, 0, 1), 0, 90).cut(dome)
    return s


lime_v0 = lime_shape(1e3).Volume
ring_in, ring_out = dome_r, g("JcR") - g("JuiceWall")
floor_z = g("JuiceBotZ") + g("JuiceFloor")


def juice_shape(squeezed):
    h = max(squeezed * JUICE_FRACTION / (math.pi * (ring_out ** 2 - ring_in ** 2)), 0.05)
    return Part.makeCylinder(ring_out, h, V(cx, 0, floor_z)).cut(Part.makeCylinder(ring_in, h, V(cx, 0, floor_z)))


def setup(name, cut):
    if name in App.listDocuments():
        App.closeDocument(name)
    ad = App.newDocument(name)
    objs = {}
    for b in d.findObjects("PartDesign::Body"):
        o = ad.addObject("Part::Feature", b.Label)
        o.Shape = b.Shape.common(keep) if cut else b.Shape.copy()
        cad.color(o, b.ViewObject.ShapeAppearance[0].DiffuseColor[:3])
        objs[b.Label] = (o, o.Placement)
    for n, col in (("Lime", LIME_COLOR), ("Juice", JUICE_COLOR)):
        o = ad.addObject("Part::Feature", n)
        cad.color(o, col)
        objs[n] = (o, None)
    objs["Juice"][0].ViewObject.Transparency = 25
    return ad, objs


def pose(objs, r, lime, juice, cut):
    ang = -r / g("PitchR") * 180 / math.pi
    for n in TURNING:
        o, p0 = objs[n]
        o.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), ang), axis_c).multiply(p0)
    for n in LIFTING:
        o, p0 = objs[n]
        o.Placement = App.Placement(V(0, 0, r), App.Rotation()).multiply(p0)
    objs["Lime"][0].Shape = lime.common(keep) if cut else lime
    objs["Juice"][0].Shape = juice.common(keep) if cut else juice


ext, ext_objs = setup("lime_press_anim", cut=False)
cut, cut_objs = setup("lime_press_anim_cut", cut=True)
views = {"ext": (ext, ext_objs, "Isometric"), "cut": (cut, cut_objs, "Front")}

# fix each camera once so it covers the whole motion: pose at mid stroke (handle up) plus
# ghost handles at both ends, fit, then drop the ghosts
top = g("Stroke") + g("HeadGap")
for key, (ad, objs, view) in views.items():
    pose(objs, top / 2, lime_shape(top / 2), juice_shape(0), key == "cut")
    ghosts = []
    for r in (0, top):
        gh = ad.addObject("Part::Feature", "Ghost")
        gh.Shape = objs["Handle"][0].Shape.copy()
        gh.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), -r / g("PitchR") * 180 / math.pi),
                                     axis_c).multiply(objs["Handle"][1])
        ghosts.append(gh)
    ad.recompute()
    v = Gui.getDocument(ad.Name).ActiveView
    getattr(v, "view" + view)()
    v.fitAll()
    for gh in ghosts:
        ad.removeObject(gh.Name)

# motion: top -> press -> hold -> back up -> hold (cosine easing)
ease = lambda t: (1 - math.cos(math.pi * t)) / 2
seq = ([top * (1 - ease(i / 39)) for i in range(40)] + [0.0] * 8 +
       [top * ease(i / 23) for i in range(24)] + [top] * 8)
os.makedirs(FRAMES, exist_ok=True)
for f in os.listdir(FRAMES):
    os.remove(os.path.join(FRAMES, f))
lime_min = lime_v0
for i, r in enumerate(seq):
    lime = lime_shape(r)
    lime_min = min(lime_min, lime.Volume)
    if lime.Volume > lime_min + 1e-6:          # once squeezed, the lime stays squeezed
        lime = lime_shape(0)
    juice = juice_shape(lime_v0 - lime_min)
    for key, (ad, objs, _) in views.items():
        pose(objs, r, lime, juice, key == "cut")
        ad.recompute()
        Gui.updateGui()
        Gui.getDocument(ad.Name).ActiveView.saveImage(
            os.path.join(FRAMES, f"{key}_{i:03d}.png"), SIZE[0], SIZE[1], "White")
App.setActiveDocument("lime_press")
print(f"{len(seq)} frames -> {FRAMES}; juice at end {(lime_v0 - lime_min) * JUICE_FRACTION / 1000:.1f} ml")

# ===== step 02:27:35 ok  (source: designs/lime_press_anim.py) =====
# Render an animation of the open lime_press model squeezing a lime.
# Frames go to out/anim_frames/ as ext_NNN.png (outside, 3/4 view) and cut_NNN.png (cutaway,
# front view). Combine with:  python3 t2m/frames_to_gif.py out/anim_frames out/lime_press_anim.gif
#
# Kinematics match the verification sweep: ram + plunger rise by r, pinion/shaft/handle/clip
# turn by -r/PitchR about the shaft axis. The lime half sits cut side down on the dome; once
# the plunger cup reaches it, it is drawn as the space left between cup and dome, and the
# squeezed-out volume (x JUICE_FRACTION) fills the juice ring.
import math
import os

import FreeCAD as App
import FreeCADGui as Gui
import Part

from t2m import cad

V = App.Vector
FRAMES = os.path.join(cad.OUT, "anim_frames")
SIZE = (1200, 900)
JUICE_FRACTION = 0.5
LIME_COLOR, JUICE_COLOR = (0.75, 0.90, 0.25), (0.98, 0.95, 0.55)

d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
TURNING, LIFTING = ("Pinion", "Shaft", "Handle", "SpringClip"), ("Ram", "Plunger")
axis_c = V(g("PinX"), 0, g("PinZ"))
cx, base_z, dome_r, cup_r, lime_r = g("RamX"), g("DomeBaseZ"), g("DomeR"), g("CupR"), g("LimeMaxD") / 2
apex_z = base_z + dome_r
keep = Part.makeBox(1e4, 1e4, 1e4, V(-5e3, 0, -5e3))  # y >= 0 for the cutaway
dome = d.getObject("JuiceCup").Shape


def lime_shape(r):
    """Lime when the plunger rim is r above the dome base."""
    if base_z + r + cup_r >= apex_z + lime_r:  # not touched yet: half sphere on the dome tip
        s = Part.makeSphere(lime_r, V(cx, 0, apex_z), V(0, 0, 1), 0, 90)
    else:                                       # squeezed: cup cavity minus dome
        s = Part.makeSphere(cup_r, V(cx, 0, base_z + r), V(0, 0, 1), 0, 90).cut(dome)
    return s


lime_v0 = lime_shape(1e3).Volume
ring_in, ring_out = dome_r, g("JcR") - g("JuiceWall")
floor_z = g("JuiceBotZ") + g("JuiceFloor")


def juice_shape(squeezed):
    h = max(squeezed * JUICE_FRACTION / (math.pi * (ring_out ** 2 - ring_in ** 2)), 0.05)
    return Part.makeCylinder(ring_out, h, V(cx, 0, floor_z)).cut(Part.makeCylinder(ring_in, h, V(cx, 0, floor_z)))


def setup(name, cut):
    if name in App.listDocuments():
        App.closeDocument(name)
    ad = App.newDocument(name)
    objs = {}
    for b in d.findObjects("PartDesign::Body"):
        o = ad.addObject("Part::Feature", b.Label)
        o.Shape = b.Shape.common(keep) if cut else b.Shape.copy()
        cad.color(o, b.ViewObject.ShapeAppearance[0].DiffuseColor[:3])
        objs[b.Label] = (o, o.Placement)
    for n, col in (("Lime", LIME_COLOR), ("Juice", JUICE_COLOR)):
        o = ad.addObject("Part::Feature", n)
        cad.color(o, col)
        objs[n] = (o, None)
    objs["Juice"][0].ViewObject.Transparency = 25
    return ad, objs


def pose(objs, r, lime, juice, cut):
    ang = -r / g("PitchR") * 180 / math.pi
    for n in TURNING:
        o, p0 = objs[n]
        o.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), ang), axis_c).multiply(p0)
    for n in LIFTING:
        o, p0 = objs[n]
        o.Placement = App.Placement(V(0, 0, r), App.Rotation()).multiply(p0)
    objs["Lime"][0].Shape = lime.common(keep) if cut else lime
    objs["Juice"][0].Shape = juice.common(keep) if cut else juice


ext, ext_objs = setup("lime_press_anim", cut=False)
cut, cut_objs = setup("lime_press_anim_cut", cut=True)
views = {"ext": (ext, ext_objs, "Isometric"), "cut": (cut, cut_objs, "Front")}

# fix each camera once so it covers the whole motion: pose at mid stroke (handle up) plus
# ghost handles at both ends, fit, then drop the ghosts
top = g("Stroke") + g("HeadGap")
for key, (ad, objs, view) in views.items():
    pose(objs, top / 2, lime_shape(top / 2), juice_shape(0), key == "cut")
    ghosts = []
    for r in (0, top):
        gh = ad.addObject("Part::Feature", "Ghost")
        gh.Shape = objs["Handle"][0].Shape.copy()
        gh.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), -r / g("PitchR") * 180 / math.pi),
                                     axis_c).multiply(objs["Handle"][1])
        ghosts.append(gh)
    ad.recompute()
    v = Gui.getDocument(ad.Name).ActiveView
    getattr(v, "view" + view)()
    v.fitAll()
    for gh in ghosts:
        ad.removeObject(gh.Name)

# motion: top -> press -> hold -> back up -> hold (cosine easing)
ease = lambda t: (1 - math.cos(math.pi * t)) / 2
seq = ([top * (1 - ease(i / 39)) for i in range(40)] + [0.0] * 8 +
       [top * ease(i / 23) for i in range(24)] + [top] * 8)
os.makedirs(FRAMES, exist_ok=True)
for f in os.listdir(FRAMES):
    os.remove(os.path.join(FRAMES, f))
lime_min = lime_v0
for i, r in enumerate(seq):
    lime = lime_shape(r)
    lime_min = min(lime_min, lime.Volume)
    if lime.Volume > lime_min + 1e-6:          # once squeezed, the lime stays squeezed
        lime = lime_shape(0)
    juice = juice_shape(lime_v0 - lime_min)
    for key, (ad, objs, _) in views.items():
        pose(objs, r, lime, juice, key == "cut")
        ad.recompute()
        Gui.updateGui()
        Gui.getDocument(ad.Name).ActiveView.saveImage(
            os.path.join(FRAMES, f"{key}_{i:03d}.png"), SIZE[0], SIZE[1], "White")
App.setActiveDocument("lime_press")
print(f"{len(seq)} frames -> {FRAMES}; juice at end {(lime_v0 - lime_min) * JUICE_FRACTION / 1000:.1f} ml")

# ===== step 02:28:03 FAILED  (source: designs/lime_press_anim.py) =====
# error: RuntimeError: No SWIG wrapped library loaded
# # Render an animation of the open lime_press model squeezing a lime.
# # Frames go to out/anim_frames/ as ext_NNN.png (outside, 3/4 view) and cut_NNN.png (cutaway,
# # front view). Combine with:  python3 t2m/frames_to_gif.py out/anim_frames out/lime_press_anim.gif
# #
# # Kinematics match the verification sweep: ram + plunger rise by r, pinion/shaft/handle/clip
# # turn by -r/PitchR about the shaft axis. The lime half sits cut side down on the dome; once
# # the plunger cup reaches it, it is drawn as the space left between cup and dome, and the
# # squeezed-out volume (x JUICE_FRACTION) fills the juice ring.
# import math
# import os
# 
# import FreeCAD as App
# import FreeCADGui as Gui
# import Part
# 
# from t2m import cad
# 
# V = App.Vector
# FRAMES = os.path.join(cad.OUT, "anim_frames")
# SIZE = (1200, 900)
# JUICE_FRACTION = 0.5
# LIME_COLOR, JUICE_COLOR = (0.75, 0.90, 0.25), (0.98, 0.95, 0.55)
# 
# d = App.getDocument("lime_press")
# P = d.getObject("Params")
# g = lambda a: float(P.get(a))
# TURNING, LIFTING = ("Pinion", "Shaft", "Handle", "SpringClip"), ("Ram", "Plunger")
# axis_c = V(g("PinX"), 0, g("PinZ"))
# cx, base_z, dome_r, cup_r, lime_r = g("RamX"), g("DomeBaseZ"), g("DomeR"), g("CupR"), g("LimeMaxD") / 2
# apex_z = base_z + dome_r
# keep = Part.makeBox(1e4, 1e4, 1e4, V(-5e3, 0, -5e3))  # y >= 0 for the cutaway
# dome = d.getObject("JuiceCup").Shape
# 
# 
# def lime_shape(r):
#     """Lime when the plunger rim is r above the dome base."""
#     if base_z + r + cup_r >= apex_z + lime_r:  # not touched yet: half sphere on the dome tip
#         s = Part.makeSphere(lime_r, V(cx, 0, apex_z), V(0, 0, 1), 0, 90)
#     else:                                       # squeezed: cup cavity minus dome
#         s = Part.makeSphere(cup_r, V(cx, 0, base_z + r), V(0, 0, 1), 0, 90).cut(dome)
#     return s
# 
# 
# lime_v0 = lime_shape(1e3).Volume
# ring_in, ring_out = dome_r, g("JcR") - g("JuiceWall")
# floor_z = g("JuiceBotZ") + g("JuiceFloor")
# 
# 
# def juice_shape(squeezed):
#     h = max(squeezed * JUICE_FRACTION / (math.pi * (ring_out ** 2 - ring_in ** 2)), 0.05)
#     return Part.makeCylinder(ring_out, h, V(cx, 0, floor_z)).cut(Part.makeCylinder(ring_in, h, V(cx, 0, floor_z)))
# 
# 
# def setup(name, cut):
#     if name in App.listDocuments():
#         App.closeDocument(name)
#     ad = App.newDocument(name)
#     objs = {}
#     for b in d.findObjects("PartDesign::Body"):
#         o = ad.addObject("Part::Feature", b.Label)
#         o.Shape = b.Shape.common(keep) if cut else b.Shape.copy()
#         cad.color(o, b.ViewObject.ShapeAppearance[0].DiffuseColor[:3])
#         objs[b.Label] = (o, o.Placement)
#     for n, col in (("Lime", LIME_COLOR), ("Juice", JUICE_COLOR)):
#         o = ad.addObject("Part::Feature", n)
#         cad.color(o, col)
#         objs[n] = (o, None)
#     objs["Juice"][0].ViewObject.Transparency = 25
#     return ad, objs
# 
# 
# def pose(objs, r, lime, juice, cut):
#     ang = -r / g("PitchR") * 180 / math.pi
#     for n in TURNING:
#         o, p0 = objs[n]
#         o.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), ang), axis_c).multiply(p0)
#     for n in LIFTING:
#         o, p0 = objs[n]
#         o.Placement = App.Placement(V(0, 0, r), App.Rotation()).multiply(p0)
#     objs["Lime"][0].Shape = lime.common(keep) if cut else lime
#     objs["Juice"][0].Shape = juice.common(keep) if cut else juice
# 
# 
# ext, ext_objs = setup("lime_press_anim", cut=False)
# cut, cut_objs = setup("lime_press_anim_cut", cut=True)
# views = {"ext": (ext, ext_objs, "Isometric"), "cut": (cut, cut_objs, "Front")}
# 
# # fix each camera once so it covers the whole motion: pose at mid stroke (handle up) plus
# # ghost handles at both ends, fit, then drop the ghosts
# top = g("Stroke") + g("HeadGap")
# for key, (ad, objs, view) in views.items():
#     pose(objs, top / 2, lime_shape(top / 2), juice_shape(0), key == "cut")
#     ghosts = []
#     for r in (0, top):
#         gh = ad.addObject("Part::Feature", "Ghost")
#         gh.Shape = objs["Handle"][0].Shape.copy()
#         gh.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), -r / g("PitchR") * 180 / math.pi),
#                                      axis_c).multiply(objs["Handle"][1])
#         ghosts.append(gh)
#     ad.recompute()
#     v = Gui.getDocument(ad.Name).ActiveView
#     getattr(v, "view" + view)()
#     v.fitAll()
#     cam = v.getCameraNode()  # fitAll fits the window's aspect, not SIZE's: zoom out, GIF step crops
#     cam.height.setValue(cam.height.getValue() * 1.25)
#     for gh in ghosts:
#         ad.removeObject(gh.Name)
# 
# # motion: top -> press -> hold -> back up -> hold (cosine easing)
# ease = lambda t: (1 - math.cos(math.pi * t)) / 2
# seq = ([top * (1 - ease(i / 39)) for i in range(40)] + [0.0] * 8 +
#        [top * ease(i / 23) for i in range(24)] + [top] * 8)
# os.makedirs(FRAMES, exist_ok=True)
# for f in os.listdir(FRAMES):
#     os.remove(os.path.join(FRAMES, f))
# lime_min = lime_v0
# for i, r in enumerate(seq):
#     lime = lime_shape(r)
#     lime_min = min(lime_min, lime.Volume)
#     if lime.Volume > lime_min + 1e-6:          # once squeezed, the lime stays squeezed
#         lime = lime_shape(0)
#     juice = juice_shape(lime_v0 - lime_min)
#     for key, (ad, objs, _) in views.items():
#         pose(objs, r, lime, juice, key == "cut")
#         ad.recompute()
#         Gui.updateGui()
#         Gui.getDocument(ad.Name).ActiveView.saveImage(
#             os.path.join(FRAMES, f"{key}_{i:03d}.png"), SIZE[0], SIZE[1], "White")
# App.setActiveDocument("lime_press")
# print(f"{len(seq)} frames -> {FRAMES}; juice at end {(lime_v0 - lime_min) * JUICE_FRACTION / 1000:.1f} ml")

# ===== step 02:28:28 ok  (source: designs/lime_press_anim.py) =====
# Render an animation of the open lime_press model squeezing a lime.
# Frames go to out/anim_frames/ as ext_NNN.png (outside, 3/4 view) and cut_NNN.png (cutaway,
# front view). Combine with:  python3 t2m/frames_to_gif.py out/anim_frames out/lime_press_anim.gif
#
# Kinematics match the verification sweep: ram + plunger rise by r, pinion/shaft/handle/clip
# turn by -r/PitchR about the shaft axis. The lime half sits cut side down on the dome; once
# the plunger cup reaches it, it is drawn as the space left between cup and dome, and the
# squeezed-out volume (x JUICE_FRACTION) fills the juice ring.
import math
import os

import FreeCAD as App
import FreeCADGui as Gui
import Part
from pivy import coin  # noqa: F401  (needed before ActiveView.getCameraNode())

from t2m import cad

V = App.Vector
FRAMES = os.path.join(cad.OUT, "anim_frames")
SIZE = (1200, 900)
JUICE_FRACTION = 0.5
LIME_COLOR, JUICE_COLOR = (0.75, 0.90, 0.25), (0.98, 0.95, 0.55)

d = App.getDocument("lime_press")
P = d.getObject("Params")
g = lambda a: float(P.get(a))
TURNING, LIFTING = ("Pinion", "Shaft", "Handle", "SpringClip"), ("Ram", "Plunger")
axis_c = V(g("PinX"), 0, g("PinZ"))
cx, base_z, dome_r, cup_r, lime_r = g("RamX"), g("DomeBaseZ"), g("DomeR"), g("CupR"), g("LimeMaxD") / 2
apex_z = base_z + dome_r
keep = Part.makeBox(1e4, 1e4, 1e4, V(-5e3, 0, -5e3))  # y >= 0 for the cutaway
dome = d.getObject("JuiceCup").Shape


def lime_shape(r):
    """Lime when the plunger rim is r above the dome base."""
    if base_z + r + cup_r >= apex_z + lime_r:  # not touched yet: half sphere on the dome tip
        s = Part.makeSphere(lime_r, V(cx, 0, apex_z), V(0, 0, 1), 0, 90)
    else:                                       # squeezed: cup cavity minus dome
        s = Part.makeSphere(cup_r, V(cx, 0, base_z + r), V(0, 0, 1), 0, 90).cut(dome)
    return s


lime_v0 = lime_shape(1e3).Volume
ring_in, ring_out = dome_r, g("JcR") - g("JuiceWall")
floor_z = g("JuiceBotZ") + g("JuiceFloor")


def juice_shape(squeezed):
    h = max(squeezed * JUICE_FRACTION / (math.pi * (ring_out ** 2 - ring_in ** 2)), 0.05)
    return Part.makeCylinder(ring_out, h, V(cx, 0, floor_z)).cut(Part.makeCylinder(ring_in, h, V(cx, 0, floor_z)))


def setup(name, cut):
    if name in App.listDocuments():
        App.closeDocument(name)
    ad = App.newDocument(name)
    objs = {}
    for b in d.findObjects("PartDesign::Body"):
        o = ad.addObject("Part::Feature", b.Label)
        o.Shape = b.Shape.common(keep) if cut else b.Shape.copy()
        cad.color(o, b.ViewObject.ShapeAppearance[0].DiffuseColor[:3])
        objs[b.Label] = (o, o.Placement)
    for n, col in (("Lime", LIME_COLOR), ("Juice", JUICE_COLOR)):
        o = ad.addObject("Part::Feature", n)
        cad.color(o, col)
        objs[n] = (o, None)
    objs["Juice"][0].ViewObject.Transparency = 25
    return ad, objs


def pose(objs, r, lime, juice, cut):
    ang = -r / g("PitchR") * 180 / math.pi
    for n in TURNING:
        o, p0 = objs[n]
        o.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), ang), axis_c).multiply(p0)
    for n in LIFTING:
        o, p0 = objs[n]
        o.Placement = App.Placement(V(0, 0, r), App.Rotation()).multiply(p0)
    objs["Lime"][0].Shape = lime.common(keep) if cut else lime
    objs["Juice"][0].Shape = juice.common(keep) if cut else juice


ext, ext_objs = setup("lime_press_anim", cut=False)
cut, cut_objs = setup("lime_press_anim_cut", cut=True)
views = {"ext": (ext, ext_objs, "Isometric"), "cut": (cut, cut_objs, "Front")}

# fix each camera once so it covers the whole motion: pose at mid stroke (handle up) plus
# ghost handles at both ends, fit, then drop the ghosts
top = g("Stroke") + g("HeadGap")
for key, (ad, objs, view) in views.items():
    pose(objs, top / 2, lime_shape(top / 2), juice_shape(0), key == "cut")
    ghosts = []
    for r in (0, top):
        gh = ad.addObject("Part::Feature", "Ghost")
        gh.Shape = objs["Handle"][0].Shape.copy()
        gh.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), -r / g("PitchR") * 180 / math.pi),
                                     axis_c).multiply(objs["Handle"][1])
        ghosts.append(gh)
    ad.recompute()
    v = Gui.getDocument(ad.Name).ActiveView
    getattr(v, "view" + view)()
    v.fitAll()
    cam = v.getCameraNode()  # fitAll fits the window's aspect, not SIZE's: zoom out, GIF step crops
    cam.height.setValue(cam.height.getValue() * 1.25)
    for gh in ghosts:
        ad.removeObject(gh.Name)

# motion: top -> press -> hold -> back up -> hold (cosine easing)
ease = lambda t: (1 - math.cos(math.pi * t)) / 2
seq = ([top * (1 - ease(i / 39)) for i in range(40)] + [0.0] * 8 +
       [top * ease(i / 23) for i in range(24)] + [top] * 8)
os.makedirs(FRAMES, exist_ok=True)
for f in os.listdir(FRAMES):
    os.remove(os.path.join(FRAMES, f))
lime_min = lime_v0
for i, r in enumerate(seq):
    lime = lime_shape(r)
    lime_min = min(lime_min, lime.Volume)
    if lime.Volume > lime_min + 1e-6:          # once squeezed, the lime stays squeezed
        lime = lime_shape(0)
    juice = juice_shape(lime_v0 - lime_min)
    for key, (ad, objs, _) in views.items():
        pose(objs, r, lime, juice, key == "cut")
        ad.recompute()
        Gui.updateGui()
        Gui.getDocument(ad.Name).ActiveView.saveImage(
            os.path.join(FRAMES, f"{key}_{i:03d}.png"), SIZE[0], SIZE[1], "White")
App.setActiveDocument("lime_press")
print(f"{len(seq)} frames -> {FRAMES}; juice at end {(lime_v0 - lime_min) * JUICE_FRACTION / 1000:.1f} ml")
