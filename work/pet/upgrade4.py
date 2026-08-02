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

old_buildmenu = """        private void BuildMenu()
        {
            _menu = new ContextMenuStrip();
            _menu.Items.Add("随机互动一下", null, delegate { TriggerRandomInteraction(); });

            ToolStripMenuItem miSize = new ToolStripMenuItem("调整大小");
            double[] sizes = new double[] { 0.5, 0.75, 1.0, 1.25, 1.5, 2.0 };
            _miSizes = new ToolStripMenuItem[sizes.Length];
            for (int i = 0; i < sizes.Length; i++)
            {
                double s = sizes[i];
                _miSizes[i] = new ToolStripMenuItem(PercentText(s), null, delegate { ApplyScale(s, false); });
                miSize.DropDownItems.Add(_miSizes[i]);
            }
            _menu.Items.Add(miSize);

            _miTopmost = new ToolStripMenuItem("置顶显示");
            _miTopmost.Checked = _topmost;
            _miTopmost.Click += delegate
            {
                _topmost = !_topmost;
                _miTopmost.Checked = _topmost;
                TopMost = _topmost;
                if (_bubble != null) _bubble.TopMost = _topmost;
                SaveSettings();
            };
            _menu.Items.Add(_miTopmost);

            _menu.Items.Add(new ToolStripSeparator());
            _menu.Items.Add("退出桌宠", null, delegate { BeginClose(); });
        }"""

new_buildmenu = """        private void BuildMenu()
        {
            _menu = new ContextMenuStrip();
            _menu.Opening += delegate { RefreshMenuState(); };
            _menu.Items.Add("随机互动一下", null, delegate { TriggerRandomInteraction(); });

            ToolStripMenuItem miPomo = new ToolStripMenuItem("番茄钟");
            miPomo.DropDownItems.Add("开始 25 分钟专注", null, delegate { StartPomodoro(); });
            miPomo.DropDownItems.Add("开始 5 分钟休息", null, delegate { StartRest(); });
            miPomo.DropDownItems.Add("停止计时", null, delegate { StopPomodoro(); });
            _menu.Items.Add(miPomo);

            _menu.Items.Add(new ToolStripSeparator());

            _miCharacters = new ToolStripMenuItem("切换角色");
            _menu.Items.Add(_miCharacters);

            ToolStripMenuItem miPhrase = new ToolStripMenuItem("自定义台词");
            miPhrase.Click += delegate { OpenPhrasesEditor(); };
            _menu.Items.Add(miPhrase);

            ToolStripMenuItem miReload = new ToolStripMenuItem("重新加载台词");
            miReload.Click += delegate { LoadPhrases(); ShowBubble("台词已重新加载～"); };
            _menu.Items.Add(miReload);

            _menu.Items.Add(new ToolStripSeparator());

            _miMood = new ToolStripMenuItem("心情：不错");
            _miMood.Enabled = false;
            _menu.Items.Add(_miMood);

            _miWander = new ToolStripMenuItem("自动散步");
            _miWander.Checked = _wanderEnabled;
            _miWander.Click += delegate
            {
                _wanderEnabled = !_wanderEnabled;
                _miWander.Checked = _wanderEnabled;
                if (!_wanderEnabled)
                {
                    _wanderTarget = null;
                    _waddling = false;
                }
                SaveSettings();
            };
            _menu.Items.Add(_miWander);

            _miAutoStart = new ToolStripMenuItem("开机自启");
            _miAutoStart.Checked = IsAutoStartEnabled();
            _miAutoStart.Click += delegate
            {
                bool on = !_miAutoStart.Checked;
                SetAutoStart(on);
                _miAutoStart.Checked = on;
            };
            _menu.Items.Add(_miAutoStart);

            ToolStripMenuItem miSize = new ToolStripMenuItem("调整大小");
            double[] sizes = new double[] { 0.5, 0.75, 1.0, 1.25, 1.5, 2.0 };
            _miSizes = new ToolStripMenuItem[sizes.Length];
            for (int i = 0; i < sizes.Length; i++)
            {
                double s = sizes[i];
                _miSizes[i] = new ToolStripMenuItem(PercentText(s), null, delegate { ApplyScale(s, false); });
                miSize.DropDownItems.Add(_miSizes[i]);
            }
            _menu.Items.Add(miSize);

            _miTopmost = new ToolStripMenuItem("置顶显示");
            _miTopmost.Checked = _topmost;
            _miTopmost.Click += delegate
            {
                _topmost = !_topmost;
                _miTopmost.Checked = _topmost;
                TopMost = _topmost;
                if (_bubble != null) _bubble.TopMost = _topmost;
                SaveSettings();
            };
            _menu.Items.Add(_miTopmost);

            _menu.Items.Add(new ToolStripSeparator());
            _menu.Items.Add("退出桌宠", null, delegate { BeginClose(); });
        }

        private void RefreshMenuState()
        {
            UpdateSizeChecks();
            if (_miMood != null) _miMood.Text = "心情：" + MoodLabel();
            if (_miWander != null) _miWander.Checked = _wanderEnabled;
            if (_miAutoStart != null) _miAutoStart.Checked = IsAutoStartEnabled();
            RefreshCharacterMenu();
        }"""

rep(old_buildmenu, new_buildmenu, "buildmenu")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("STEP4 done, len:", len(src))
