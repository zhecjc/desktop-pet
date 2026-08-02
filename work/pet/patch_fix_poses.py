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

# F1: Main - 新互斥名 + 自动关闭旧版本
rep("""            bool createdNew;
            using (new System.Threading.Mutex(true, "DesktopPet_SingleInstance_zh", out createdNew))
            {
                if (!createdNew) return;
                Native.SetProcessDPIAware();""",
    """            bool createdNew;
            using (new System.Threading.Mutex(true, "DesktopPet_SingleInstance_v3", out createdNew))
            {
                if (!createdNew) return;
                try
                {
                    foreach (System.Diagnostics.Process p in System.Diagnostics.Process.GetProcessesByName("桌宠"))
                    {
                        if (p.Id != System.Diagnostics.Process.GetCurrentProcess().Id)
                        {
                            try { p.Kill(); } catch { }
                        }
                    }
                }
                catch { }
                Native.SetProcessDPIAware();""", "main-upgrade")

# F2: 互动池 - 姿势权重提高（4/9）+ 时长 1800ms
rep("""            int r = _rng.Next(7);
            switch (r)
            {
                case 0: StartAnim("jump", 900, "bang", 500); break;
                case 1: StartAnim("squash", 750, "poji", 600); break;
                case 2: StartAnim("shake", 750, "laugh", 700); break;
                case 3: StartAnim("pose1", 1600, "star", 1000); break;
                case 4: StartAnim("pose2", 1600, "music", 1000); break;
                case 5: StartAnim("nod", 800, "talk", 700); break;
                default: StartAnim("talk", 1100, "music", 800); break;
            }""",
    """            int r = _rng.Next(9);
            switch (r)
            {
                case 0: StartAnim("jump", 900, "bang", 500); break;
                case 1: StartAnim("squash", 750, "poji", 600); break;
                case 2: StartAnim("shake", 750, "laugh", 700); break;
                case 3: StartAnim("pose1", 1800, "star", 1100); break;
                case 4: StartAnim("pose2", 1800, "star", 1100); break;
                case 5: StartAnim("pose1", 1800, "star", 1100); break;
                case 6: StartAnim("pose2", 1800, "star", 1100); break;
                case 7: StartAnim("nod", 800, "talk", 700); break;
                default: StartAnim("talk", 1100, "music", 800); break;
            }""", "interactions")

# F3: 空闲动作也偶尔摆姿势
rep("""            int r = _rng.Next(5);
            switch (r)
            {
                case 0: StartAnim("nod", 800, "", 0); break;
                case 1: StartAnim("stretch", 1300, "zzz", 900); break;
                case 2: StartAnim("look", 1400, "", 0); break;
                case 3: StartAnim("breath", 900, "zzz", 700); break;
                default: StartAnim("squash", 700, "poji", 500); break;
            }""",
    """            int r = _rng.Next(7);
            switch (r)
            {
                case 0: StartAnim("nod", 800, "", 0); break;
                case 1: StartAnim("stretch", 1300, "zzz", 900); break;
                case 2: StartAnim("look", 1400, "", 0); break;
                case 3: StartAnim("breath", 900, "zzz", 700); break;
                case 4: StartAnim("pose1", 1600, "star", 900); break;
                case 5: StartAnim("pose2", 1600, "star", 900); break;
                default: StartAnim("squash", 700, "poji", 500); break;
            }""", "idle poses")

# F4: 姿势动画 - 弹入效果 + 呼吸/摇摆（合并两个分支）
rep("""            else if (_anim == "pose1")
            {
                double t = DateTime.UtcNow.TimeOfDay.TotalMilliseconds / 900.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.02 * Math.Sin(t));
                p.oy = (float)(-2.0 * Math.Sin(t) * (float)_scale);
            }
            else if (_anim == "pose2")
            {
                double t = DateTime.UtcNow.TimeOfDay.TotalMilliseconds / 1100.0 * 2.0 * Math.PI;
                p.rot = (float)(2.0 * Math.Sin(t));
                p.oy = (float)(-1.5 * Math.Sin(t * 2) * (float)_scale);
            }
            return p;""",
    """            else if (_anim == "pose1" || _anim == "pose2")
            {
                double tt = DateTime.UtcNow.TimeOfDay.TotalMilliseconds;
                double pop = 1.0;
                if (k < 0.22) pop = 1.0 + 0.14 * Math.Sin(Math.PI * (k / 0.22));
                p.sy = (float)(pop * (1.0 + 0.02 * Math.Sin(tt / 900.0 * 2.0 * Math.PI)));
                if (_anim == "pose2")
                {
                    p.rot = (float)(2.0 * Math.Sin(tt / 1100.0 * 2.0 * Math.PI));
                    p.oy = (float)(-1.5 * Math.Sin(tt / 550.0 * 2.0 * Math.PI) * (float)_scale);
                }
                else
                {
                    p.oy = (float)(-2.0 * Math.Sin(tt / 900.0 * 2.0 * Math.PI) * (float)_scale);
                }
            }
            return p;""", "pose anim")

# F5: 自检 - 设置 _poseImg
rep("""                f._anim = a;
                f._animStart = DateTime.UtcNow;
                f._animDur = 600;
                f._effect = "star";
                f._effectStart = DateTime.UtcNow;
                f._effectDur = 500;
                f.SaveFrame(System.IO.Path.Combine(outDir, "frame_" + a + ".png"));""",
    """                f._anim = a;
                f._animStart = DateTime.UtcNow;
                f._animDur = 600;
                f._poseImg = (a == "pose1" || a == "pose2") ? a : "";
                f._effect = "star";
                f._effectStart = DateTime.UtcNow;
                f._effectDur = 500;
                f.SaveFrame(System.IO.Path.Combine(outDir, "frame_" + a + ".png"));""", "selftest pose")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("saved F1-F5, len:", len(src))
