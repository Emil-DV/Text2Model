# Export every part of the open lime_press model as a fine-resolution,
# print-oriented STL into out/limepressv1parts/.
import FreeCAD as App
from t2m import cad

V = App.Vector
d = App.getDocument("lime_press")
print(cad.export_stls(cad.parts_of(d), "limepressv1parts"))
