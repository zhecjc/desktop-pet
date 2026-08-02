from PIL import Image
import os
img = Image.open(r"work\pet\character_original.jpg")
print("size:", img.size, "mode:", img.mode)
print("filesize:", os.path.getsize(r"work\pet\character_original.jpg"))
# Sample corners and edges to determine background color
px = img.convert("RGB")
w, h = img.size
samples = {
    "top-left": px.getpixel((5, 5)),
    "top-right": px.getpixel((w-6, 5)),
    "bottom-left": px.getpixel((5, h-6)),
    "bottom-right": px.getpixel((w-6, h-6)),
    "top-center": px.getpixel((w//2, 3)),
    "bottom-center": px.getpixel((w//2, h-4)),
    "left-center": px.getpixel((3, h//2)),
    "right-center": px.getpixel((w-4, h//2)),
}
for k, v in samples.items():
    print(k, v)
# color histogram of border ring
from collections import Counter
c = Counter()
for x in range(w):
    for y in range(h):
        if x < 8 or y < 8 or x >= w-8 or y >= h-8:
            c[px.getpixel((x,y))] += 1
print("top border colors:", c.most_common(8))
