from PIL import Image
import numpy as np
import scipy.ndimage as ndi

img = Image.open(r"work\pet\character.png").convert("RGBA")
arr = np.array(img)
a = arr[...,3]
rgb = arr[...,:3].astype(int)
mask = a > 128
h, w = a.shape
R, G, B = rgb[...,0], rgb[...,1], rgb[...,2]

# 头区域 (y<330, 对称轴 396)
head_mask = mask.copy(); head_mask[330:,:] = False
head_mask[:, :260] = False; head_mask[:, 540:] = False

# 1) 深色眼睛候选: 亮度<140 的头部区域内的块
lum = 0.3*R + 0.6*G + 0.1*B
dark = (lum < 140) & head_mask
lbl, n = ndi.label(dark)
sizes = ndi.sum(dark, lbl, range(1, n+1))
print("=== 深色块 (y<330) ===")
for i in np.argsort(sizes)[::-1][:10]:
    if sizes[i] < 60: break
    fy, fx = np.where(lbl == i+1)
    print(f"  块: {sizes[i]:.0f}px bbox=({fx.min()},{fy.min()})-({fx.max()},{fy.max()}) 中心=({fx.mean():.0f},{fy.mean():.0f})")

# 2) 红色（腮红）检测: R 明显大于 G 和 B
reddish = (R - G > 25) & (R - B > 40) & (R > 170) & head_mask
lbl2, n2 = ndi.label(reddish)
sizes2 = ndi.sum(reddish, lbl2, range(1, n2+1))
print("\n=== 红色块（腮红候选）===")
for i in np.argsort(sizes2)[::-1][:6]:
    if sizes2[i] < 100: break
    fy, fx = np.where(lbl2 == i+1)
    print(f"  块: {sizes2[i]:.0f}px bbox=({fx.min()},{fy.min()})-({fx.max()},{fy.max()}) 中心=({fx.mean():.0f},{fy.mean():.0f})")

# 3) 嘴部: 头部中线下方深色/暗红
mouth_zone = head_mask.copy(); mouth_zone[:140,:] = False; mouth_zone[230:,:] = False
mouth = (lum < 160) & mouth_zone
lbl3, n3 = ndi.label(mouth)
sizes3 = ndi.sum(mouth, lbl3, range(1, n3+1))
print("\n=== 嘴部深色块 (y140-230) ===")
for i in np.argsort(sizes3)[::-1][:6]:
    if sizes3[i] < 40: break
    fy, fx = np.where(lbl3 == i+1)
    print(f"  块: {sizes3[i]:.0f}px bbox=({fx.min()},{fy.min()})-({fx.max()},{fy.max()}) 中心=({fx.mean():.0f},{fy.mean():.0f})")

# 4) 眼睛周围肤色（打底用）
print("\n=== 关键点周围肤色采样 ===")
pts = {"左眼候选": (362, 140), "右眼候选": (445, 133), "鼻": (410, 137)}
for name, (cx, cy) in pts.items():
    ring = []
    for dy in range(-18, 19, 3):
        for dx in range(-18, 19, 3):
            yy, xx = cy+dy, cx+dx
            if 0<=yy<h and 0<=xx<w and mask[yy,xx] and (abs(dx)>=6 or abs(dy)>=6):
                ring.append(rgb[yy,xx])
    m = np.median(np.array(ring), axis=0)
    print(f"  {name} ({cx},{cy}): 肤色 RGB({m[0]:.0f},{m[1]:.0f},{m[2]:.0f})")
