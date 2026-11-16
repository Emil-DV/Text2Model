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
