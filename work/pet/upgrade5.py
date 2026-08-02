# -*- coding: utf-8 -*-
import sys

src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()

def rep(frm, to, label):
    global src
    n = src.count(frm)
    if n != 1:
        print(f"FAIL {label}: count={n}")
        sys.exit(1)
    src = src.replace(frm, to)
    print(f"OK   {label}")

# OnTick 集成
rep("""            if (_closing)
            {
                if (_winAlpha > 20) _winAlpha = (byte)(_winAlpha - 25);
                RenderFrame();
                if (_winAlpha <= 20) Close();
                return;
            }

            if (!IsAnimating() && DateTime.UtcNow >= _idleNextAt)""",
    """            if (_closing)
            {
                if (_winAlpha > 20) _winAlpha = (byte)(_winAlpha - 25);
                RenderFrame();
                if (_winAlpha <= 20) Close();
                return;
            }

            TickPomodoro();
            if (DateTime.UtcNow >= _moodDecayAt)
            {
                _moodDecayAt = DateTime.UtcNow.AddSeconds(60);
                AddMood(-1);
            }
            TickWander();

            if (!IsAnimating() && DateTime.UtcNow >= _idleNextAt)""", "ontick")

# StartIdleAction 心情自适应
rep("""            int r = _rng.Next(7);
            switch (r)
            {
                case 0: StartAnim("nod", 800, "", 0); break;
                case 1: StartAnim("stretch", 1300, "zzz", 900); break;
                case 2: StartAnim("look", 1400, "", 0); break;
                case 3: StartAnim("breath", 900, "zzz", 700); break;
                case 4: StartAnim("pose1", 1600, "star", 900); break;
                case 5: StartAnim("pose2", 1600, "star", 900); break;
                default: StartAnim("squash", 700, "poji", 500); break;
            }
            if (_rng.Next(4) == 0)
            {
                ShowBubble(_idlePhrases[_rng.Next(_idlePhrases.Count)]);
            }""",
    """            int r;
            if (_mood >= 75)
            {
                r = _rng.Next(9);
                if (r >= 7) r = 7;
            }
            else if (_mood >= 45)
            {
                r = _rng.Next(7);
            }
            else
            {
                r = _rng.Next(8);
                if (r < 3) r = 3;
                else if (r < 5) r = 1;
            }
            switch (r)
            {
                case 0: StartAnim("nod", 800, "", 0); break;
                case 1: StartAnim("stretch", 1300, "zzz", 900); break;
                case 2: StartAnim("look", 1400, "", 0); break;
                case 3: StartAnim("breath", 900, "zzz", 700); break;
                case 4: StartAnim("pose1", 1600, "star", 900); break;
                case 5: StartAnim("pose2", 1600, "star", 900); break;
                case 6: StartAnim("squash", 700, "poji", 500); break;
                default: StartAnim("talk", 1100, "music", 800); break;
            }
            if (_rng.Next(3) == 0)
            {
                if (_mood >= 75)
                {
                    _effect = "laugh";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 800;
                    ShowBubble(_happyPhrases[_rng.Next(_happyPhrases.Count)]);
                }
                else if (_mood < 25)
                {
                    _effect = "poji";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 800;
                    ShowBubble(_sadPhrases[_rng.Next(_sadPhrases.Count)]);
                }
            }
            else if (_rng.Next(4) == 0)
            {
                ShowBubble(_idlePhrases[_rng.Next(_idlePhrases.Count)]);
            }""", "idleaction")

# 点击加心情
rep("""        private void TriggerRandomInteraction()
        {
            DateTime now = DateTime.UtcNow;""",
    """        private void TriggerRandomInteraction()
        {
            AddMood(8);""", "mood click")
# 检查一下 TriggerRandomInteraction 是否还有 now 引用
src2 = src
i = src2.find("private void TriggerRandomInteraction()")
seg = src2[i:i+300]
if "DateTime now" in seg:
    print("WARN: TriggerRandomInteraction still has DateTime now")
else:
    print("OK: no stray now in TriggerRandomInteraction")

# 放下加心情
rep("""                    _effect = "heart";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 700;""",
    """                    AddMood(4);
                    _effect = "heart";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 700;""", "mood drop")

# 散步摆动（ComputePose idle 分支）
rep("""                double t = DateTime.UtcNow.Millisecond / 1600.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.018 * Math.Sin(t));
                return p;""",
    """                double t = DateTime.UtcNow.Millisecond / 1600.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.018 * Math.Sin(t));
                if (_waddling)
                {
                    p.ox += (float)(3.5 * Math.Sin(_waddlePhase) * (float)_scale);
                    p.rot += (float)(2.5 * Math.Sin(_waddlePhase) * (float)_scale);
                }
                return p;""", "waddle")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("STEP5 done, len:", len(src))
