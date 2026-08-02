from PIL import Image
import numpy as np, glob, os

base = Image.open(r"work\pet\selftest\expr_normal.png").convert("RGBA")
ba = np.array(base)
print("=== 程序渲染的表情帧 vs normal（眼部区域差异）===")
for f in sorted(glob.glob(r"work\pet\selftest\expr_*.png")):
    name = os.path.basename(f)
    if name == "expr_normal.png": continue
    a = np.array(Image.open(f).convert("RGBA"))
    left = np.abs(a[18:45, 160:195].astype(int) - ba[18:45, 160:195].astype(int)).sum()
    right = np.abs(a[50:82, 220:255].astype(int) - ba[50:82, 220:255].astype(int)).sum()
    print(f"{name:18s} 左眼区差异={left:8d} 右眼区差异={right:8d}")

# 生成供用户查看的面部表情预览（放大显示）
from PIL import ImageDraw, ImageFont
names = ["normal","happy","sleepy","shocked","sad","wink","love","angry","blink"]
labels = ["普通","开心","困","惊吓","委屈","眨眼","爱心眼","生气","正常眨眼"]
zoom = 5
cell = None
imgs = []
for n in names:
    im = Image.open(os.path.join(r"work\pet\selftest", "expr_" + n + ".png")).convert("RGBA")
    # 程序渲染帧是 301x390（scale 0.5），面部区域约 x130-260 y20-110
    crop = im.crop((130, 15, 265, 115))
    imgs.append(crop)
w0, h0 = imgs[0].size
cw, ch = w0*zoom, h0*zoom
cols = 3
rows = 3
pad = 10
sheet = Image.new("RGB", (cols*(cw+pad)+pad, rows*(ch+pad+30)+pad), (238,238,243))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("msyh.ttc", 22)
except Exception:
    font = ImageFont.load_default()
for i, im in enumerate(imgs):
    r, c = divmod(i, cols)
    x = pad + c*(cw+pad)
    y = pad + r*(ch+pad+30)
    big = im.resize((cw, ch), Image.LANCZOS)
    sheet.paste(big, (x, y))
    d.text((x+8, y+ch+4), labels[i], fill=(50,50,70), font=font)
sheet.save(r"work\pet\expr_preview_user.png")
print("user preview saved:", sheet.size)
