src = open(r"work\pet\DesktopPet_v2b.cs", "r", encoding="utf-8-sig").read()
import re
for m in ["UpdateExpressionAndBlink", "_clickCount"]:
    print(f"=== {m} ===")
    for i, line in enumerate(src.split("\n"), 1):
        if m in line:
            print(f"  行{i}: {line.strip()[:100]}")
