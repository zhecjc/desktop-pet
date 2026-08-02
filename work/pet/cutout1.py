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

# 1) LoadCharacterFromFolder：支持多格式 + 自动抠图
rep("""                string cPath = Path.Combine(dir, "character.png");
                if (!File.Exists(cPath)) return false;
                Bitmap c = new Bitmap(cPath);
                _char = c;
                _charW = c.Width;
                _charH = c.Height;
                _pose1 = TryLoadBitmap(Path.Combine(dir, "pose1.png"));
                _pose2 = TryLoadBitmap(Path.Combine(dir, "pose2.png"));""",
    """                string cPath = FindImage(dir, "character");
                if (cPath == null) return false;
                Bitmap c = PrepareCharacterImage(cPath);
                if (c == null) return false;
                _char = c;
                _charW = c.Width;
                _charH = c.Height;
                string p1 = FindImage(dir, "pose1");
                string p2 = FindImage(dir, "pose2");
                _pose1 = (p1 != null) ? PrepareCharacterImage(p1) : null;
                _pose2 = (p2 != null) ? PrepareCharacterImage(p2) : null;""", "loadcharfolder")

# 2) ApplySavedCharacter
rep("""                if (Directory.Exists(dir) && File.Exists(Path.Combine(dir, "character.png")))""",
    """                if (Directory.Exists(dir) && FindImage(dir, "character") != null)""", "applysaved")

# 3) RefreshCharacterMenu
rep("""                        if (!File.Exists(Path.Combine(dir, "character.png"))) continue;""",
    """                        if (FindImage(dir, "character") == null) continue;""", "menuscan")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("STEP A done, len:", len(src))
