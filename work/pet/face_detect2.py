from PIL import Image
import numpy as np

img = Image.open(r"work\pet\character.png").convert("RGBA")
arr = np.array(img)
a = arr[...,3]
rgb = arr[...,:3].astype(int)
mask = a > 128
h, w = a.shape

lum = rgb[...,0]*0.3 + rgb[...,1]*0.6 + rgb[...,2]*0.1

# 头区域放大 ASCII 图：y 25..200, x 240..560，分辨亮度
def ascii_map(x0, x1, y0, y1, cols, rows, lum_thresh):
    print(f"=== 头部区域 ({x0}-{x1}, {y0}-{y1}) 亮度图 ===")
    print("   X: " + "".join(str((x0 + int((x1-x0)*(i+0.5)/cols))//100 % 10) for i in range(cols)))
    for ry in range(rows):
        line = ""
        for rx in range(cols):
            X0 = x0 + int((x1-x0)*rx/cols); X1 = x0 + int((x1-x0)*(rx+1)/cols)
            Y0 = y0 + int((y1-y0)*ry/rows); Y1 = y0 + int((y1-y0)*(ry+1)/rows)
            blk = lum[Y0:Y1, X0:X1]
            mk = mask[Y0:Y1, X0:X1]
            if mk.mean() < 0.2: ch = " "
            else:
                m = blk[mk].mean()
                if m < 90: ch = "#"
                elif m < 130: ch = "@"
                elif m < 170: ch = "+"
                elif m < 205: ch = "-"
                else: ch = "."
            line += ch
        print(f"{Y0:4d} {line}")

ascii_map(240, 560, 25, 210, 64, 37, 130)

# 深色特征重检（宽松阈值）
dark = (lum < 150) & mask
import scipy.ndimage as ndi
lbl, n = ndi.label(dark)
sizes = ndi.sum(dark, lbl, range(1, n+1))
order = np.argsort(sizes)[::-1]
print("\n亮度<150 的特征（含较大）:")
for i in order[:12]:
    if sizes[i] < 50: break
    fy, fx = np.where(lbl == i+1)
    if fy.max() > 250: continue  # 只看头部
    print(f"  像素={sizes[i]:.0f} bbox=({fx.min()},{fy.min()})-({fx.max()},{fy.max()}) 中心=({fx.mean():.0f},{fy.mean():.0f})")
