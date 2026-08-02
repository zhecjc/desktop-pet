# -*- coding: utf-8 -*-
"""用 selftest_new 的渲染帧重新生成效果预览（姿势大小统一后）。"""
from PIL import Image
import os

out_dir = r"work\pet\selftest_restored"
frames = ["frame_idle.png", "frame_jump.png", "frame_squash.png", "frame_shake.png",
          "frame_pose1.png", "frame_pose2.png", "frame_nod.png", "frame_stretch.png",
          "frame_talk.png"]
frame_imgs = []
for f in frames:
    im = Image.open(os.path.join(out_dir, f))
    im = im.crop(im.split()[3].getbbox())
    frame_imgs.append(im)

th = 180
scaled = []
for im in frame_imgs:
    ratio = th / im.size[1]
    scaled.append(im.resize((max(1, int(im.size[0] * ratio)), th), Image.LANCZOS))

padding = 10
frame_w = max(im.size[0] for im in scaled)
cols = 5
rows = 2
total_w = frame_w * cols + padding * (cols + 1)
row_h = th + 4
canvas_h = padding * (rows + 1) + row_h * rows
canvas = Image.new("RGB", (total_w, canvas_h), (245, 245, 250))
for i, im in enumerate(scaled):
    r, c = divmod(i, cols)
    x = padding + c * (frame_w + padding)
    yy = padding + r * (row_h + padding)
    canvas.paste(im, (x, yy), im)
canvas.save(r"outputs\桌面宠物\效果预览.png")
print("效果预览 updated:", canvas.size)
