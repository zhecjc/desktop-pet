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

methods_block = r"""
        private void LoadPhrases()
        {
            List<string> tap = new List<string>();
            List<string> pose = new List<string>();
            List<string> idle = new List<string>();
            List<string> drop = new List<string>();
            List<string> happy = new List<string>();
            List<string> sad = new List<string>();
            bool hasTap = false, hasPose = false, hasIdle = false, hasDrop = false, hasHappy = false, hasSad = false;
            try
            {
                if (File.Exists(_phrasesPath))
                {
                    string text = DecodeText(File.ReadAllBytes(_phrasesPath));
                    string current = "tap";
                    string[] lines = text.Split(new char[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                    foreach (string raw in lines)
                    {
                        string line = raw.Trim();
                        if (line.Length == 0 || line.StartsWith("#") || line.StartsWith("//")) continue;
                        if (line.StartsWith("["))
                        {
                            int close = line.IndexOf(']');
                            if (close > 0)
                            {
                                string tag = line.Substring(1, close - 1).Trim().ToLowerInvariant();
                                switch (tag)
                                {
                                    case "点击": case "tap": current = "tap"; hasTap = true; break;
                                    case "姿势": case "pose": current = "pose"; hasPose = true; break;
                                    case "发呆": case "idle": current = "idle"; hasIdle = true; break;
                                    case "放下": case "drop": current = "drop"; hasDrop = true; break;
                                    case "开心": case "happy": current = "happy"; hasHappy = true; break;
                                    case "委屈": case "sad": current = "sad"; hasSad = true; break;
                                }
                            }
                            continue;
                        }
                        switch (current)
                        {
                            case "pose": pose.Add(line); break;
                            case "idle": idle.Add(line); break;
                            case "drop": drop.Add(line); break;
                            case "happy": happy.Add(line); break;
                            case "sad": sad.Add(line); break;
                            default: tap.Add(line); break;
                        }
                    }
                }
            }
            catch { }
            if (hasTap && tap.Count > 0) _tapPhrases = tap; else _tapPhrases = new List<string>(DefaultTap);
            if (hasPose && pose.Count > 0) _posePhrases = pose; else _posePhrases = new List<string>(DefaultPose);
            if (hasIdle && idle.Count > 0) _idlePhrases = idle; else _idlePhrases = new List<string>(DefaultIdle);
            if (hasDrop && drop.Count > 0) _dropPhrases = drop; else _dropPhrases = new List<string>(DefaultDrop);
            if (hasHappy && happy.Count > 0) _happyPhrases = happy; else _happyPhrases = new List<string>(DefaultHappy);
            if (hasSad && sad.Count > 0) _sadPhrases = sad; else _sadPhrases = new List<string>(DefaultSad);
        }

        private static string DecodeText(byte[] bytes)
        {
            try
            {
                return new System.Text.UTF8Encoding(false, true).GetString(bytes);
            }
            catch
            {
                try { return System.Text.Encoding.GetEncoding(936).GetString(bytes); }
                catch { return System.Text.Encoding.Default.GetString(bytes); }
            }
        }

        private static string DefaultPhrasesText()
        {
            System.Text.StringBuilder sb = new System.Text.StringBuilder();
            sb.AppendLine("# 桌宠台词文件：一行一句");
            sb.AppendLine("# 用 [点击] [姿势] [发呆] [放下] [开心] [委屈] 分段，不带标签的默认归入[点击]");
            sb.AppendLine();
            sb.AppendLine("[点击]");
            foreach (string s in DefaultTap) sb.AppendLine(s);
            sb.AppendLine();
            sb.AppendLine("[姿势]");
            foreach (string s in DefaultPose) sb.AppendLine(s);
            sb.AppendLine();
            sb.AppendLine("[发呆]");
            foreach (string s in DefaultIdle) sb.AppendLine(s);
            sb.AppendLine();
            sb.AppendLine("[放下]");
            foreach (string s in DefaultDrop) sb.AppendLine(s);
            sb.AppendLine();
            sb.AppendLine("[开心]");
            foreach (string s in DefaultHappy) sb.AppendLine(s);
            sb.AppendLine();
            sb.AppendLine("[委屈]");
            foreach (string s in DefaultSad) sb.AppendLine(s);
            return sb.ToString();
        }

        private void OpenPhrasesEditor()
        {
            try
            {
                if (!File.Exists(_phrasesPath))
                {
                    File.WriteAllText(_phrasesPath, DefaultPhrasesText(), new System.Text.UTF8Encoding(true));
                }
                System.Diagnostics.Process.Start("notepad.exe", "\"" + _phrasesPath + "\"");
            }
            catch { }
        }

        private bool IsAutoStartEnabled()
        {
            try
            {
                using (Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey("Software\\Microsoft\\Windows\\CurrentVersion\\Run"))
                {
                    if (key == null) return false;
                    return key.GetValue("DesktopPet") != null;
                }
            }
            catch { return false; }
        }

        private void SetAutoStart(bool enable)
        {
            try
            {
                using (Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey("Software\\Microsoft\\Windows\\CurrentVersion\\Run", true))
                {
                    if (key == null) return;
                    if (enable)
                    {
                        key.SetValue("DesktopPet", "\"" + Application.ExecutablePath + "\"");
                    }
                    else
                    {
                        key.DeleteValue("DesktopPet", false);
                    }
                }
            }
            catch { }
        }

        private void ApplySavedCharacter()
        {
            if (_charName.Length == 0) return;
            try
            {
                string charsRoot = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "characters");
                string dir = Path.Combine(charsRoot, _charName);
                if (Directory.Exists(dir) && File.Exists(Path.Combine(dir, "character.png")))
                {
                    LoadCharacterFromFolder(dir, false);
                }
            }
            catch { }
        }

        private bool LoadCharacterFromFolder(string dir, bool announce)
        {
            try
            {
                string cPath = Path.Combine(dir, "character.png");
                if (!File.Exists(cPath)) return false;
                Bitmap c = new Bitmap(cPath);
                _char = c;
                _charW = c.Width;
                _charH = c.Height;
                _pose1 = TryLoadBitmap(Path.Combine(dir, "pose1.png"));
                _pose2 = TryLoadBitmap(Path.Combine(dir, "pose2.png"));
                _charDir = dir;
                _charName = Path.GetFileName(dir);
                ApplyScale(_scale, false);
                SaveSettings();
                if (announce) ShowBubble("已切换角色：" + _charName);
                RenderFrame();
                return true;
            }
            catch { return false; }
        }

        private void UseBuiltinCharacter()
        {
            _charDir = "";
            _charName = "";
            LoadCharacter();
            ApplyScale(_scale, false);
            SaveSettings();
            ShowBubble("已切换回内置角色");
            RenderFrame();
        }

        private static Bitmap TryLoadBitmap(string path)
        {
            try
            {
                if (File.Exists(path)) return new Bitmap(path);
            }
            catch { }
            return null;
        }

        private void RefreshCharacterMenu()
        {
            if (_miCharacters == null) return;
            _miCharacters.DropDownItems.Clear();
            ToolStripMenuItem miBuiltin = new ToolStripMenuItem("内置默认", null, delegate { UseBuiltinCharacter(); });
            miBuiltin.Checked = (_charDir.Length == 0);
            _miCharacters.DropDownItems.Add(miBuiltin);
            try
            {
                string charsRoot = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "characters");
                if (Directory.Exists(charsRoot))
                {
                    foreach (string dir in Directory.GetDirectories(charsRoot))
                    {
                        if (!File.Exists(Path.Combine(dir, "character.png"))) continue;
                        string name = Path.GetFileName(dir);
                        ToolStripMenuItem mi = new ToolStripMenuItem(name, null, delegate { LoadCharacterFromFolder(dir, true); });
                        mi.Checked = (string.Compare(_charDir, dir, StringComparison.OrdinalIgnoreCase) == 0);
                        _miCharacters.DropDownItems.Add(mi);
                    }
                }
            }
            catch { }
        }

        private void StartPomodoro()
        {
            _pomoActive = true;
            _pomoIsRest = false;
            _pomoEnd = DateTime.UtcNow.AddMinutes(25);
            ShowBubble("番茄钟：专注 25 分钟开始！加油鸭！");
            StartAnim("nod", 800, "talk", 700);
        }

        private void StartRest()
        {
            _pomoActive = true;
            _pomoIsRest = true;
            _pomoEnd = DateTime.UtcNow.AddMinutes(5);
            ShowBubble("休息 5 分钟，起来活动一下～");
            StartAnim("stretch", 1300, "zzz", 900);
        }

        private void StopPomodoro()
        {
            if (_pomoActive)
            {
                _pomoActive = false;
                ShowBubble("计时已停止");
            }
        }

        private void TickPomodoro()
        {
            if (!_pomoActive) return;
            if (DateTime.UtcNow < _pomoEnd) return;
            if (_pomoIsRest)
            {
                _pomoActive = false;
                ShowBubble("休息结束！继续加油！");
                StartAnim("stretch", 1300, "zzz", 900);
            }
            else
            {
                ShowBubble("番茄钟到啦！站起来活动一下吧～");
                StartAnim("stretch", 1300, "zzz", 900);
                _pomoActive = true;
                _pomoIsRest = true;
                _pomoEnd = DateTime.UtcNow.AddMinutes(5);
            }
        }

        private void AddMood(int delta)
        {
            _mood = Math.Max(0, Math.Min(100, _mood + delta));
        }

        private string MoodLabel()
        {
            if (_mood >= 75) return "开心";
            if (_mood >= 45) return "不错";
            if (_mood >= 25) return "困倦";
            return "委屈";
        }

        private void TickWander()
        {
            DateTime now = DateTime.UtcNow;
            if (!_wanderEnabled || _mouseDown || _dragging || IsAnimating())
            {
                if (_mouseDown || _dragging) _wanderTarget = null;
                _waddling = false;
                return;
            }
            if (_wanderTarget.HasValue)
            {
                Point cur = Location;
                Point tgt = _wanderTarget.Value;
                double dx = tgt.X - cur.X;
                double dy = tgt.Y - cur.Y;
                double dist = Math.Sqrt(dx * dx + dy * dy);
                if (dist < 3.0)
                {
                    _wanderTarget = null;
                    _waddling = false;
                    _wanderNextAt = now.AddMilliseconds(_rng.Next(18000, 45000));
                }
                else
                {
                    double step = Math.Min(dist, 3.2);
                    int nx = (int)Math.Round(cur.X + dx / dist * step);
                    int ny = (int)Math.Round(cur.Y + dy / dist * step);
                    Location = new Point(nx, ny);
                    _waddling = true;
                    _waddlePhase = now.TimeOfDay.TotalMilliseconds / 260.0 * 2.0 * Math.PI;
                    if (_rng.Next(150) == 0) ShowBubble(_idlePhrases[_rng.Next(_idlePhrases.Count)]);
                }
            }
            else if (now >= _wanderNextAt)
            {
                Rectangle wa = Screen.FromPoint(Location).WorkingArea;
                int w = ClientSize.Width;
                int h = ClientSize.Height;
                int tx = wa.X + 30 + _rng.Next(Math.Max(1, wa.Width - w - 60));
                int ty = wa.Y + 30 + _rng.Next(Math.Max(1, wa.Height - h - 60));
                _wanderTarget = new Point(tx, ty);
            }
        }

        private void ApplyScale(double newScale, bool anchorAtCursor)"""

rep("""        private void ApplyScale(double newScale, bool anchorAtCursor)""",
    methods_block, "methods")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("STEP3 done, len:", len(src))
