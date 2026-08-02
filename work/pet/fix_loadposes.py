# -*- coding: utf-8 -*-
src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()
frm = """                        _charW = _char.Width;
                        _charH = _char.Height;
                        return;"""
to = """                        _charW = _char.Width;
                        _charH = _char.Height;
                        LoadPoses();
                        return;"""
n = src.count(frm)
print("match count:", n)
if n == 1:
    src = src.replace(frm, to)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("fixed: LoadPoses now called on normal path")
else:
    print("FAIL")
