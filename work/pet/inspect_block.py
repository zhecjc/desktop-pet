src = open(r"work\pet\DesktopPet_v2b.cs", "r", encoding="utf-8-sig").read()
i1 = src.find("        private void LoadExpressions()")
print("i1:", i1)
# 打印从 i1 开始的 3000 字符
print(src[i1:i1+3200])
