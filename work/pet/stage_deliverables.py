# -*- coding: utf-8 -*-
import os, shutil

out = r"outputs\桌面宠物"
# 1) 复制正式 EXE
shutil.copy(r"work\pet\test_pet.exe", os.path.join(out, "桌宠.exe"))

# 1b) 复制豆包问答脚本（桌宠从 exe 同目录调用）
shutil.copy(r"work\pet\ask_doubao.py", os.path.join(out, "ask_doubao.py"))

# 2) 角色文件夹
char_root = os.path.join(out, "characters")
default_char = os.path.join(char_root, "默认角色")
os.makedirs(default_char, exist_ok=True)
shutil.copy(r"work\pet\character.png", os.path.join(default_char, "character.png"))
shutil.copy(r"work\pet\poses\pose1.png", os.path.join(default_char, "pose1.png"))
shutil.copy(r"work\pet\poses\pose2.png", os.path.join(default_char, "pose2.png"))
char_readme = """角色文件夹说明
================

每个子文件夹 = 一个角色，放入以下图片即可在右键菜单"切换角色"中看到：

  character.png   必填：角色主图（透明背景 PNG）
  pose1.png       可选：姿势1
  pose2.png       可选：姿势2

示例：把新角色放到 "characters\\新角色\\character.png"，
然后右键桌宠 -> 切换角色 -> 新角色。

提示：图片最好用透明背景 PNG；如果不是，白色背景也能自动处理
（程序会忽略接近白色的部分）。
"""
with open(os.path.join(char_root, "角色使用说明.txt"), "w", encoding="utf-8-sig") as f:
    f.write(char_readme)

# 3) 默认台词文件
phrases = """# 桌宠台词文件：一行一句
# 用 [点击] [姿势] [发呆] [放下] [开心] [委屈] 分段，不带标签的默认归入[点击]
# 修改后保存，在右键菜单点"重新加载台词"即可生效

[点击]
戳我干嘛呀！(>ω<)
嘿嘿，有点痒～
再戳我就要生气了！(｀へ´)
主人加油鸭！٩(◕‿◕｡)۶
今天也要元气满满哦！
发呆中…勿扰 (-_-)
嘻嘻，被你抓到啦！
陪我玩一会儿嘛～
盯——(◎_◎)
冲鸭！冲鸭！
别摸啦，要害羞了 >///<
叮！专注模式开启 ✧
喵～有什么事吗？
我超可爱的！哼！
偷偷摸鱼被发现了(ﾉ≧∀≦)ﾉ
这里是专心工作的小可爱！

[姿势]
咔嚓！摆个造型～
换个姿势，更好看！
这样够帅吧？
嘿嘿，摆好了！

[发呆]
呼…好安静呀～
这里是我的地盘！
主人加油，我陪着你～
Zzz… 不许吵我…
今天也是美好的一天～

[放下]
放我下来啦！
轻拿轻放！
举高高！再来一次！
呼，站稳了～

[开心]
今天超开心！嘿嘿～
心情美滋滋！
最喜欢你啦！
元气满满！冲鸭！

[委屈]
有点难过…
呜呜…被冷落了…
心情低落的喵…
求摸摸头…
"""
with open(os.path.join(out, "台词.txt"), "w", encoding="utf-8") as f:
    f.write(phrases)
print("deliverables staged")
print("chars folder:", os.listdir(char_root))
