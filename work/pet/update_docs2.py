# -*- coding: utf-8 -*-
readme = """角色文件夹说明
================

每个子文件夹 = 一个角色，放入图片后即可在右键菜单"切换角色"中看到。

支持格式：character.png / character.jpg / character.jpeg / character.bmp / character.gif
（姿势图同理：pose1.png、pose2.png 也支持这些格式）

  character.png   必填：角色主图
  pose1.png       可选：姿势1
  pose2.png       可选：姿势2

【背景处理】
- 透明背景 PNG：直接用
- 白底 / 纯色背景：程序会自动把背景去掉（边缘柔和处理）
- 复杂照片背景：建议先用其他工具抠成透明 PNG，效果更好

【示例】
把新角色放到：characters\\新角色\\character.png
然后：右键桌宠 -> 切换角色 -> 新角色

图片过大也没关系，程序会自动缩小到合适尺寸。
"""
with open(r"outputs\桌面宠物\characters\角色使用说明.txt", "w", encoding="utf-8-sig") as f:
    f.write(readme)

# 更新主说明中的角色部分
main = open(r"outputs\桌面宠物\使用说明.txt", "r", encoding="utf-8-sig").read()
old = "Q: 想加新角色？\nA: 在 characters 文件夹里新建一个子文件夹，放入 character.png\n   （可选 pose1.png / pose2.png），右键菜单\"切换角色\"里就能选。"
new = "Q: 想加新角色？\nA: 在 characters 文件夹里新建一个子文件夹，放入角色图\n   （character.png 必填，可选 pose1/pose2.png，支持 png/jpg/bmp），\n   右键菜单\"切换角色\"里就能选。\n   白底或纯色背景的图片会自动去背景，不用自己抠图。"
if old in main:
    main = main.replace(old, new)
    with open(r"outputs\桌面宠物\使用说明.txt", "w", encoding="utf-8-sig") as f:
        f.write(main)
    print("docs updated")
else:
    print("main README pattern not found - leaving as is")
