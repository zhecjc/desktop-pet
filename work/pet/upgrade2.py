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

# 构造函数：台词路径、加载台词、角色、定时器
rep("""            _settingsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "DesktopPet", "pet.ini");
            LoadCharacter();
            LoadSettings();
            ApplyScale(_scale, false);""",
    """            _settingsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "DesktopPet", "pet.ini");
            _phrasesPath = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "台词.txt");
            LoadPhrases();
            LoadCharacter();
            LoadSettings();
            ApplySavedCharacter();
            ApplyScale(_scale, false);
            _moodDecayAt = DateTime.UtcNow;
            _wanderNextAt = DateTime.UtcNow.AddMilliseconds(12000);""", "ctor")

# LoadSettings 增加 char/wander
rep("""                        else if (line.StartsWith("topmost="))
                        {
                            _topmost = line.Substring(8).Trim() == "1";
                        }""",
    """                        else if (line.StartsWith("topmost="))
                        {
                            _topmost = line.Substring(8).Trim() == "1";
                        }
                        else if (line.StartsWith("char="))
                        {
                            _charName = line.Substring(5).Trim();
                        }
                        else if (line.StartsWith("wander="))
                        {
                            _wanderEnabled = line.Substring(7).Trim() == "1";
                        }""", "loadsettings")

# SaveSettings 增加 char/wander
rep("""                string s = "scale=" + _scale.ToString("0.00", CultureInfo.InvariantCulture) + "\\r\\n" +
                           "topmost=" + (_topmost ? "1" : "0") + "\\r\\n";
                File.WriteAllText(_settingsPath, s);""",
    """                string s = "scale=" + _scale.ToString("0.00", CultureInfo.InvariantCulture) + "\\r\\n" +
                           "topmost=" + (_topmost ? "1" : "0") + "\\r\\n" +
                           "char=" + _charName + "\\r\\n" +
                           "wander=" + (_wanderEnabled ? "1" : "0") + "\\r\\n";
                File.WriteAllText(_settingsPath, s);""", "savesettings")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("STEP2 done, len:", len(src))
