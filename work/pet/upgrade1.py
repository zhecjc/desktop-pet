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

# 1) usings
rep("using System;\nusing System.Drawing;",
    "using System;\nusing System.Collections.Generic;\nusing System.Diagnostics;\nusing System.Drawing;", "usings")

# 2) 字段
rep("""        private string _settingsPath;
        private Bitmap _pose1;
        private Bitmap _pose2;
        private string _poseImg = "";""",
    """        private string _settingsPath;
        private Bitmap _pose1;
        private Bitmap _pose2;
        private string _poseImg = "";
        private string _charName = "";
        private string _charDir = "";
        private bool _pomoActive;
        private DateTime _pomoEnd;
        private bool _pomoIsRest;
        private int _mood = 60;
        private DateTime _moodDecayAt;
        private List<string> _tapPhrases;
        private List<string> _posePhrases;
        private List<string> _idlePhrases;
        private List<string> _dropPhrases;
        private List<string> _happyPhrases;
        private List<string> _sadPhrases;
        private string _phrasesPath;
        private bool _wanderEnabled = true;
        private Point? _wanderTarget;
        private DateTime _wanderNextAt;
        private double _waddlePhase;
        private bool _waddling;
        private ToolStripMenuItem _miCharacters;
        private ToolStripMenuItem _miMood;
        private ToolStripMenuItem _miWander;
        private ToolStripMenuItem _miAutoStart;""", "fields")

# 3) 静态默认台词改名 + 增加开心/委屈
rep("        private static readonly string[] TapPhrases = new string[]",
    "        private static readonly string[] DefaultTap = new string[]", "tapname")
rep("        private static readonly string[] PosePhrases = new string[]",
    "        private static readonly string[] DefaultPose = new string[]", "posename")
rep("        private static readonly string[] IdlePhrases = new string[]",
    "        private static readonly string[] DefaultIdle = new string[]", "idlename")
rep("        private static readonly string[] DropPhrases = new string[]",
    "        private static readonly string[] DefaultDrop = new string[]", "dropname")
rep("""            "呼，站稳了～",
        };

        public PetForm()""",
    """            "呼，站稳了～",
        };

        private static readonly string[] DefaultHappy = new string[]
        {
            "今天超开心！嘿嘿～",
            "心情美滋滋！",
            "最喜欢你啦！",
            "元气满满！冲鸭！",
        };

        private static readonly string[] DefaultSad = new string[]
        {
            "有点难过…",
            "呜呜…被冷落了…",
            "心情低落的喵…",
            "求摸摸头…",
        };

        public PetForm()""", "happy sad defaults")

# 4) 台词使用处改为实例列表
rep("        private string _phrasesPath;", "        private string _phrasesPath;", "anchor-check")
rep("ShowBubble(PosePhrases[_rng.Next(PosePhrases.Length)]);",
    "ShowBubble(_posePhrases[_rng.Next(_posePhrases.Count)]);", "usepose")
rep("ShowBubble(TapPhrases[_rng.Next(TapPhrases.Length)]);",
    "ShowBubble(_tapPhrases[_rng.Next(_tapPhrases.Count)]);", "usetap")
rep("ShowBubble(IdlePhrases[_rng.Next(IdlePhrases.Length)]);",
    "ShowBubble(_idlePhrases[_rng.Next(_idlePhrases.Count)]);", "useidle")
rep("ShowBubble(DropPhrases[_rng.Next(DropPhrases.Length)]);",
    "ShowBubble(_dropPhrases[_rng.Next(_dropPhrases.Count)]);", "usedrop")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("STEP1 done, len:", len(src))
