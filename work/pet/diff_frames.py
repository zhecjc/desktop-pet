from PIL import Image
import glob, os

def load(f):
    img = Image.open(f).convert("RGBA")
    return img

base = load(r"work\pet\selftest\frame_idle.png")
for f in sorted(glob.glob(r"work\pet\selftest\frame_*.png")):
    name = os.path.basename(f)
    if name == "frame_idle.png":
        continue
    img = load(f)
    w, h = base.size
    diff = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            a = base.getpixel((x,y)); b = img.getpixel((x,y))
            if a != b:
                diff += 1
    print(f"{name:20s} differs from idle: {diff} px")
