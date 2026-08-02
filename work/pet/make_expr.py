from PIL import Image, ImageDraw, ImageFilter
import os

SRC = r"work\pet\character.png"
OUT = r"work\pet\expr"
os.makedirs(OUT, exist_ok=True)

base = Image.open(SRC).convert("RGBA")
W, H = base.size  # 602x600

# 检测到的眼睛
L_EYE = (357, 62, 17, 16)   # cx, cy, rx, ry
R_EYE = (479, 129, 14, 17)  # cx, cy, rx, ry
L_FUR = (204, 179, 112)
R_FUR = (212, 196, 124)
DARK = (70, 52, 30)

def fur_patch(img, cx, cy, rx, ry, fur):
    """用肤色柔边椭圆盖住原眼睛"""
    layer = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx-rx-4, cy-ry-4, cx+rx+4, cy+ry+4], fill=fur + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(2.5))
    return Image.alpha_composite(img, layer)

def draw_arc(img, cx, cy, rx, ry, start, end, color=DARK, width=5):
    d = ImageDraw.Draw(img)
    d.arc([cx-rx, cy-ry, cx+rx, cy+ry], start, end, fill=color + (255,), width=width)

def draw_line(img, x0, y0, x1, y1, color=DARK, width=5):
    d = ImageDraw.Draw(img)
    d.line([x0, y0, x1, y1], fill=color + (255,), width=width)

def draw_ellipse(img, x0, y0, x1, y1, color):
    d = ImageDraw.Draw(img)
    d.ellipse([x0, y0, x1, y1], fill=color + (255,))

def blush(img, cx, cy, s, alpha=110):
    layer = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx-s, cy-s, cx+s, cy+s], fill=(255, 130, 140, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    return Image.alpha_composite(img, layer)

def teardrop(img, cx, cy, s):
    layer = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx-s*0.55, cy-s*0.2, cx+s*0.55, cy+s*0.75], fill=(150, 205, 255, 230))
    d.polygon([(cx-s*0.55, cy+s*0.15), (cx+s*0.55, cy+s*0.15), (cx, cy-s*0.9)], fill=(150, 205, 255, 230))
    layer = layer.filter(ImageFilter.GaussianBlur(0.8))
    return Image.alpha_composite(img, layer)

def heart(img, cx, cy, s):
    layer = Image.new("RGBA", img.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx-s*0.9, cy-s*0.75, cx, cy+s*0.25], fill=(255, 105, 170, 255))
    d.ellipse([cx, cy-s*0.75, cx+s*0.9, cy+s*0.25], fill=(255, 105, 170, 255))
    d.polygon([(cx-s*1.0, cy+s*0.05), (cx+s*1.0, cy+s*0.05), (cx, cy+s*1.2)], fill=(255, 105, 170, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(0.5))
    return Image.alpha_composite(img, layer)

def save(img, name):
    img.save(os.path.join(OUT, name))
    print("saved", name)

# 0) normal（原图）
save(base.copy(), "expr_normal.png")

# 1) blink 眨眼（细线）
img = base.copy()
for cx, cy, rx, ry, fur in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3],L_FUR), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3],R_FUR)]:
    img = fur_patch(img, cx, cy, rx, ry, fur)
for cx, cy, rx, ry in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3]), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3])]:
    draw_line(img, cx-rx+2, cy, cx+rx-2, cy, width=5)
save(img, "expr_blink.png")

# 2) happy 开心（∩∩ 笑眼 + 腮红）
img = base.copy()
for cx, cy, rx, ry, fur in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3],L_FUR), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3],R_FUR)]:
    img = fur_patch(img, cx, cy, rx, ry, fur)
for cx, cy, rx, ry in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3]), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3])]:
    draw_arc(img, cx, cy+2, rx+2, ry+2, 180, 360, width=5)
img = blush(img, 320, 92, 13)
img = blush(img, 488, 158, 12)
save(img, "expr_happy.png")

# 3) sleepy 困（半睁眼 + 下眼弧）
img = base.copy()
for cx, cy, rx, ry, fur in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3],L_FUR), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3],R_FUR)]:
    img = fur_patch(img, cx, cy, rx, ry, fur)
for cx, cy, rx, ry in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3]), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3])]:
    draw_line(img, cx-rx+2, cy-1, cx+rx-2, cy-1, width=5)
    draw_arc(img, cx, cy+2, rx, ry-2, 0, 180, width=3)
save(img, "expr_sleepy.png")

# 4) shocked 惊吓（大白眼 + 小瞳孔）
img = base.copy()
for cx, cy, rx, ry, fur in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3],L_FUR), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3],R_FUR)]:
    img = fur_patch(img, cx, cy, rx+2, ry+2, fur)
for cx, cy, rx, ry in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3]), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3])]:
    draw_ellipse(img, cx-rx-2, cy-ry-2, cx+rx+2, cy+ry+2, (255,255,255))
    pr = 6
    draw_ellipse(img, cx-pr, cy-pr, cx+pr, cy+pr, (30,30,40))
    draw_ellipse(img, cx-pr+2, cy-pr+2, cx-pr+5, cy-pr+5, (255,255,255))
save(img, "expr_shocked.png")

# 5) sad 委屈（下垂眼 + 泪珠）
img = base.copy()
for cx, cy, rx, ry, fur in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3],L_FUR), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3],R_FUR)]:
    img = fur_patch(img, cx, cy, rx, ry, fur)
for cx, cy, rx, ry in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3]), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3])]:
    draw_arc(img, cx, cy-2, rx+2, ry+6, 0, 180, width=5)
img = teardrop(img, R_EYE[0]+8, R_EYE[1]+18, 14)
save(img, "expr_sad.png")

# 6) wink 眨眼卖萌（左眼笑弧，右眼保留）
img = base.copy()
img = fur_patch(img, L_EYE[0], L_EYE[1], L_EYE[2], L_EYE[3], L_FUR)
draw_arc(img, L_EYE[0], L_EYE[1]+2, L_EYE[2]+2, L_EYE[3]+2, 180, 360, width=5)
save(img, "expr_wink.png")

# 7) love 爱心眼
img = base.copy()
for cx, cy, rx, ry, fur in [(L_EYE[0],L_EYE[1],L_EYE[2],L_EYE[3],L_FUR), (R_EYE[0],R_EYE[1],R_EYE[2],R_EYE[3],R_FUR)]:
    img = fur_patch(img, cx, cy, rx, ry, fur)
img = heart(img, L_EYE[0], L_EYE[1], 13)
img = heart(img, R_EYE[0], R_EYE[1], 13)
save(img, "expr_love.png")

# 8) angry 生气（保留眼睛 + 斜眉毛）
img = base.copy()
# 左眉：内低外高
draw_line(img, 330, 46, 378, 58, width=6)
draw_line(img, 332, 44, 330, 50, width=6)
# 右眉
draw_line(img, 500, 122, 452, 136, width=6)
draw_line(img, 498, 120, 500, 126, width=6)
save(img, "expr_angry.png")

print("done")
