# -*- coding: utf-8 -*-
src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()
frm = """                    using (SolidBrush b = new SolidBrush(Color.Red))
                    {
                        g.FillEllipse(b, 40, 40, 120, 120);
                    }"""
to = """                    using (SolidBrush brush = new SolidBrush(Color.Red))
                    {
                        g.FillEllipse(brush, 40, 40, 120, 120);
                    }"""
n = src.count(frm)
print("match:", n)
if n == 1:
    src = src.replace(frm, to)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("renamed brush")
else:
    print("FAIL")
