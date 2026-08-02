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
    if "A" in img.mode:
        a = np.array(img.split()[-1])
        print("  alpha min/max:", a.min(), a.max(), "transparent%:", round((a<128).mean()*100,1))
        mask = a > 128
        bbox_arr = np.argwhere(mask)
        if len(bbox_arr):
            ys, xs = bbox_arr[:,0], bbox_arr[:,1]
            print("  opaque bbox:", (xs.min(), ys.min(), xs.max(), ys.max()))
    else:
        mask = np.ones((h,w), dtype=bool)
    # 边缘像素颜色（判断背景色）
    border = arr_rgb[mask[:8,:].reshape(-1) | mask[-8:,:].reshape(-1) | mask[:,:8].reshape(-1) | mask[:,-8:].reshape(-1)]
    if len(border):
        c = Counter([tuple(b) for b in border[::7]])
        print("  border top colors:", c.most_common(3))
    c = Counter()
    for y in range(0, h, 6):
        for x in range(0, w, 6):
            if mask[y,x]:
                r,g,b = arr_rgb[y,x]
                c[(r//32*32, g//32*32, b//32*32)] += 1
    print("  top colors:", c.most_common(4))
