import math, os
from collections import deque
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SRC = r"work\pet\character_original.jpg"
OUT_PNG = r"work\pet\character.png"
OUT_PREVIEW = r"work\pet\preview_cutout.png"
OUT_ICO = r"work\pet\character.ico"

img = Image.open(SRC).convert("RGB")
w, h = img.size
px = img.load()

TOL = 30
BG = (255, 255, 255)

def near_bg(c):
    return abs(c[0]-BG[0]) <= TOL and abs(c[1]-BG[1]) <= TOL and abs(c[2]-BG[2]) <= TOL

# 1) flood fill background from borders
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

# 2) keep largest foreground connected component
fg = [1 if not vis[i] else 0 for i in range(w*h)]
comp = [-1]*(w*h)
best = None
for i in range(w*h):
    if fg[i] and comp[i] == -1:
        cid = len(set(comp)) if False else 0
        # assign id = number of components found so far via counting
        q2 = deque([i]); comp[i] = -2
        size = 0; minx=w; maxx=-1; miny=h; maxy=-1
        while q2:
            j = q2.popleft()
            size += 1
            cx, cy = j % w, j // w
            if cx<minx: minx=cx
            if cx>maxx: maxx=cx
            if cy<miny: miny=cy
            if cy>maxy: maxy=cy
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny = cx+dx, cy+dy
                if 0<=nx<w and 0<=ny<h and fg[ny*w+nx] and comp[ny*w+nx]==-1:
                    comp[ny*w+nx] = -2
                    q2.append(ny*w+nx)
        if best is None or size > best[0]:
            best = (size, minx, maxx, miny, maxy)
print("foreground components total px:", sum(fg))
print("largest bbox:", best[1:])

# 3) build alpha: keep pixels in largest component (recompute membership via bbox+flood from a seed)
seed_x = (best[1]+best[2])//2
seed_y = (best[3]+best[4])//2
alpha = bytearray(w*h)
q3 = deque([(seed_x, seed_y)]); alpha[seed_y*w+seed_x] = 255
while q3:
    x, y = q3.popleft()
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx,ny = x+dx, y+dy
        if 0<=nx<w and 0<=ny<h and fg[ny*w+nx] and alpha[ny*w+nx]==0:
            alpha[ny*w+nx] = 255
            q3.append((nx,ny))
keep = [1 if alpha[i]==255 else 0 for i in range(w*h)]
print("kept px:", sum(keep))

# 4) build RGBA image
out = Image.new("RGBA", (w,h), (0,0,0,0))
opx = out.load()
for y in range(h):
    for x in range(w):
        if keep[y*w+x]:
            opx[x,y] = (px[x,y][0], px[x,y][1], px[x,y][2], 255)

# 5) feather edges slightly to avoid jaggies: blur alpha a touch, re-mask
a = out.split()[3].filter(ImageFilter.GaussianBlur(0.9))
# keep hard interior but smooth boundary: threshold at 60
a = a.point(lambda v: 255 if v >= 128 else (int(v) if v > 20 else 0))
out.putalpha(a)

# 6) crop to content bbox + small pad
bbox = out.getbbox()
pad = 8
box = (max(0,bbox[0]-pad), max(0,bbox[1]-pad), min(w,bbox[2]+pad), min(h,bbox[3]+pad))
out = out.crop(box)
# remove near-invisible rows from padding artifacts
out = out.crop(out.getbbox() if out.getbbox() else (0,0,*out.size))

# 7) scale to target height
TH = 600
scale = TH / out.size[1]
if scale < 1:
    out = out.resize((max(1,int(out.size[0]*scale)), TH), Image.LANCZOS)
elif scale > 1 and out.size[1] < 700:
    out = out.resize((max(1,int(out.size[0]*scale)), TH), Image.LANCZOS)
out.save(OUT_PNG)
print("saved", OUT_PNG, out.size, os.path.getsize(OUT_PNG))

# 8) preview on checkerboard + white
cw, ch = out.size
cell = 24
check = Image.new("RGB", (cw, ch), (255,255,255))
cd = check.load()
for y in range(ch):
    for x in range(cw):
        if ((x//cell)+(y//cell)) % 2 == 0:
            cd[x,y] = (228, 228, 228)
check.paste(out, (0,0), out)
white = Image.new("RGB", (cw, ch), (255,255,255))
white.paste(out, (0,0), out)
preview = Image.new("RGB", (cw*2+10, ch), (200,200,200))
preview.paste(check, (0,0))
preview.paste(white, (cw+10,0))
preview.save(OUT_PREVIEW)
print("preview saved", OUT_PREVIEW, preview.size)

# 9) icon
ico_sizes = [16, 24, 32, 48, 64, 128, 256]
out.save(OUT_ICO, sizes=[(s,s) for s in ico_sizes])
print("ico saved", os.path.getsize(OUT_ICO))
