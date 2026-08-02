from PIL import Image
import numpy as np

img = Image.open(r"work\pet\character.png").convert("RGBA")
arr = np.array(img)
a = arr[...,3]
rgb = arr[...,:3].astype(int)
mask = a > 128
h, w = a.shape
lum = rgb[...,0]*0.3 + rgb[...,1]*0.6 + rgb[...,2]*0.1

# 头部中下部 y 130..330
x0, x1, y0, y1 = 260, 530, 130, 330
cols, rows = 90, 40
print("=== 头部中下部亮度图 (y130-330) ===")
for ry in range(rows):
    line = ""
    for rx in range(cols):
        X0 = x0 + int((x1-x0)*rx/cols); X1 = x0 + int((x1-x0)*(rx+1)/cols)
        Y0 = y0 + int((y1-y0)*ry/rows); Y1 = y0 + int((y1-y0)*(ry+1)/rows)
        blk = lum[Y0:Y1, X0:X1]
        mk = mask[Y0:Y1, X0:X1]
        if mk.mean() < 0.15: ch = " "
        else:
            m = blk[mk].mean()
            if m < 95: ch = "#"
            elif m < 135: ch = "@"
            elif m < 175: ch = "+"
            elif m < 210: ch = "-"
            else: ch = "."
        line += ch
    print(f"{Y0:4d}|{line}|")
