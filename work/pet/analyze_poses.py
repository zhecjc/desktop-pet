from PIL import Image
import numpy as np

for name in ["pose1_src", "pose2_src"]:
    img = Image.open(rf"work\pet\poses\{name}.png")
    print(f"=== {name} ===")
    print("  size:", img.size, "mode:", img.mode)
    a = img.split()[-1]  # alpha
    if img.mode == "RGBA" or img.mode == "LA" or img.mode == "P":
        # 检查 alpha 是否有透明
        arr = np.array(a)
        print("  alpha min/max:", arr.min(), arr.max(), "transparent%:", (arr < 128).mean()*100)
    else:
        print("  no alpha channel")
    rgb = img.convert("RGB")
    px = rgb.load()
    w, h = img.size
    corners = [px.getpixel((5,5)), px.getpixel((w-6,5)), px.getpixel((5,h-6)), px.getpixel((w-6,h-6))]
    print("  corners:", corners)
    # 内容 bbox（不透明区域）
    if img.mode in ("RGBA","LA"):
        bbox = Image.fromarray(np.array(a) > 128).getbbox()
        print("  opaque bbox:", bbox)
    # 主色
    arr_rgb = np.array(rgb)
    mask = np.ones((h,w), dtype=bool)
    if img.mode in ("RGBA","LA"):
        mask = np.array(a) > 128
    from collections import Counter
    c = Counter()
    for y in range(0, h, 5):
        for x in range(0, w, 5):
            if mask[y,x]:
                r,g,b = arr_rgb[y,x]
                c[(r//32*32, g//32*32, b//32*32)] += 1
    print("  top colors:", c.most_common(4))
