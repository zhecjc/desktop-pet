from PIL import Image
import numpy as np

# 检查姿势帧 vs 角色帧的差异
for name in ["pose1", "pose2"]:
    frame = Image.open(rf"work\pet\selftest\frame_{name}.png").convert("RGBA")
    idle = Image.open(r"work\pet\selftest\frame_idle.png").convert("RGBA")
    print(f"frame_{name}: size={frame.size}")
    fa, ia = np.array(frame)[...,3], np.array(idle)[...,3]
    print(f"  pose帧不透明bbox: {Image.fromarray(fa>128).getbbox()}")
    diff = (np.abs(np.array(frame).astype(int) - np.array(idle).astype(int))).sum()
    print(f"  与idle帧差异: {diff}")
    # 主色
    rgb = np.array(frame.convert("RGB"))[fa>128]
    if len(rgb):
        from collections import Counter
        c = Counter([tuple(p//32*32 for p in q) for q in rgb[::3]])
        print("  主色:", c.most_common(3))

# 生成姿势预览图（把角色和两个姿势放在一起，供用户查看）
char = Image.open(r"work\pet\character.png").convert("RGBA")
p1 = Image.open(r"work\pet\poses\pose1.png").convert("RGBA")
p2 = Image.open(r"work\pet\poses\pose2.png").convert("RGBA")
# 统一高度 300
def to_h(im, h):
    r = h / im.size[1]
    return im.resize((max(1,int(im.size[0]*r)), h), Image.LANCZOS)
ch = to_h(char, 300); a = to_h(p1, 300); b = to_h(p2, 300)
pad = 20
W = ch.size[0] + a.size[0] + b.size[0] + pad*4
H = 300 + pad*2 + 40
sheet = Image.new("RGBA", (W, H), (250,250,252,255))
sheet.paste(ch, (pad, pad), ch)
sheet.paste(a, (pad*2+ch.size[0], pad), a)
sheet.paste(b, (pad*3+ch.size[0]+a.size[0], pad), b)
from PIL import ImageDraw, ImageFont
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("msyh.ttc", 22)
except Exception:
    font = ImageFont.load_default()
d.text((pad, H-34), "普通", fill=(60,60,80), font=font)
d.text((pad*2+ch.size[0], H-34), "姿势1", fill=(60,60,80), font=font)
d.text((pad*3+ch.size[0]+a.size[0], H-34), "姿势2", fill=(60,60,80), font=font)
sheet.convert("RGB").save(r"work\pet\poses_preview.png")
print("preview saved:", sheet.size)
