# -*- coding: utf-8 -*-
import sys

def read(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8-sig") as f:
        f.write(s)

src = read(r"work\pet\DesktopPet_v2b.cs")

def rep(frm, to, label):
    global src
    n = src.count(frm)
    if n != 1:
        print(f"FAIL {label}: count={n}")
        sys.exit(1)
    src = src.replace(frm, to)
    print(f"OK   {label}")

# R11: idle sway revert
rep("""            if (_anim == "idle" || !IsAnimating())
            {
                double ms = DateTime.UtcNow.TimeOfDay.TotalMilliseconds;
                double t1 = ms / 1600.0 * 2.0 * Math.PI;
                double t2 = ms / 2400.0 * 2.0 * Math.PI;
                double t3 = ms / 3700.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.018 * Math.Sin(t1));
                p.rot = (float)(1.2 * Math.Sin(t2));
                p.ox = (float)(1.8 * Math.Sin(t3));
                return p;
            }""",
    """            if (_anim == "idle" || !IsAnimating())
            {
                double t = DateTime.UtcNow.Millisecond / 1600.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.018 * Math.Sin(t));
                return p;
            }""", "idle sway")

# R12: OnTick
rep("""            UpdateExpressionAndBlink();

            if (!IsAnimating() && DateTime.UtcNow >= _idleNextAt)""",
    "            if (!IsAnimating() && DateTime.UtcNow >= _idleNextAt)", "ontick")

# R13: angry logic
rep("""        private void TriggerRandomInteraction()
        {
            DateTime now = DateTime.UtcNow;
            if (now > _clickWindow) _clickCount = 0;
            _clickWindow = now.AddSeconds(2);
            _clickCount++;
            if (_clickCount >= 4)
            {
                _clickCount = 0;
                _angryUntil = now.AddMilliseconds(2500);
                ShowBubble("再戳我就要生气啦！(｀へ´)");
                StartAnim("shake", 900, "bang", 500);
                return;
            }

            int r = _rng.Next(6);""",
    """        private void TriggerRandomInteraction()
        {
            int r = _rng.Next(6);""", "angry")

# R14: drop _exprUntil
rep("""                    _effect = "heart";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 700;
                    _exprUntil = DateTime.UtcNow.AddMilliseconds(900);""",
    """                    _effect = "heart";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 700;""", "drop")

# R15: remove methods block (LoadExpressions .. SmoothPose)
start_marker = "        private void LoadExpressions()"
end_marker = "        // ---------------- 交互 ----------------"
i1 = src.find(start_marker)
i2 = src.find(end_marker)
if i1 < 0 or i2 < 0 or i2 <= i1:
    print(f"FAIL methods block: i1={i1} i2={i2}")
    sys.exit(1)
# 移除 start_marker 到 end_marker 之前的内容（含前面的空行）
block_start = src.rfind("\n\n", 0, i1)
src = src[:block_start+1] + src[i2:]
print("OK   methods block removed")

# R16: selftest expr loop
rep("""            string[] exprs = new string[] { "normal", "blink", "happy", "sleepy", "shocked", "sad", "wink", "love", "angry" };
            foreach (string e in exprs)
            {
                f._anim = "idle";
                f._animStart = DateTime.UtcNow.AddDays(-1);
                f._animDur = 1;
                f._effect = "";
                f._expr = e;
                f.SaveFrame(System.IO.Path.Combine(outDir, "expr_" + e + ".png"));
            }
""", "", "expr loop")

write(r"work\pet\DesktopPet_v2b.cs", src)
print("PART2 done, len:", len(src))
