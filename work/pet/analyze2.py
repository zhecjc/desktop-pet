from PIL import Image
import numpy as np

img = Image.open(r"work\pet\character.png")
a = np.array(img.split()[3])
rgb = np.array(img.convert("RGBA"))

# 1) 不透明区域的轮廓（ASCII 图，40x30 网格）
h, w = a.shape
gh, gw = 30, 60
print("=== 轮廓图（# = 不透明，. = 透明）===")
for gy in range(gh):
    row = ""
    for gx in range(gw):
        y0, y1 = gy*h//gh, (gy+1)*h//gh
        x0, x1 = gx*w//gw, (gx+1)*w//gw
        block = a[y0:y1, x0:x1]
        frac = (block > 128).mean()
        if frac > 0.75: row += "#"
        elif frac > 0.35: row += "+"
        elif frac > 0.08: row += "."
        else: row += " "
    print(row)

# 2) 不透明像素的颜色分布
mask = a > 128
pix = rgb[mask]
print("\n=== 不透明像素数:", pix.shape[0])
# 主要颜色聚类（粗量化）
from collections import Counter
c = Counter()
for p in pix[::5]:
    c[(p[0]//32*32, p[1]//32*32, p[2]//32*32)] += 1
print("主要颜色（量化后）:")
for col, n in c.most_common(10):
    print(f"  RGB{col}: {n}")

# 3) 白色/浅色像素占比
light = ((pix[:,0]>230)&(pix[:,1]>230)&(pix[:,2]>230)).mean()
print(f"\n纯白/近白像素占比: {light*100:.1f}%")
# 彩色（非灰）占比
mx = pix.max(axis=1).astype(int); mn = pix.min(axis=1).astype(int)
colorful = ((mx-mn)>30).mean()
print(f"彩色像素占比: {colorful*100:.1f}%")

# 4) 最大连通块分析（确认是不是两个块）
import scipy.ndimage as ndi
lbl, n = ndi.label(mask)
print(f"\n连通块数量: {n}")
sizes = ndi.sum(mask, lbl, range(1, n+1))
order = np.argsort(sizes)[::-1]
for i in order[:6]:
    ys, xs = np.where(lbl == i+1)
    print(f"  块{i+1}: 像素={sizes[i]:.0f} bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 占画面{sizes[i]/mask.sum()*100:.1f}%")
