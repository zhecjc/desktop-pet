from PIL import Image
import os, glob

files = sorted(glob.glob(r"work\pet\selftest\*.png"))
for f in files:
    img = Image.open(f)
    a = img.split()[3]
    w, h = img.size
    px = a.load()
    opaque = sum(1 for y in range(0, h, 2) for x in range(0, w, 2) if px[x,y] > 128)
    bbox = a.getbbox()
    # sample colors
    rgb = img.convert("RGBA")
    colored = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r,g,b,al = rgb.getpixel((x,y))
            if al > 128 and not (abs(r-g)<12 and abs(g-b)<12):
                colored += 1
    print(f"{os.path.basename(f):20s} size={w}x{h} opaque%={opaque*4*100/(w*h):5.1f} colored={colored:5d} bbox={bbox}")
