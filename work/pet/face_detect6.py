from PIL import Image
import numpy as np

img = Image.open(r"work\pet\character.png").convert("RGBA")
arr = np.array(img)
a = arr[...,3]
rgb = arr[...,:3].astype(int)
mask = a > 128
h, w = a.shape
R, G, B = rgb[...,0], rgb[...,1], rgb[...,2]
lum = 0.3*R + 0.6*G + 0.1*B

blobs = {
    "左特征(357,62)": (341, 47, 373, 77),
    "右特征(479,129)": (465, 113, 493, 146),
    "中心特征(389,148)": (350, 122, 432, 168),
}
for name, (x0, y0, x1, y1) in blobs.items():
    sub = lum[y0:y1+1, x0:x1+1]
    print(f"=== {name} ===")
    print(f"  亮度范围: {sub.min():.0f} - {sub.max():.0f}, 均值 {sub.mean():.0f}")
    # 内部是否有亮像素（高光）
    bright = (sub > 190).sum()
    print(f"  内部亮像素(>190): {bright} ({bright/sub.size*100:.0f}%)")
    # 精细亮度图
    rows, cols = 8, 10
    for ry in range(rows):
        line = ""
        for rx in range(cols):
            X0 = x0 + int((x1-x0)*rx/cols); X1 = x0 + int((x1-x0)*(rx+1)/cols)
            Y0 = y0 + int((y1-y0)*ry/rows); Y1 = y0 + int((y1-y0)*(ry+1)/rows)
            blk = lum[Y0:Y1, X0:X1]
            if blk.size == 0: line += " "; continue
            m = blk.mean()
            if m < 80: line += "#"
            elif m < 130: line += "@"
            elif m < 180: line += "+"
            elif m < 220: line += "-"
            else: line += "."
        print(f"  {line}")
    print()
