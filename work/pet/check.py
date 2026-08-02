from PIL import Image
from collections import deque
img = Image.open(r"work\pet\character.png")
print("size:", img.size)
a = img.split()[3]
w, h = img.size
px = a.load()
# count fully transparent pixels and their location
zeros = sum(1 for y in range(h) for x in range(w) if px[x,y] == 0)
total = w*h
print("transparent px:", zeros, f"({zeros*100/total:.1f}%)")
# find transparent holes fully enclosed by foreground (not connected to border)
vis = set()
q = deque()
for x in range(w):
    for y in (0, h-1):
        if px[x,y] == 0 and (x,y) not in vis:
            vis.add((x,y)); q.append((x,y))
for y in range(h):
    for x in (0, w-1):
        if px[x,y] == 0 and (x,y) not in vis:
            vis.add((x,y)); q.append((x,y))
while q:
    x, y = q.popleft()
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx,ny = x+dx, y+dy
        if 0<=nx<w and 0<=ny<h and px[nx,ny]==0 and (nx,ny) not in vis:
            vis.add((nx,ny)); q.append((nx,ny))
holes = zeros - len(vis)
print("enclosed transparent holes px:", holes)
# bounding box of opaque content
bbox = img.split()[3].getbbox()
print("opaque bbox:", bbox)
# edge alpha stats (semi-transparent ring)
semi = 0
for y in range(h):
    for x in range(w):
        v = px[x,y]
        if 0 < v < 255:
            semi += 1
print("semi-transparent px:", semi)
