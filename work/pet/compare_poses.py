from PIL import Image
import numpy as np

char = Image.open(r"work\pet\character.png").convert("RGBA")
p1 = Image.open(r"work\pet\poses\pose1.png").convert("RGBA")
p2 = Image.open(r"work\pet\poses\pose2.png").convert("RGBA")
print("sizes: char", char.size, "pose1", p1.size, "pose2", p2.size)

# 统一缩放到相同尺寸（按宽度），底部对齐后计算差异
def align(src, w=300):
    r = w / src.size[0]
    im = src.resize((w, max(1,int(src.size[1]*r))), Image.LANCZOS)
    return im

W = 300
c = align(char, W); a = align(p1, W); b = align(p2, W)
H = max(c.size[1], a.size[1], b.size[1])
def pad(im, H):
    canvas = Image.new("RGBA", (W, H), (0,0,0,0))
    canvas.paste(im, (0, H-im.size[1]), im)
    return canvas
c = pad(c, H); a = pad(a, H); b = pad(b, H)
ca, aa, ba = np.array(c), np.array(a), np.array(b)

def diff(x, y, label):
    m = (x[...,3] > 128) | (y[...,3] > 128)
    if m.sum() == 0: return
    d = np.abs(x.astype(int) - y.astype(int))[..., :3].sum(axis=2)
    d[~m] = 0
    mean = d[m].mean()
    pct = (d[m] > 40).mean() * 100
    print(f"{label}: 平均像素差={mean:.1f} 显著差异像素占比={pct:.1f}%")

diff(ca, aa, "角色 vs 姿势1")
diff(ca, ba, "角色 vs 姿势2")
diff(aa, ba, "姿势1 vs 姿势2")

# 显著差异区域的分布（上/中/下 三部分）
def region_diff(x, y):
    m = (x[...,3] > 128) | (y[...,3] > 128)
    d = np.abs(x.astype(int) - y.astype(int))[..., :3].sum(axis=2)
    d[~m] = 0
    sig = d > 40
    h = sig.shape[0]
    for name, y0, y1 in [("上部", 0, h//3), ("中部", h//3, 2*h//3), ("下部", 2*h//3, h)]:
        print(f"    {name}: 显著差异像素 {sig[y0:y1].sum()}")
region_diff(ca, aa)
region_diff(ca, ba)
