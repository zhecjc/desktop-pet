# -*- coding: utf-8 -*-
import sys

src = open(r"work\pet\DesktopPet_v2b.cs", "r", encoding="utf-8-sig").read()

start_marker = "        private void LoadExpressions()"
end_marker = "        private void TriggerRandomInteraction()"
i1 = src.find(start_marker)
i2 = src.find(end_marker)
if i1 < 0 or i2 < 0 or i2 <= i1:
    print(f"FAIL: i1={i1} i2={i2}")
    sys.exit(1)
block_start = src.rfind("\n\n", 0, i1)
src = src[:block_start+1] + src[i2:]
print("methods block removed, len:", len(src))

# R16: selftest expr loop
expr_loop = """            string[] exprs = new string[] { "normal", "blink", "happy", "sleepy", "shocked", "sad", "wink", "love", "angry" };
            foreach (string e in exprs)
            {
                f._anim = "idle";
                f._animStart = DateTime.UtcNow.AddDays(-1);
                f._animDur = 1;
                f._effect = "";
                f._expr = e;
                f.SaveFrame(System.IO.Path.Combine(outDir, "expr_" + e + ".png"));
            }
"""
n = src.count(expr_loop)
if n != 1:
    print(f"FAIL expr loop: count={n}")
    sys.exit(1)
src = src.replace(expr_loop, "")
print("expr loop removed, len:", len(src))

with open(r"work\pet\DesktopPet_v2b.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("PART2 done")
