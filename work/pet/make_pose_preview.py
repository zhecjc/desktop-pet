# -*- coding: utf-8 -*-
"""用统一大小后的渲染帧重新生成姿势预览图。"""
from PIL import Image, ImageDraw, ImageFont

out_dir = r"work\pet\selftest_new"
imgs = []
for name in ["idle", "pose1", "pose2"]:
    im = Image.open(out_dir + r"\frame_" + name + ".png").convert("RGBA")
    im = im.crop(im.split()[3].getbbox())
    ratio = 300 / im.size[1]
    im = im.resize((max(1, int(im.size[0] * ratio)), 300), Image.LANCZOS)
    imgs.append(im)

pad = 24
W = sum(im.size[0] for im in imgs) + pad * (len(imgs) + 1)
H = 300 + pad * 2 + 46
sheet = Image.new("RGB", (W, H), (250, 250, 252))
x = pad
for im in imgs:
    sheet.paste(im, (x, pad), im)
    x += im.size[0] + pad

d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("msyh.ttc", 24)
except Exception:
    font = ImageFont.load_default()
labels = ["普通", "姿势1", "姿势2"]
x = pad
for im, label in zip(imgs, labels):
    d.text((x + (im.size[0] - d.textlength(label, font=font)) / 2, H - 40), label,
           fill=(60, 60, 80), font=font)
    x += im.size[0] + pad

sheet.save(r"outputs\桌面宠物\姿势预览.png")
print("姿势预览 updated:", sheet.size)
