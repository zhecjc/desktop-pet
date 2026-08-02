from PIL import Image
import numpy as np
from collections import Counter

for name in ["pose1_src", "pose2_src"]:
    img = Image.open(rf"work\pet\poses\{name}.png")
    print(f"=== {name} ===")
    print("  size:", img.size, "mode:", img.mode)
    arr_rgb = np.array(img.convert("RGB")).astype(int)
    h, w = arr_rgb.shape[:2]
    print("  corners:", [tuple(arr_rgb[y,x]) for (y,x) in [(5,5),(5,w-6),(h-6,5),(h-6,w-6)]])
    mask = np.ones((h,w), dtype=bool)
    if "A" in img.mode:
        a = np.array(img.split()[-1])
        mask = a > 128
        print("  alpha min/max:", a.min(), a.max(), "transparent%:", round((a<128).mean()*100,1))
        ys, xs = np.argwhere(mask).T
        if len(ys): print("  opaque bbox:", (xs.min(), ys.min(), xs.max(), ys.max()))
    # 边缘 10px 像素
    edges = np.concatenate([
        arr_rgb[:10,:].reshape(-1,3), arr_rgb[-10:,:].reshape(-1,3),
        arr_rgb[:,:10].reshape(-1,3), arr_rgb[:,-10:].reshape(-1,3)])
    c = Counter([tuple(b) for b in edges[::9]])
    print("  edge top colors:", c.most_common(4))
    c = Counter()
    for y in range(0, h, 6):
        for x in range(0, w, 6):
            if mask[y,x]:
                r,g,b = arr_rgb[y,x]
                c[(r//32*32, g//32*32, b//32*32)] += 1
    print("  top colors:", c.most_common(4))
    print()
