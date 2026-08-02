from PIL import Image, ImageDraw, ImageFont
import os

# 1) 复制透明角色图
src = Image.open(r"work\pet\character.png")
src.save(r"outputs\桌面宠物\角色透明图.png")
print("角色透明图 saved")

# 2) 生成综合预览图：角色抠图 + 各动画帧
out_dir = r"work\pet\selftest"
frames = ["frame_idle.png", "frame_jump.png", "frame_squash.png", "frame_shake.png", "frame_spin.png", "frame_nod.png", "frame_stretch.png"]
frame_imgs = []
for f in frames:
    im = Image.open(os.path.join(out_dir, f))
    # 裁剪到内容区域
    im = im.crop(im.split()[3].getbbox())
    frame_imgs.append(im)

# 统一的帧尺寸（缩放到高度 220）
th = 220
scaled = []
for im in frame_imgs:
    ratio = th / im.size[1]
    scaled.append(im.resize((max(1, int(im.size[0] * ratio)), th), Image.LANCZOS))

# 角色原图预览（棋盘格）
check = Image.new("RGB", (602, 600), (255, 255, 255))
cell = 24
px = check.load()
for y in range(600):
    for x in range(602):
        if ((x // cell) + (y // cell)) % 2 == 0:
            px[x, y] = (230, 230, 230)
check.paste(src, (0, 0), src)
src_small = check.resize((220, 219), Image.LANCZOS)

# 拼版：标题行 + 帧
padding = 12
frame_w = max(im.size[0] for im in scaled)
total_w = max(frame_w * 4 + padding * 5, 920)
rows = [scaled[i:i+4] for i in range(0, len(scaled), 4)]
row_h = max(im.size[1] for im in scaled) + 4

title_h = 46
canvas_h = title_h + row_h * len(rows) + padding * (len(rows) + 2)
canvas = Image.new("RGB", (total_w, canvas_h), (245, 245, 250))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("msyh.ttc", 26)
except Exception:
    font = ImageFont.load_default()
d.text((padding, 8), "桌宠动画帧预览（自检渲染）", fill=(60, 60, 80), font=font)

y = title_h + padding
for row in rows:
    x = padding
    for im in row:
        canvas.paste(im, (x, y), im)
        x += frame_w + padding
    y += row_h + padding
canvas.save(r"outputs\桌面宠物\效果预览.png")
print("效果预览 saved", canvas.size)

# 3) 气泡预览
bub = Image.open(os.path.join(out_dir, "bubble.png"))
bub.save(r"outputs\桌面宠物\气泡样式.png")
print("气泡样式 saved")
