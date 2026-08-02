# -*- coding: utf-8 -*-
import sys

def read(p):
    with open(p, "r", encoding="utf-8-sig") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8-sig") as f:
        f.write(s)

src = read(r"work\pet\DesktopPet.cs")
orig = src

def rep(frm, to, label):
    global src
    n = src.count(frm)
    if n != 1:
        print(f"FAIL {label}: count={n}")
        sys.exit(1)
    src = src.replace(frm, to)
    print(f"OK   {label}")

# R1: remove using
rep("using System.Collections.Generic;\nusing System.Globalization;",
    "using System.Globalization;", "using")
# R2: scale
rep("        private double _scale = 0.5;", "        private double _scale = 1.0;", "scale")
# R3: min scale
rep("        private const double MIN_SCALE = 0.25;", "        private const double MIN_SCALE = 0.30;", "minscale")
# R4: settings file
rep('"DesktopPet", "pet2.ini");', '"DesktopPet", "pet.ini");', "settings")
# R5: remove fields
rep("""        private string _settingsPath;
        private Dictionary<string, Bitmap> _exprs;
        private string _expr = "normal";
        private DateTime _blinkUntil;
        private DateTime _nextBlink;
        private DateTime _angryUntil;
        private DateTime _exprUntil;
        private int _clickCount;
        private DateTime _clickWindow;
        private Pose _display;
        private DateTime _lastFrame;
        private bool _displayInit;""",
    "        private string _settingsPath;", "fields")
# R6: ctor
rep("""            _idleNextAt = DateTime.UtcNow.AddMilliseconds(_rng.Next(8000, 16000));
            _nextBlink = DateTime.UtcNow.AddMilliseconds(2500);
            _clickWindow = DateTime.UtcNow;""",
    "            _idleNextAt = DateTime.UtcNow.AddMilliseconds(_rng.Next(8000, 16000));", "ctor")
# R7: OnShown
rep("""        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            _lastFrame = DateTime.UtcNow;
            _displayInit = false;
            _timer.Start();
            RenderFrame();
        }""",
    """        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            _timer.Start();
            RenderFrame();
        }""", "onshown")
# R8: LoadCharacter
rep("""                        _charW = _char.Width;
                        _charH = _char.Height;
                        LoadExpressions();
                        return;""",
    """                        _charW = _char.Width;
                        _charH = _char.Height;
                        return;""", "loadchar1")
rep("""            _charW = 200;
            _charH = 200;
            LoadExpressions();
        }""",
    """            _charW = 200;
            _charH = 200;
        }""", "loadchar2")
# R9: RenderFrame
rep("""                        Pose p = SmoothPose(ComputePose());
                        DrawPet(g, w, h, p);""",
    """                        Pose p = ComputePose();
                        DrawPet(g, w, h, p);""", "smooth")
# R10: DrawPet
rep("""        private void DrawPet(Graphics g, int w, int h, Pose p)
        {
            Bitmap src = CurrentBase();
            if (src == null) src = _char;
            if (src == null) return;""",
    """        private void DrawPet(Graphics g, int w, int h, Pose p)
        {
            if (_char == null) return;""", "drawpet")
rep("            g.DrawImage(src, new RectangleF(-cw / 2f, -chh, cw, chh));",
    "            g.DrawImage(_char, new RectangleF(-cw / 2f, -chh, cw, chh));", "drawimage")

write(r"work\pet\DesktopPet_v2b.cs", src)
print("PART1 done, len:", len(src))
