from PIL import Image
import numpy as np, glob, os

base = Image.open(r"work\pet\selftest\expr_normal.png").convert("RGBA")
ba = np.array(base)
# scale 0.5: 窗口301x390，角色底部对齐 y=387，角色高300，顶 y=87
# 左眼原(357,62) -> 窗口(178, 87+31=118)；右眼原(479,129) -> 窗口(239, 87+64=151)
print("=== 程序渲染的表情帧 vs normal（正确眼部区域）===")
for f in sorted(glob.glob(r"work\pet\selftest\expr_*.png")):
    name = os.path.basename(f)
    if name == "expr_normal.png": continue
    a = np.array(Image.open(f).convert("RGBA"))
    left = np.abs(a[105:135, 160:200].astype(int) - ba[105:135, 160:200].astype(int)).sum()
    right = np.abs(a[138:168, 222:258].astype(int) - ba[138:168, 222:258].astype(int)).sum()
    total = np.abs(a.astype(int) - ba.astype(int)).sum()
    print(f"{name:18s} 左眼={left:8d} 右眼={right:8d} 全图差异={total:9d}")

# 用正确区域重新生成用户预览
names = ["normal","happy","sleepy","shocked","sad","wink","love","angry","blink"]
labels = ["普通","开心","困","惊吓","委屈","眨眼","爱心眼","生气","正常眨眼"]
zoom = 6
imgs = []
for n in names:
    im = Image.open(os.path.join(r"work\pet\selftest", "expr_" + n + ".png")).convert("RGBA")
    crop = im.crop((135, 85, 270, 180))
    imgs.append(crop)
w0, h0 = imgs[0].size
cw, ch = w0*zoom, h0*zoom
cols = 3
rows = 3
pad = 10
from PIL import ImageDraw, ImageFont
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
