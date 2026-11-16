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
