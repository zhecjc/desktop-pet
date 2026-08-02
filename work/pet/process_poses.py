from PIL import Image, ImageFilter
import numpy as np
from collections import deque
import scipy.ndimage as ndi

def cutout(src_path, out_path, target_h=600, tol=30, pad=8):
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    px = img.load()
    BG = (255, 255, 255)
    def near_bg(c):
        return abs(c[0]-BG[0]) <= tol and abs(c[1]-BG[1]) <= tol and abs(c[2]-BG[2]) <= tol
    vis = bytearray(w*h)
    q = deque()
    for x in range(w):
        for y in (0, h-1):
            if not vis[y*w+x] and near_bg(px[x,y]):
                vis[y*w+x] = 1; q.append((x,y))
    for y in range(h):
        for x in (0, w-1):
            if not vis[y*w+x] and near_bg(px[x,y]):
                vis[y*w+x] = 1; q.append((x,y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if 0 <= nx < w and 0 <= ny < h and not vis[ny*w+nx] and near_bg(px[nx,ny]):
                vis[ny*w+nx] = 1
                q.append((nx,ny))
    # 前景 = 非背景；保留最大连通块
    fg = (np.array(list(vis)).reshape(h, w) == 0)
    lbl, n = ndi.label(fg)
    if n > 1:
        sizes = ndi.sum(fg, lbl, range(1, n+1))
        keep = lbl == (np.argmax(sizes)+1)
    else:
        keep = fg
    # 构建 RGBA
    out = Image.new("RGBA", (w,h), (0,0,0,0))
    opx = out.load()
    arr = np.array(img)
    ys, xs = np.where(keep)
    for y, x in zip(ys[::1], xs[::1]):
        r,g,b = arr[y,x]
        opx[x,y] = (int(r), int(g), int(b), 255)
    # 边缘羽化
    a = out.split()[3].filter(ImageFilter.GaussianBlur(0.9))
    a = a.point(lambda v: 255 if v >= 128 else (int(v) if v > 20 else 0))
    out.putalpha(a)
    bbox = out.getbbox()
    box = (max(0,bbox[0]-pad), max(0,bbox[1]-pad), min(w,bbox[2]+pad), min(h,bbox[3]+pad))
    out = out.crop(box)
    out = out.crop(out.getbbox())
    # 缩放到目标高度
    scale = target_h / out.size[1]
    out = out.resize((max(1,int(out.size[0]*scale)), target_h), Image.LANCZOS)
    out.save(out_path)
    print(out_path, out.size)

cutout(r"work\pet\poses\pose1_src.png", r"work\pet\poses\pose1.png")
cutout(r"work\pet\poses\pose2_src.png", r"work\pet\poses\pose2.png")

# 轮廓 ASCII 图
for name in ["pose1", "pose2"]:
    img = Image.open(rf"work\pet\poses\{name}.png")
    a = np.array(img.split()[3])
    h, w = a.shape
    print(f"\n=== {name} 轮廓 ({w}x{h}) ===")
    gh, gw = 22, 40
    for gy in range(gh):
        row = ""
        for gx in range(gw):
            y0, y1 = gy*h//gh, (gy+1)*h//gh
            x0, x1 = gx*w//gw, (gx+1)*w//gw
            frac = (a[y0:y1, x0:x1] > 128).mean()
            if frac > 0.7: row += "#"
            elif frac > 0.3: row += "+"
            elif frac > 0.05: row += "."
            else: row += " "
        print(row)
