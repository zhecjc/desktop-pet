# -*- coding: utf-8 -*-
import sys

src = open(r"work\pet\DesktopPet_v2b.cs", "r", encoding="utf-8-sig").read()

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

with open(r"work\pet\DesktopPet_v2b.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("saved, len:", len(src))
