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
