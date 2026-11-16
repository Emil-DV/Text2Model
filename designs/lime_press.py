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
