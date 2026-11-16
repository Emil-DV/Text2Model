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
