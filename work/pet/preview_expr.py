from PIL import Image
import numpy as np, os, glob

files = sorted(glob.glob(r"work\pet\expr\expr_*.png"))
print("=== 每张表情 vs 原图 的差异（眼部区域）===")
base = Image.open(r"work\pet\expr\expr_normal.png").convert("RGBA")
ba = np.array(base)
for f in files:
    name = os.path.basename(f)
    if name == "expr_normal.png": continue
    img = Image.open(f).convert("RGBA")
    a = np.array(img)
    # 左眼区域 (320,40)-(390,90)
    left = np.abs(a[40:90, 320:390].astype(int) - ba[40:90, 320:390].astype(int)).sum()
    right = np.abs(a[100:165, 440:510].astype(int) - ba[100:165, 440:510].astype(int)).sum()
    print(f"{name:18s} 左眼区差异={left:8d} 右眼区差异={right:8d}")

# 生成面部预览拼图（放大3倍）
preview_faces = []
for f in sorted(glob.glob(r"work\pet\expr\expr_*.png")):
    img = Image.open(f).convert("RGBA")
    crop = img.crop((280, 20, 530, 200))  # 面部区域
    crop = crop.resize((crop.size[0]*3, crop.size[1]*3), Image.LANCZOS)
    preview_faces.append(crop)

# 拼成网格（3列）
cols = 3
rows = (len(preview_faces) + cols - 1) // cols
cell_w = max(im.size[0] for im in preview_faces)
cell_h = max(im.size[1] for im in preview_faces)
pad = 12
sheet = Image.new("RGBA", (cols*cell_w + pad*(cols+1), rows*cell_h + pad*(rows+1)), (240,240,245,255))
for i, im in enumerate(preview_faces):
    r, c = divmod(i, cols)
    x = pad + c*(cell_w+pad)
    y = pad + r*(cell_h+pad)
    sheet.paste(im, (x, y), im)
sheet.convert("RGB").save(r"work\pet\expr_preview_faces.png")
print("face preview saved:", sheet.size)

# 每个表情裁剪后的完整角色缩略图拼图
thumbs = []
for f in sorted(glob.glob(r"work\pet\expr\expr_*.png")):
    im = Image.open(f).convert("RGBA")
    im = im.resize((120, 120), Image.LANCZOS)
    thumbs.append(im)
cols = 5
rows = (len(thumbs) + cols - 1) // cols
cw, chh = 120, 120
sheet2 = Image.new("RGBA", (cols*cw + pad*(cols+1), rows*chh + pad*(rows+1)), (255,255,255,255))
for i, im in enumerate(thumbs):
    r, c = divmod(i, cols)
    sheet2.paste(im, (pad + c*(cw+pad), pad + r*(chh+pad)), im)
sheet2.convert("RGB").save(r"work\pet\expr_preview_all.png")
print("all preview saved:", sheet2.size)
