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

# P1: 字段
rep("""        private string _settingsPath;
""",
    """        private string _settingsPath;
        private Bitmap _pose1;
        private Bitmap _pose2;
        private string _poseImg = "";
""", "fields")

# P2: LoadCharacter 末尾加载姿势
rep("""            _charW = 200;
            _charH = 200;
        }

        private void LoadSettings()""",
    """            _charW = 200;
            _charH = 200;
            LoadPoses();
        }

        private void LoadPoses()
        {
            Assembly asm = Assembly.GetExecutingAssembly();
            try
            {
                using (Stream s = asm.GetManifestResourceStream("DesktopPet.pose1.png"))
                {
                    if (s != null) _pose1 = new Bitmap(s);
                }
            }
            catch { }
            try
            {
                using (Stream s = asm.GetManifestResourceStream("DesktopPet.pose2.png"))
                {
                    if (s != null) _pose2 = new Bitmap(s);
                }
            }
            catch { }
        }

        private void LoadSettings()""", "loadposes")

# P3: 互动池（去掉 spin，加入 pose1/pose2）
rep("""            int r = _rng.Next(6);
            switch (r)
            {
                case 0: StartAnim("jump", 900, "bang", 500); break;
                case 1: StartAnim("squash", 750, "poji", 600); break;
                case 2: StartAnim("shake", 750, "laugh", 700); break;
                case 3: StartAnim("spin", 1050, "star", 900); break;
                case 4: StartAnim("nod", 800, "talk", 700); break;
                default: StartAnim("talk", 1100, "music", 800); break;
            }
            ShowBubble(TapPhrases[_rng.Next(TapPhrases.Length)]);""",
    """            int r = _rng.Next(7);
            switch (r)
            {
                case 0: StartAnim("jump", 900, "bang", 500); break;
                case 1: StartAnim("squash", 750, "poji", 600); break;
                case 2: StartAnim("shake", 750, "laugh", 700); break;
                case 3: StartAnim("pose1", 1600, "star", 1000); break;
                case 4: StartAnim("pose2", 1600, "music", 1000); break;
                case 5: StartAnim("nod", 800, "talk", 700); break;
                default: StartAnim("talk", 1100, "music", 800); break;
            }
            if (_anim == "pose1" || _anim == "pose2")
            {
                ShowBubble(PosePhrases[_rng.Next(PosePhrases.Length)]);
            }
            else
            {
                ShowBubble(TapPhrases[_rng.Next(TapPhrases.Length)]);
            }""", "interactions")

# P4: 姿势台词
rep("""        private static readonly string[] DropPhrases = new string[]
        {""",
    """        private static readonly string[] PosePhrases = new string[]
        {
            "咔嚓！摆个造型～",
            "换个姿势，更好看！",
            "这样够帅吧？",
            "嘿嘿，摆好了！",
        };

        private static readonly string[] DropPhrases = new string[]
        {""", "posephrases")

# P5: StartAnim 设置 _poseImg
rep("""            _anim = name;
            _animStart = DateTime.UtcNow;
            _animDur = durMs;
            if (effect.Length > 0)""",
    """            _anim = name;
            _animStart = DateTime.UtcNow;
            _animDur = durMs;
            _poseImg = (name == "pose1" || name == "pose2") ? name : "";
            if (effect.Length > 0)""", "startanim")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("saved P1-P5, len:", len(src))
