from PIL import Image
import numpy as np

img = Image.open(r"work\pet\character.png").convert("RGBA")
arr = np.array(img)
a = arr[...,3]
rgb = arr[...,:3].astype(int)
mask = a > 128
h, w = a.shape
lum = rgb[...,0]*0.3 + rgb[...,1]*0.6 + rgb[...,2]*0.1

# 精细：头+脖子区域 y 20..190, x 260..500
x0, x1, y0, y1 = 260, 500, 20, 190
cols, rows = 80, 34
print("=== 头部精细亮度图 ===")
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

# 对称轴检测：对头部区域（y 20..100）镜像对比
import scipy.ndimage as ndi
head_mask = mask.copy(); head_mask[100:,:] = False
head_lum = lum.copy(); head_lum[100:,:] = 0; head_lum[head_mask==False] = 0
best = None
for cx in range(300, 500, 4):
    # 镜像翻转
    flipped = head_lum[:, ::-1].copy()
    # 对齐：原始以cx为中心，翻转后中心在 w-cx
    off = 2*cx - w
    shifted = np.roll(flipped, off, axis=1) if off != 0 else flipped
    diff = np.abs(head_lum - shifted)
    score = diff[head_mask].mean()
    if best is None or score < best[0]:
        best = (score, cx)
print(f"\n头部对称轴 x={best[1]} (得分 {best[0]:.1f})")

# 保存头部放大图供后续用
crop = img.crop((x0-10, y0-10, x1+10, y1+10))
crop.save(r"work\pet\head_crop.png")
print("head crop saved", crop.size)
