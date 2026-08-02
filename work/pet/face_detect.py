from PIL import Image
import numpy as np
import scipy.ndimage as ndi

img = Image.open(r"work\pet\character.png").convert("RGBA")
arr = np.array(img)
a = arr[...,3]
rgb = arr[...,:3].astype(int)

h, w = a.shape
mask = a > 128

# 内容区域
ys, xs = np.where(mask)
top, bottom = ys.min(), ys.max()
left, right = xs.min(), xs.max()
print(f"内容区域: x[{left},{right}] y[{top},{bottom}] 高={bottom-top}")

# 头部分析：上半部（高度前55%）内找深色特征（眼睛通常是深色）
head_bottom = top + int((bottom-top)*0.62)
head_region = mask.copy()
head_region[head_bottom:,:] = False
lum = rgb[...,0]*0.3 + rgb[...,1]*0.6 + rgb[...,2]*0.1

# 在头部区域内，找比周围暗得多的像素
dark = (lum < 110) & head_region
lbl, n = ndi.label(dark)
print(f"头部深色特征块数量: {n}")
sizes = ndi.sum(dark, lbl, range(1, n+1))
order = np.argsort(sizes)[::-1]
feats = []
for i in order[:8]:
    if sizes[i] < 30: continue
    fy, fx = np.where(lbl == i+1)
    feats.append((int(sizes[i]), (fx.min(), fy.min(), fx.max(), fy.max())))
    print(f"  特征{i+1}: 像素={sizes[i]:.0f} bbox=({fx.min()},{fy.min()})-({fx.max()},{fy.max()}) 中心=({fx.mean():.0f},{fy.mean():.0f})")

# 找两个左右对称的眼睛
if len(feats) >= 2:
    f = sorted(feats, key=lambda z: z[1][0])  # 按x排序
    print("\n按x排序的深色特征中心:")
    for i,(s,b) in enumerate(f):
        cx = (b[0]+b[2])/2; cy = (b[1]+b[3])/2
        print(f"  #{i}: cx={cx:.0f} cy={cy:.0f} size={s} bbox={b}")

# 眼睛附近颜色采样（眼睛周围一圈的平均色，用于打底）
for i,(s,b) in enumerate(f[:4]):
    cx = (b[0]+b[2])//2; cy = (b[1]+b[3])//2
    r = max(6, (b[2]-b[0])//2 + 6)
    ring = []
    for dy in range(-r, r+1, 2):
        for dx in range(-r, r+1, 2):
            yy, xx = cy+dy, cx+dx
            if 0<=yy<h and 0<=xx<w and mask[yy,xx]:
                if abs(dx)>=4 or abs(dy)>=4:
                    ring.append(rgb[yy,xx])
    if ring:
        m = np.median(np.array(ring), axis=0)
        print(f"  眼睛#{i} 周围肤色: RGB({m[0]:.0f},{m[1]:.0f},{m[2]:.0f})")
