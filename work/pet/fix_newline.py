# -*- coding: utf-8 -*-
import sys

src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()

broken = 'System.IO.File.WriteAllText(pf, "[点击]\n测试台词一号\n测试台词二号\n[姿势]\n姿势台词A\n", new System.Text.UTF8Encoding(true));'
fixed = 'System.IO.File.WriteAllText(pf, "[点击]\\n测试台词一号\\n测试台词二号\\n[姿势]\\n姿势台词A\\n", new System.Text.UTF8Encoding(true));'
n = src.count(broken)
print("broken count:", n)
if n == 1:
    src = src.replace(broken, fixed)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("fixed")
else:
    print("check lines around 1416")
