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
