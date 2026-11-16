"""Combine ext_NNN.png / cut_NNN.png frame pairs side by side into an animated GIF
(each view cropped to the area its parts move through over the whole animation).

Runs on the host (needs Pillow):  python3 t2m/frames_to_gif.py <frames_dir> <out.gif> [fps]
"""
import glob
import os
import sys

from PIL import Image, ImageChops

frames_dir, out = sys.argv[1], sys.argv[2]
fps = float(sys.argv[3]) if len(sys.argv) > 3 else 15
HEIGHT, MARGIN = 540, 15
ext = sorted(glob.glob(os.path.join(frames_dir, "ext_*.png")))
pairs = [(Image.open(e).convert("RGB"), Image.open(e.replace("ext_", "cut_")).convert("RGB")) for e in ext]


def content_box(images):
    """Union of the non-white area over all frames of one view, plus a margin."""
    boxes = [ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox() for im in images]
    boxes = [b for b in boxes if b]
    w, h = images[0].size
    return (max(min(b[0] for b in boxes) - MARGIN, 0), max(min(b[1] for b in boxes) - MARGIN, 0),
            min(max(b[2] for b in boxes) + MARGIN, w), min(max(b[3] for b in boxes) + MARGIN, h))


crops = [content_box([p[k] for p in pairs]) for k in (0, 1)]
frames = []
for pair in pairs:
    parts = []
    for im, box in zip(pair, crops):
        im = im.crop(box)
        parts.append(im.resize((round(im.width * HEIGHT / im.height), HEIGHT), Image.LANCZOS))
    f = Image.new("RGB", (parts[0].width + parts[1].width, HEIGHT), "white")
    f.paste(parts[0], (0, 0))
    f.paste(parts[1], (parts[0].width, 0))
    frames.append(f.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
frames[0].save(out, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0, optimize=True)
print(f"{out}: {len(frames)} frames, {frames[0].width}x{frames[0].height}, {os.path.getsize(out) / 1e6:.1f} MB")
