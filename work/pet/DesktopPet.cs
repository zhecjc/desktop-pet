using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Windows.Devices.Geolocation;

namespace DesktopPet
{
    internal static class Native
    {
        [DllImport("user32.dll")]
        public static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr hdcDst, ref POINT pptDst,
            ref SIZE psize, IntPtr hdcSrc, ref POINT pptSrc, int crKey, ref BLENDFUNCTION pblend, int dwFlags);

        [DllImport("user32.dll")]
        public static extern IntPtr GetDC(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);

        [DllImport("gdi32.dll")]
        public static extern IntPtr CreateCompatibleDC(IntPtr hDC);

        [DllImport("gdi32.dll")]
        public static extern bool DeleteDC(IntPtr hdc);

        [DllImport("gdi32.dll")]
        public static extern IntPtr SelectObject(IntPtr hDC, IntPtr hObject);

        [DllImport("gdi32.dll")]
        public static extern bool DeleteObject(IntPtr hObject);

        [DllImport("user32.dll")]
        public static extern int GetWindowLong(IntPtr hWnd, int nIndex);

        [DllImport("user32.dll")]
        public static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);

        [DllImport("user32.dll")]
        public static extern bool SetCapture(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool ReleaseCapture();

        [DllImport("user32.dll")]
        public static extern bool SetProcessDPIAware();

        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr SetWindowsHookEx(int idHook, HookProc lpfn, IntPtr hMod, uint dwThreadId);

        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool UnhookWindowsHookEx(IntPtr hhk);

        [DllImport("user32.dll")]
        public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        public static extern IntPtr GetModuleHandle(string lpModuleName);

        public delegate IntPtr HookProc(int nCode, IntPtr wParam, IntPtr lParam);

        public const int GWL_EXSTYLE = -20;
        public const int WS_EX_LAYERED = 0x00080000;
        public const int WS_EX_TOOLWINDOW = 0x00000080;
        public const int WS_EX_NOACTIVATE = 0x08000000;
        public const int WS_EX_TRANSPARENT = 0x00000020;
        public const int ULW_ALPHA = 0x00000002;
        public const int WH_MOUSE_LL = 14;
        public const int WH_KEYBOARD_LL = 13;
        public const int WM_LBUTTONDOWN = 0x0201;
        public const int WM_RBUTTONDOWN = 0x0204;
        public const int WM_MBUTTONDOWN = 0x0207;
        public const int WM_XBUTTONDOWN = 0x020B;
        public const int WM_KEYDOWN = 0x0100;
        public const int VK_ESCAPE = 0x1B;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct POINT { public int x; public int y; }

    [StructLayout(LayoutKind.Sequential)]
    internal struct SIZE { public int cx; public int cy; }

    [StructLayout(LayoutKind.Sequential, Pack = 1)]
    internal struct BLENDFUNCTION
    {
        public byte BlendOp;
        public byte BlendFlags;
        public byte SourceConstantAlpha;
        public byte AlphaFormat;
    }

    internal static class LayeredPainter
    {
        public static void Push(IntPtr hwnd, Bitmap surface, int windowLeft, int windowTop, byte alpha)
        {
            if (surface == null || hwnd == IntPtr.Zero) return;
            IntPtr hdcScreen = Native.GetDC(IntPtr.Zero);
            IntPtr hdcMem = Native.CreateCompatibleDC(hdcScreen);
            IntPtr hBitmap = IntPtr.Zero;
            try
            {
                hBitmap = surface.GetHbitmap(Color.FromArgb(0));
                IntPtr old = Native.SelectObject(hdcMem, hBitmap);
                POINT ptDst = new POINT();
                ptDst.x = windowLeft;
                ptDst.y = windowTop;
                POINT ptSrc = new POINT();
                ptSrc.x = 0;
                ptSrc.y = 0;
                SIZE size = new SIZE();
                size.cx = surface.Width;
                size.cy = surface.Height;
                BLENDFUNCTION blend = new BLENDFUNCTION();
                blend.BlendOp = 0;
                blend.BlendFlags = 0;
                blend.SourceConstantAlpha = alpha;
                blend.AlphaFormat = 1; // AC_SRC_ALPHA
                LastUpdateOk = Native.UpdateLayeredWindow(hwnd, hdcScreen, ref ptDst, ref size, hdcMem, ref ptSrc, 0, ref blend, Native.ULW_ALPHA);
                Native.SelectObject(hdcMem, old);
            }
            finally
            {
                if (hBitmap != IntPtr.Zero) Native.DeleteObject(hBitmap);
                Native.DeleteDC(hdcMem);
                Native.ReleaseDC(IntPtr.Zero, hdcScreen);
            }
        }

        public static bool LastUpdateOk = false;
    }

    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            string[] args = Environment.GetCommandLineArgs();
            if (args.Length > 1 && args[1] == "/selftest")
            {
                string outDir = (args.Length > 2) ? args[2] : ".";
                PetForm.RunSelfTest(outDir);
                return;
            }
            bool createdNew;
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
                Native.SetProcessDPIAware();
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new PetForm());
            }
        }
    }

    internal class PetForm : Form
    {
        private const double HEADROOM = 0.30;
        private const double MIN_SCALE = 0.30;
        private const double MAX_SCALE = 3.0;

        private Bitmap _char;
        private int _charW;
        private int _charH;
        private double _scale = 1.0;
        private bool _topmost = true;

        private System.Windows.Forms.Timer _timer;
        private Random _rng = new Random();

        private bool _mouseDown;
        private bool _dragging;
        private Point _downScreen;
        private Point _grabOffset;

        private string _anim = "idle";
        private DateTime _animStart;
        private double _animDur = 1.0;
        private DateTime _idleNextAt;
        private string _effect = "";
        private DateTime _effectStart;
        private double _effectDur = 1.0;

        private BubbleForm _bubble;
        private ContextMenuStrip _menu;
        private ToolStripMenuItem _miTopmost;

        private byte _winAlpha = 255;
        private bool _closing;

        private string _settingsPath;
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
        private ToolStripMenuItem _miAutoStart;
        private ToolStripMenuItem _miDrink;
        private ToolStripMenuItem _miSit;
        private ToolStripMenuItem _miDrinkInt;
        private ToolStripMenuItem _miSitInt;
        private ToolStripMenuItem[] _miDrinkInts;
        private ToolStripMenuItem[] _miSitInts;
        private bool _drinkEnabled;
        private bool _sitEnabled;
        private int _drinkIntervalMin = 60;
        private int _sitIntervalMin = 60;
        private DateTime _drinkNextAt;
        private DateTime _sitNextAt;
        private ToolStripMenuItem _miWeather;
        private ToolStripMenuItem[] _miFxItems;
        private bool _weatherBusy;
        private string _cityCode = "";
        private string _cityName = "";
        private bool _cityLocated;
        // 定位诊断（供"定位信息"菜单与日志）
        private string _locateDiag = "";
        private double _locateLat = 0;
        private double _locateLon = 0;
        private bool _locateLocalOk = false;
        private bool _locatePermissionNotified = false;
        private string _lastWeatherDay = "";
        private DateTime _nextWeatherRefresh;
        private readonly object _weatherLock = new object();
        private string _fxOverride = "";
        private string _weatherFx = "";
        private string _weatherParticle = "";
        private Bitmap _hotOverlay;
        private Bitmap _coldOverlay;
        private Bitmap _overlaySource;
        private readonly List<WeatherParticle> _particles = new List<WeatherParticle>();
        private double _lastParticleTick;
        private string _lastParticleType = "";

        private class WeatherParticle
        {
            public string type;
            public float x, y, vx, vy, size, phase, amp;
            public int life, maxLife;
        }

        private IntPtr _menuHookMouse;
        private IntPtr _menuHookKey;
        private Native.HookProc _menuHookMouseProc;
        private Native.HookProc _menuHookKeyProc;
        private bool _menuWasOpen;

        private static readonly string[] DefaultTap = new string[]
        {
            "戳我干嘛呀！(>ω<)",
            "嘿嘿，有点痒～",
            "再戳我就要生气了！(｀へ´)",
            "主人加油鸭！٩(◕‿◕｡)۶",
            "今天也要元气满满哦！",
            "发呆中…勿扰 (-_-)",
            "嘻嘻，被你抓到啦！",
            "陪我玩一会儿嘛～",
            "盯——(◎_◎)",
            "冲鸭！冲鸭！",
            "别摸啦，要害羞了 >///<",
            "叮！专注模式开启 ✧",
            "喵～有什么事吗？",
            "我超可爱的！哼！",
            "偷偷摸鱼被发现了(ﾉ≧∀≦)ﾉ",
            "这里是专心工作的小可爱！",
        };

        private static readonly string[] DefaultIdle = new string[]
        {
            "呼…好安静呀～",
            "这里是我的地盘！",
            "主人加油，我陪着你～",
            "Zzz… 不许吵我…",
            "今天也是美好的一天～",
        };

        private static readonly string[] DefaultPose = new string[]
        {
            "咔嚓！摆个造型～",
            "换个姿势，更好看！",
            "这样够帅吧？",
            "嘿嘿，摆好了！",
        };

        private static readonly string[] DefaultDrop = new string[]
        {
            "放我下来啦！",
            "轻拿轻放！",
            "举高高！再来一次！",
            "呼，站稳了～",
        };

        private static readonly string[] DrinkPhrases = new string[]
        {
            "咕噜咕噜～该喝水啦！",
            "主人，喝口水润润嗓子吧～",
            "口渴了吗？喝杯温水休息下！",
            "喝水时间到！(๑•̀ㅂ•́)و✧",
        };

        private static readonly string[] SitPhrases = new string[]
        {
            "坐了这么久，起来活动一下腰吧～",
            "伸个懒腰，站起来走走！",
            "久坐伤身，起身眺望远方一下吧！",
            "该活动活动啦，扭扭脖子伸伸腿～",
        };

        private static readonly int[] HealthIntervals = new int[] { 30, 45, 60, 90, 120 };

        private void TickHealth()
        {
            DateTime now = DateTime.UtcNow;
            if (_drinkEnabled && now >= _drinkNextAt)
            {
                _drinkNextAt = now.AddMinutes(_drinkIntervalMin);
                ShowBubble(DrinkPhrases[_rng.Next(DrinkPhrases.Length)]);
            }
            if (_sitEnabled && now >= _sitNextAt)
            {
                _sitNextAt = now.AddMinutes(_sitIntervalMin);
                if (!IsAnimating()) StartAnim("stretch", 1300, "zzz", 900);
                ShowBubble(SitPhrases[_rng.Next(SitPhrases.Length)]);
            }
        }

        private void ToggleDrink()
        {
            _drinkEnabled = !_drinkEnabled;
            if (_miDrink != null) _miDrink.Checked = _drinkEnabled;
            if (_drinkEnabled) _drinkNextAt = DateTime.UtcNow.AddMinutes(_drinkIntervalMin);
            SaveSettings();
        }

        private void ToggleSit()
        {
            _sitEnabled = !_sitEnabled;
            if (_miSit != null) _miSit.Checked = _sitEnabled;
            if (_sitEnabled) _sitNextAt = DateTime.UtcNow.AddMinutes(_sitIntervalMin);
            SaveSettings();
        }

        private void BuildHealthMenu(ToolStripMenuItem parent)
        {
            _miDrink = new ToolStripMenuItem("喝水提醒");
            _miDrink.Checked = _drinkEnabled;
            _miDrink.Click += delegate { ToggleDrink(); };
            parent.DropDownItems.Add(_miDrink);

            _miSit = new ToolStripMenuItem("久坐提醒");
            _miSit.Checked = _sitEnabled;
            _miSit.Click += delegate { ToggleSit(); };
            parent.DropDownItems.Add(_miSit);

            parent.DropDownItems.Add(new ToolStripSeparator());

            _miDrinkInt = new ToolStripMenuItem("喝水间隔：" + _drinkIntervalMin + " 分钟");
            _miDrinkInts = new ToolStripMenuItem[HealthIntervals.Length];
            for (int i = 0; i < HealthIntervals.Length; i++)
            {
                int m = HealthIntervals[i];
                _miDrinkInts[i] = new ToolStripMenuItem(m + " 分钟", null, delegate
                {
                    _drinkIntervalMin = m;
                    if (_drinkEnabled) _drinkNextAt = DateTime.UtcNow.AddMinutes(m);
                    SaveSettings();
                });
                _miDrinkInt.DropDownItems.Add(_miDrinkInts[i]);
            }
            parent.DropDownItems.Add(_miDrinkInt);

            _miSitInt = new ToolStripMenuItem("久坐间隔：" + _sitIntervalMin + " 分钟");
            _miSitInts = new ToolStripMenuItem[HealthIntervals.Length];
            for (int i = 0; i < HealthIntervals.Length; i++)
            {
                int m = HealthIntervals[i];
                _miSitInts[i] = new ToolStripMenuItem(m + " 分钟", null, delegate
                {
                    _sitIntervalMin = m;
                    if (_sitEnabled) _sitNextAt = DateTime.UtcNow.AddMinutes(m);
                    SaveSettings();
                });
                _miSitInt.DropDownItems.Add(_miSitInts[i]);
            }
            parent.DropDownItems.Add(_miSitInt);
        }

        private void RefreshHealthMenu()
        {
            if (_miDrink != null) _miDrink.Checked = _drinkEnabled;
            if (_miSit != null) _miSit.Checked = _sitEnabled;
            if (_miDrinkInt != null) _miDrinkInt.Text = "喝水间隔：" + _drinkIntervalMin + " 分钟";
            if (_miSitInt != null) _miSitInt.Text = "久坐间隔：" + _sitIntervalMin + " 分钟";
            if (_miDrinkInts != null)
            {
                for (int i = 0; i < _miDrinkInts.Length; i++)
                    _miDrinkInts[i].Checked = (HealthIntervals[i] == _drinkIntervalMin);
            }
            if (_miSitInts != null)
            {
                for (int i = 0; i < _miSitInts.Length; i++)
                    _miSitInts[i].Checked = (HealthIntervals[i] == _sitIntervalMin);
            }
        }

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

        public PetForm()
        {
            Text = "桌面宠物";
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            TopMost = true;

            _settingsPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "DesktopPet", "pet.ini");
            _phrasesPath = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "台词.txt");
            LoadPhrases();
            LoadCharacter();
            LoadSettings();
            ApplySavedCharacter();
            ApplyScale(_scale, false);
            _moodDecayAt = DateTime.UtcNow;
            _wanderNextAt = DateTime.UtcNow.AddMilliseconds(12000);

            Rectangle wa = Screen.PrimaryScreen.WorkingArea;
            Location = new Point(wa.Right - ClientSize.Width - 40, wa.Bottom - ClientSize.Height - 30);

            _bubble = new BubbleForm();
            BuildMenu();

            _timer = new System.Windows.Forms.Timer();
            _timer.Interval = 33;
            _timer.Tick += OnTick;
            _idleNextAt = DateTime.UtcNow.AddMilliseconds(_rng.Next(8000, 16000));
            _nextWeatherRefresh = DateTime.UtcNow.AddMinutes(30);
        }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= Native.WS_EX_LAYERED | Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE;
                return cp;
            }
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            int ex = Native.GetWindowLong(Handle, Native.GWL_EXSTYLE);
            ex |= Native.WS_EX_LAYERED | Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE;
            Native.SetWindowLong(Handle, Native.GWL_EXSTYLE, ex);
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            RenderFrame();
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            _timer.Start();
            RenderFrame();
            ThreadPool.QueueUserWorkItem(delegate
            {
                Thread.Sleep(3000);
                QueryWeather(true);
            });
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!_closing)
            {
                e.Cancel = true;
                BeginClose();
                return;
            }
            _timer.Stop();
            SaveSettings();
            UninstallMenuHooks();
            if (_bubble != null) _bubble.Close();
            base.OnFormClosing(e);
        }

        private void BeginClose()
        {
            _closing = true;
            _timer.Interval = 20;
        }

        private void LoadCharacter()
        {
            try
            {
                Assembly asm = Assembly.GetExecutingAssembly();
                using (Stream s = asm.GetManifestResourceStream("DesktopPet.character.png"))
                {
                    if (s != null)
                    {
                        _char = new Bitmap(s);
                        _charW = _char.Width;
                        _charH = _char.Height;
                        LoadPoses();
                        return;
                    }
                }
            }
            catch { }

            _char = new Bitmap(200, 200, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(_char))
            {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                using (SolidBrush b = new SolidBrush(Color.FromArgb(255, 255, 190, 120)))
                {
                    g.FillEllipse(b, 10, 10, 180, 180);
                }
            }
            _charW = 200;
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

        private void LoadSettings()
        {
            try
            {
                if (File.Exists(_settingsPath))
                {
                    string[] lines = File.ReadAllLines(_settingsPath);
                    foreach (string line in lines)
                    {
                        if (line.StartsWith("scale="))
                        {
                            double v;
                            if (double.TryParse(line.Substring(6), NumberStyles.Float, CultureInfo.InvariantCulture, out v))
                                _scale = Math.Max(MIN_SCALE, Math.Min(MAX_SCALE, v));
                        }
                        else if (line.StartsWith("topmost="))
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
                        }
                        else if (line.StartsWith("citycode="))
                        {
                            _cityCode = line.Substring(9).Trim();
                        }
                        else if (line.StartsWith("cityname="))
                        {
                            _cityName = line.Substring(9).Trim();
                        }
                        else if (line.StartsWith("drink="))
                        {
                            _drinkEnabled = line.Substring(6).Trim() == "1";
                        }
                        else if (line.StartsWith("drinkmin="))
                        {
                            int v;
                            if (int.TryParse(line.Substring(9), out v) && v >= 10 && v <= 300)
                                _drinkIntervalMin = v;
                        }
                        else if (line.StartsWith("sit="))
                        {
                            _sitEnabled = line.Substring(4).Trim() == "1";
                        }
                        else if (line.StartsWith("sitmin="))
                        {
                            int v;
                            if (int.TryParse(line.Substring(7), out v) && v >= 10 && v <= 300)
                                _sitIntervalMin = v;
                        }
                    }
                }
            }
            catch { }
        }

        private void SaveSettings()
        {
            try
            {
                string dir = Path.GetDirectoryName(_settingsPath);
                if (!Directory.Exists(dir)) Directory.CreateDirectory(dir);
                string s = "scale=" + _scale.ToString("0.00", CultureInfo.InvariantCulture) + "\r\n" +
                           "topmost=" + (_topmost ? "1" : "0") + "\r\n" +
                           "char=" + _charName + "\r\n" +
                           "wander=" + (_wanderEnabled ? "1" : "0") + "\r\n" +
                           "citycode=" + _cityCode + "\r\n" +
                           "cityname=" + _cityName + "\r\n" +
                           "drink=" + (_drinkEnabled ? "1" : "0") + "\r\n" +
                           "drinkmin=" + _drinkIntervalMin + "\r\n" +
                           "sit=" + (_sitEnabled ? "1" : "0") + "\r\n" +
                           "sitmin=" + _sitIntervalMin + "\r\n";
                File.WriteAllText(_settingsPath, s);
            }
            catch { }
        }


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
                string s = new System.Text.UTF8Encoding(false, true).GetString(bytes);
                if (s.Length > 0 && s[0] == '\uFEFF') s = s.Substring(1);
                return s;
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
                if (Directory.Exists(dir) && FindImage(dir, "character") != null)
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
                string cPath = FindImage(dir, "character");
                if (cPath == null) return false;
                Bitmap c = PrepareCharacterImage(cPath);
                if (c == null) return false;
                _char = c;
                _charW = c.Width;
                _charH = c.Height;
                _hotOverlay = null;
                _coldOverlay = null;
                _overlaySource = null;
                string p1 = FindImage(dir, "pose1");
                string p2 = FindImage(dir, "pose2");
                _pose1 = (p1 != null) ? PrepareCharacterImage(p1) : null;
                _pose2 = (p2 != null) ? PrepareCharacterImage(p2) : null;
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
            _hotOverlay = null;
            _coldOverlay = null;
            _overlaySource = null;
            ApplyScale(_scale, false);
            SaveSettings();
            ShowBubble("已切换回内置角色");
            RenderFrame();
        }

        private static string FindImage(string dir, string baseName)
        {
            string[] exts = new string[] { ".png", ".jpg", ".jpeg", ".bmp", ".gif" };
            foreach (string e in exts)
            {
                string p = Path.Combine(dir, baseName + e);
                if (File.Exists(p)) return p;
            }
            return null;
        }

        private static Bitmap PrepareCharacterImage(string path)
        {
            try
            {
                Bitmap cut;
                using (Bitmap src = new Bitmap(path))
                {
                    cut = AutoCutout(src);
                }
                if (cut == null) return null;
                Bitmap cropped = CropToContent(cut);
                if (cropped != null && cropped != cut) { cut.Dispose(); cut = cropped; }
                Bitmap sized = NormalizeHeight(cut, 800);
                if (sized != null && sized != cut) { cut.Dispose(); cut = sized; }
                return cut;
            }
            catch { return null; }
        }

        private static Bitmap AutoCutout(Bitmap src)
        {
            int w = src.Width, h = src.Height;
            if (w <= 0 || h <= 0) return null;
            Bitmap bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(bmp))
            {
                g.Clear(Color.Transparent);
                g.DrawImage(src, 0, 0, w, h);
            }
            Rectangle rect = new Rectangle(0, 0, w, h);
            BitmapData bd = bmp.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
            int stride = bd.Stride;
            byte[] pixels = new byte[stride * h];
            Marshal.Copy(bd.Scan0, pixels, 0, pixels.Length);
            try
            {
                bool hasAlpha = false;
                for (int i = 3; i < pixels.Length; i += 4)
                {
                    if (pixels[i] < 250) { hasAlpha = true; break; }
                }
                if (hasAlpha)
                {
                    bmp.UnlockBits(bd);
                    return bmp;
                }

                int margin = Math.Max(4, Math.Min(w, h) / 60);
                Dictionary<int, int> hist = new Dictionary<int, int>();
                for (int y = 0; y < h; y++)
                {
                    for (int x = 0; x < w; x++)
                    {
                        if (x >= margin && y >= margin && x < w - margin && y < h - margin) continue;
                        int idx = y * stride + x * 4;
                        int key = ((pixels[idx] >> 4) << 8) | ((pixels[idx + 1] >> 4) << 4) | (pixels[idx + 2] >> 4);
                        int c;
                        if (hist.TryGetValue(key, out c)) hist[key] = c + 1;
                        else hist[key] = 1;
                    }
                }
                int bestKey = -1, bestCount = -1;
                foreach (KeyValuePair<int, int> kv in hist)
                {
                    if (kv.Value > bestCount) { bestCount = kv.Value; bestKey = kv.Key; }
                }
                if (bestKey < 0) { bmp.UnlockBits(bd); return bmp; }
                int br = (bestKey >> 8) << 4;
                int bg2 = ((bestKey >> 4) & 0xF) << 4;
                int bb = (bestKey & 0xF) << 4;
                int tol = 42;

                byte[] isBg = new byte[w * h];
                Queue<int> queue = new Queue<int>();
                Func<int, int, bool> near = delegate(int x, int y)
                {
                    if (x < 0 || y < 0 || x >= w || y >= h) return false;
                    int idx = y * stride + x * 4;
                    return Math.Abs(pixels[idx] - br) <= tol &&
                           Math.Abs(pixels[idx + 1] - bg2) <= tol &&
                           Math.Abs(pixels[idx + 2] - bb) <= tol;
                };
                Action<int, int> seed = delegate(int x, int y)
                {
                    if (x < 0 || y < 0 || x >= w || y >= h) return;
                    int pos = y * w + x;
                    if (isBg[pos] != 0) return;
                    if (near(x, y))
                    {
                        isBg[pos] = 1;
                        queue.Enqueue(pos);
                    }
                };
                for (int x = 0; x < w; x++) { seed(x, 0); seed(x, h - 1); }
                for (int y = 0; y < h; y++) { seed(0, y); seed(w - 1, y); }
                while (queue.Count > 0)
                {
                    int pos = queue.Dequeue();
                    int x = pos % w;
                    int y = pos / w;
                    seed(x - 1, y); seed(x + 1, y); seed(x, y - 1); seed(x, y + 1);
                }

                byte[] alpha = new byte[w * h];
                for (int i = 0; i < w * h; i++) alpha[i] = (isBg[i] == 0) ? (byte)255 : (byte)0;
                alpha = BoxBlur(alpha, w, h);
                alpha = BoxBlur(alpha, w, h);
                for (int i = 0; i < w * h; i++) pixels[i * 4 + 3] = alpha[i];
                Marshal.Copy(pixels, 0, bd.Scan0, pixels.Length);
                bmp.UnlockBits(bd);
                return bmp;
            }
            catch
            {
                try { bmp.UnlockBits(bd); } catch { }
                return null;
            }
        }

        private static byte[] BoxBlur(byte[] src, int w, int h)
        {
            byte[] dst = new byte[w * h];
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    int sum = 0, cnt = 0;
                    for (int dy = -1; dy <= 1; dy++)
                    {
                        for (int dx = -1; dx <= 1; dx++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (nx >= 0 && ny >= 0 && nx < w && ny < h)
                            {
                                sum += src[ny * w + nx];
                                cnt++;
                            }
                        }
                    }
                    dst[y * w + x] = (byte)(sum / cnt);
                }
            }
            return dst;
        }

        private static Bitmap CropToContent(Bitmap bmp)
        {
            int w = bmp.Width, h = bmp.Height;
            BitmapData bd = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            int stride = bd.Stride;
            byte[] pixels = new byte[stride * h];
            Marshal.Copy(bd.Scan0, pixels, 0, pixels.Length);
            int minX = w, minY = h, maxX = -1, maxY = -1;
            for (int y = 0; y < h; y++)
            {
                int row = y * stride;
                for (int x = 0; x < w; x++)
                {
                    if (pixels[row + x * 4 + 3] > 8)
                    {
                        if (x < minX) minX = x;
                        if (x > maxX) maxX = x;
                        if (y < minY) minY = y;
                        if (y > maxY) maxY = y;
                    }
                }
            }
            bmp.UnlockBits(bd);
            if (maxX < 0) return bmp;
            int bw = maxX - minX + 1, bh = maxY - minY + 1;
            if (bw >= w && bh >= h) return bmp;
            Bitmap cropped = new Bitmap(bw, bh, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(cropped))
            {
                g.DrawImage(bmp, new Rectangle(0, 0, bw, bh), new Rectangle(minX, minY, bw, bh), GraphicsUnit.Pixel);
            }
            return cropped;
        }

        private static Bitmap NormalizeHeight(Bitmap bmp, int maxH)
        {
            if (bmp.Height <= maxH) return bmp;
            int nh = maxH;
            int nw = Math.Max(1, (int)Math.Round((double)bmp.Width * nh / bmp.Height));
            Bitmap resized = new Bitmap(nw, nh, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(resized))
            {
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.DrawImage(bmp, 0, 0, nw, nh);
            }
            return resized;
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
                        if (FindImage(dir, "character") == null) continue;
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

        private void ApplyScale(double newScale, bool anchorAtCursor)
        {
            newScale = Math.Max(MIN_SCALE, Math.Min(MAX_SCALE, newScale));
            int oldW = ClientSize.Width;
            int oldH = ClientSize.Height;
            Point center = PointToScreen(new Point(oldW / 2, oldH / 2));
            int newW = (int)Math.Round(_charW * newScale);
            int newH = (int)Math.Round(_charH * newScale * (1.0 + HEADROOM));
            _scale = newScale;
            ClientSize = new Size(newW, newH);
            if (anchorAtCursor)
            {
                Location = new Point(center.X - newW / 2, center.Y - newH / 2);
            }
            ClampToScreen();
            SaveSettings();
            RenderFrame();
        }

        private void ClampToScreen()
        {
            Rectangle wa = Screen.FromPoint(Location).WorkingArea;
            int w = ClientSize.Width;
            int h = ClientSize.Height;
            int x = Location.X;
            int y = Location.Y;
            if (w >= wa.Width) x = wa.X;
            else
            {
                if (x < wa.X) x = wa.X;
                if (x + w > wa.Right) x = wa.Right - w;
            }
            if (h >= wa.Height) y = wa.Y;
            else
            {
                if (y < wa.Y) y = wa.Y;
                if (y + h > wa.Bottom) y = wa.Bottom - h;
            }
            Location = new Point(x, y);
        }

        private void BuildMenu()
        {
            _menu = new ContextMenuStrip();
            _menu.Closed += delegate { UninstallMenuHooks(); };
            _menu.Opening += delegate { RefreshMenuState(); };
            _menu.Items.Add("随机互动一下", null, delegate { TriggerRandomInteraction(); });

            _menu.Items.Add("今日天气", null, delegate { QueryWeather(true); });
            _menu.Items.Add("设置城市…", null, delegate { PromptCity(); });
            _miWeather = new ToolStripMenuItem("天气：未设置城市");
            _miWeather.Enabled = false;
            _menu.Items.Add(_miWeather);
            _menu.Items.Add("定位信息", null, delegate { ShowLocateInfo(); });

            ToolStripMenuItem miFx = new ToolStripMenuItem("天气效果预览");
            string[] fxKeys = new string[] { "", "rain", "snow", "hot", "cold" };
            string[] fxLabels = new string[] { "跟随天气（自动）", "雨丝", "雪花", "红温", "结冰" };
            _miFxItems = new ToolStripMenuItem[fxKeys.Length];
            for (int i = 0; i < fxKeys.Length; i++)
            {
                string k = fxKeys[i];
                _miFxItems[i] = new ToolStripMenuItem(fxLabels[i], null, delegate { ApplyFxOverride(k); });
                miFx.DropDownItems.Add(_miFxItems[i]);
            }
            _menu.Items.Add(miFx);

            ToolStripMenuItem miPomo = new ToolStripMenuItem("番茄钟");
            miPomo.DropDownItems.Add("开始 25 分钟专注", null, delegate { StartPomodoro(); });
            miPomo.DropDownItems.Add("开始 5 分钟休息", null, delegate { StartRest(); });
            miPomo.DropDownItems.Add("停止计时", null, delegate { StopPomodoro(); });
            _menu.Items.Add(miPomo);

            ToolStripMenuItem miHealth = new ToolStripMenuItem("健康提醒");
            BuildHealthMenu(miHealth);
            _menu.Items.Add(miHealth);

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

        private void InstallMenuHooks()
        {
            if (_menuHookMouse == IntPtr.Zero)
            {
                _menuHookMouseProc = MenuMouseHookProc;
                _menuHookMouse = Native.SetWindowsHookEx(Native.WH_MOUSE_LL, _menuHookMouseProc,
                    Native.GetModuleHandle(null), 0);
            }
            if (_menuHookKey == IntPtr.Zero)
            {
                _menuHookKeyProc = MenuKeyHookProc;
                _menuHookKey = Native.SetWindowsHookEx(Native.WH_KEYBOARD_LL, _menuHookKeyProc,
                    Native.GetModuleHandle(null), 0);
            }
        }

        private void UninstallMenuHooks()
        {
            if (_menuHookMouse != IntPtr.Zero)
            {
                Native.UnhookWindowsHookEx(_menuHookMouse);
                _menuHookMouse = IntPtr.Zero;
            }
            if (_menuHookKey != IntPtr.Zero)
            {
                Native.UnhookWindowsHookEx(_menuHookKey);
                _menuHookKey = IntPtr.Zero;
            }
        }

        private void CloseMenu()
        {
            if (_menu != null && _menu.Visible) _menu.Close();
        }

        private IntPtr MenuMouseHookProc(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                int msg = wParam.ToInt32();
                if (msg == Native.WM_LBUTTONDOWN || msg == Native.WM_RBUTTONDOWN ||
                    msg == Native.WM_MBUTTONDOWN || msg == Native.WM_XBUTTONDOWN)
                {
                    if (_menu == null || !_menu.Visible)
                    {
                        UninstallMenuHooks();
                    }
                    else
                    {
                        Point p = Cursor.Position;
                        Rectangle pet = new Rectangle(Location, Size);
                        if (!IsPointInsideMenu(p) && !pet.Contains(p))
                        {
                            CloseMenu();
                        }
                    }
                }
            }
            return Native.CallNextHookEx(_menuHookMouse, nCode, wParam, lParam);
        }

        private IntPtr MenuKeyHookProc(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && wParam.ToInt32() == Native.WM_KEYDOWN)
            {
                if (_menu != null && _menu.Visible)
                {
                    int vk = Marshal.ReadInt32(lParam);
                    if (vk == Native.VK_ESCAPE)
                    {
                        CloseMenu();
                        return new IntPtr(1);
                    }
                }
            }
            return Native.CallNextHookEx(_menuHookKey, nCode, wParam, lParam);
        }

        private bool IsPointInsideMenu(Point p)
        {
            if (_menu == null || !_menu.Visible) return false;
            if (_menu.Bounds.Contains(p)) return true;
            foreach (ToolStripItem item in _menu.Items)
            {
                ToolStripMenuItem mi = item as ToolStripMenuItem;
                if (mi != null && mi.DropDown != null && mi.DropDown.Visible &&
                    IsPointInsideDropDown(p, mi.DropDown))
                    return true;
            }
            return false;
        }

        private static bool IsPointInsideDropDown(Point p, ToolStripDropDown dd)
        {
            if (!dd.Visible) return false;
            if (dd.Bounds.Contains(p)) return true;
            foreach (ToolStripItem item in dd.Items)
            {
                ToolStripMenuItem mi = item as ToolStripMenuItem;
                if (mi != null && mi.DropDown != null && mi.DropDown.Visible &&
                    IsPointInsideDropDown(p, mi.DropDown))
                    return true;
            }
            return false;
        }

        private void RefreshMenuState()
        {
            if (_miWeather != null)
                _miWeather.Text = _cityName.Length > 0 ? "天气城市：" + _cityName : "天气：未设置城市";
            if (_miFxItems != null)
            {
                for (int i = 0; i < _miFxItems.Length; i++)
                {
                    string k = (i == 0) ? "" : new string[] { "rain", "snow", "hot", "cold" }[i - 1];
                    _miFxItems[i].Checked = (_fxOverride == k);
                }
            }
            if (_miMood != null) _miMood.Text = "心情：" + MoodLabel();
            if (_miWander != null) _miWander.Checked = _wanderEnabled;
            if (_miAutoStart != null) _miAutoStart.Checked = IsAutoStartEnabled();
            RefreshHealthMenu();
            RefreshCharacterMenu();
        }

        private void TriggerRandomInteraction()
        {
            AddMood(8);
            int r = _rng.Next(9);
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
            }
            if (_anim == "pose1" || _anim == "pose2")
            {
                ShowBubble(_posePhrases[_rng.Next(_posePhrases.Count)]);
            }
            else
            {
                ShowBubble(_tapPhrases[_rng.Next(_tapPhrases.Count)]);
            }
        }

        private void StartIdleAction()
        {
            int r;
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
            }
        }

        private void StartAnim(string name, double durMs, string effect, double effectMs)
        {
            _anim = name;
            _animStart = DateTime.UtcNow;
            _animDur = durMs;
            _poseImg = (name == "pose1" || name == "pose2") ? name : "";
            if (effect.Length > 0)
            {
                _effect = effect;
                _effectStart = DateTime.UtcNow;
                _effectDur = effectMs;
            }
            else
            {
                _effect = "";
            }
        }

        private void QueryWeather(bool announce)
        {
            lock (_weatherLock)
            {
                if (_weatherBusy) return;
                _weatherBusy = true;
            }
            _lastWeatherDay = DateTime.Now.ToString("yyyyMMdd");
            if (announce) SafeBubble("正在查询今日天气…");
            ThreadPool.QueueUserWorkItem(delegate { DoWeatherQuery(announce, false); });
        }

        private void QueryWeatherSilent()
        {
            lock (_weatherLock)
            {
                if (_weatherBusy) return;
                _weatherBusy = true;
            }
            _nextWeatherRefresh = DateTime.UtcNow.AddMinutes(30);
            ThreadPool.QueueUserWorkItem(delegate { DoWeatherQuery(false, true); });
        }

        private void SafeBubble(string text)
        {
            try
            {
                if (IsHandleCreated && !IsDisposed)
                    BeginInvoke(new Action(delegate { ShowBubble(text); }));
            }
            catch { }
        }

        private void DoWeatherQuery(bool announce, bool silent)
        {
            string msg = "";
            try
            {
                string code = _cityCode;
                string name = _cityName;
                if (!_cityLocated)
                {
                    // 每次启动首次查询都重新 IP 定位（手动设置仅当前会话生效）
                    LocateCity(out code, out name);
                    if (string.IsNullOrEmpty(code))
                    {
                        code = _cityCode;
                        name = _cityName;
                    }
                    if (string.IsNullOrEmpty(code))
                    {
                        code = "101010100";
                        name = "北京";
                    }
                    _cityLocated = true;
                }
                string page = HttpGetUtf8("http://d1.weather.com.cn/weather_index/" + code + ".html", "http://www.weather.com.cn/");
                WeatherInfo wi = ParseWeather(page, name);
                msg = wi.Text;
                string fx = ResolveWeatherFx(wi);
                if (fx != _weatherFx)
                {
                    _weatherFx = fx;
                }
                _weatherParticle = ResolveWeatherParticle(wi);
                _cityCode = code;
                _cityName = name;
                SaveSettings();
            }
            catch (Exception ex)
            {
                msg = "天气查询失败(>_<)\n" + (announce ? "请检查网络后重试～" : "主人，网络好像不太给力～");
            }
            finally
            {
                string m = msg;
                try
                {
                    if (IsHandleCreated && !IsDisposed)
                        BeginInvoke(new Action(delegate
                        {
                            if (!silent) ShowBubble(m);
                            lock (_weatherLock) { _weatherBusy = false; }
                        }));
                    else
                        lock (_weatherLock) { _weatherBusy = false; }
                }
                catch { lock (_weatherLock) { _weatherBusy = false; } }
            }
        }

        private struct WeatherInfo
        {
            public string Text;
            public string Weather;
            public int TempHigh;
            public int TempLow;
            public int TempNow;
        }

        private static int ParseIntTemp(string s)
        {
            int v;
            if (int.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out v))
                return (v >= 900) ? -9999 : v;
            double d;
            if (double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out d))
                return (d >= 900) ? -9999 : (int)Math.Round(d);
            return -9999;
        }

        private static WeatherInfo ParseWeather(string page, string fallbackName)
        {
            WeatherInfo wi = new WeatherInfo();
            string name = Regex.Match(page, "\"city\":\"([^\"]+)\"").Groups[1].Value;
            if (string.IsNullOrEmpty(name)) name = fallbackName;

            string tHigh = Regex.Match(page, "\"temp\":\"([^\"]+)\"").Groups[1].Value;
            string tLow = Regex.Match(page, "\"tempn\":\"([^\"]+)\"").Groups[1].Value;
            string weather = Regex.Match(page, "\"weather\":\"([^\"]+)\"").Groups[1].Value;

            int i = page.IndexOf("var dataSK");
            string sk = i >= 0 ? page.Substring(i) : page;
            string rt = Regex.Match(sk, "\"temp\":\"([^\"]+)\"").Groups[1].Value;
            string wd = Regex.Match(sk, "\"WD\":\"([^\"]+)\"").Groups[1].Value;
            string ws = Regex.Match(sk, "\"WS\":\"([^\"]+)\"").Groups[1].Value;
            string sd = Regex.Match(sk, "\"SD\":\"([^\"]+)\"").Groups[1].Value;
            string rw = Regex.Match(sk, "\"weather\":\"([^\"]+)\"").Groups[1].Value;
            if (string.IsNullOrEmpty(rw)) rw = weather;
            if (string.IsNullOrEmpty(rw)) rw = "天气数据获取中";

            // 实时天气现象优先（d1 的"今日预报"字段 temp/weather 经常滞后不准）
            wi.Weather = rw;
            wi.TempHigh = ParseIntTemp(tHigh);
            wi.TempLow = ParseIntTemp(tLow);
            wi.TempNow = ParseIntTemp(rt);

            string line1 = "主人～今日天气播报！";
            string line2 = name + "：" + rw;
            if (wi.TempNow > -9000) line2 += " 实时" + wi.TempNow + "℃";
            string line3 = "";
            if (wi.TempHigh > -9000)
                line3 = "预报 " + wi.TempLow + "℃~" + wi.TempHigh + "℃";
            else if (wi.TempLow > -9000)
                line3 = "气温约 " + wi.TempLow + "℃";
            string line4 = "";
            if (!string.IsNullOrEmpty(wd) || !string.IsNullOrEmpty(ws))
                line4 = (wd + " " + ws).Trim();
            if (!string.IsNullOrEmpty(sd)) line4 = line4.Length > 0 ? line4 + " · 湿度" + sd : "湿度 " + sd;
            wi.Text = line1 + "\n" + line2 + (line3.Length > 0 ? "\n" + line3 : "") + (line4.Length > 0 ? "\n" + line4 : "");
            return wi;
        }

        private static string DecideWeatherFx(WeatherInfo wi)
        {
            if (wi.TempNow >= 33 || wi.TempHigh >= 34) return "hot";
            if (wi.TempNow <= 2 || (wi.TempLow > -9000 && wi.TempLow <= 0)) return "cold";
            return "";
        }

        private static string DecideWeatherParticle(WeatherInfo wi)
        {
            string w = wi.Weather;
            if (!string.IsNullOrEmpty(w))
            {
                if (w.Contains("雪")) return "snow";
                if (w.Contains("雨") || w.Contains("冰雹")) return "rain";
            }
            if (wi.TempNow >= 33 || wi.TempHigh >= 34) return "hot";
            if (wi.TempNow <= 2 || (wi.TempLow > -9000 && wi.TempLow <= 0)) return "cold";
            return "";
        }

        private string ResolveWeatherFx(WeatherInfo wi)
        {
            if (_fxOverride == "hot" || _fxOverride == "cold") return _fxOverride;
            if (_fxOverride == "rain" || _fxOverride == "snow") return "";
            return DecideWeatherFx(wi);
        }

        private string ResolveWeatherParticle(WeatherInfo wi)
        {
            if (_fxOverride.Length > 0) return _fxOverride;
            return DecideWeatherParticle(wi);
        }

        private void ApplyFxOverride(string k)
        {
            _fxOverride = k;
            if (k.Length == 0)
            {
                QueryWeather(false); // 恢复自动：重新查询以应用真实天气效果
                return;
            }
            if (k == "hot" || k == "cold")
            {
                _weatherFx = k;
                EnsureWeatherOverlays(CurrentPose() ?? _char);
            }
            else
            {
                _weatherFx = "";
            }
            _weatherParticle = k;
            string label = (k == "rain") ? "雨丝" : (k == "snow") ? "雪花" : (k == "hot") ? "红温" : "结冰";
            SafeBubble("天气效果预览：" + label);
        }

        private void EnsureWeatherOverlays(Bitmap src)
        {
            if (src == null) return;
            if (_overlaySource != src || _hotOverlay == null || _coldOverlay == null)
            {
                if (_hotOverlay != null) _hotOverlay.Dispose();
                if (_coldOverlay != null) _coldOverlay.Dispose();
                _hotOverlay = MakeTint(src, 255, 80, 70, 0.34f);
                _coldOverlay = MakeTint(src, 135, 200, 255, 0.45f);
                _overlaySource = src;
            }
        }

        private static Bitmap MakeTint(Bitmap src, int r, int g, int b, float alphaMul)
        {
            Bitmap bmp = new Bitmap(src.Width, src.Height, PixelFormat.Format32bppArgb);
            BitmapData sd = src.LockBits(new Rectangle(0, 0, src.Width, src.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            BitmapData bd = bmp.LockBits(new Rectangle(0, 0, bmp.Width, bmp.Height), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            try
            {
                int stride = sd.Stride;
                byte[] spx = new byte[stride * src.Height];
                byte[] dpx = new byte[stride * src.Height];
                Marshal.Copy(sd.Scan0, spx, 0, spx.Length);
                for (int i = 0; i < spx.Length; i += 4)
                {
                    dpx[i] = (byte)b;
                    dpx[i + 1] = (byte)g;
                    dpx[i + 2] = (byte)r;
                    dpx[i + 3] = (byte)(spx[i + 3] * alphaMul);
                }
                Marshal.Copy(dpx, 0, bd.Scan0, dpx.Length);
            }
            finally
            {
                src.UnlockBits(sd);
                bmp.UnlockBits(bd);
            }
            return bmp;
        }

        private void DrawWeatherFx(Graphics g, int w, int h, Pose p)
        {
            if (_weatherFx.Length == 0) return;
            Bitmap src = CurrentPose();
            if (src == null) src = _char;
            EnsureWeatherOverlays(src);
            float bottom = h - 3f;
            float cw = (float)(_charW * _scale) * p.sx;
            float chh = (float)(_charH * _scale) * p.sy;
            float cx = w / 2f;
            double t = DateTime.UtcNow.Ticks / 10000000.0; // 秒

            // 与 DrawPet 相同的绘制区域（姿势图按比例 fit）
            float dw = cw, dh = chh;
            if (src != _char)
            {
                float fit = Math.Min(cw / src.Width, chh / src.Height);
                dw = src.Width * fit;
                dh = src.Height * fit;
            }

            if (_weatherFx == "hot")
            {
                g.TranslateTransform(cx, bottom + p.oy);
                g.RotateTransform(p.rot);
                g.TranslateTransform(p.ox, 0f);
                if (_hotOverlay != null)
                    g.DrawImage(_hotOverlay, new RectangleF(-dw / 2f, -dh, dw, dh));
                g.ResetTransform();
            }
            else if (_weatherFx == "cold")
            {
                g.TranslateTransform(cx, bottom + p.oy);
                g.RotateTransform(p.rot);
                g.TranslateTransform(p.ox, 0f);
                if (_coldOverlay != null)
                    g.DrawImage(_coldOverlay, new RectangleF(-dw / 2f, -dh, dw, dh));
                DrawIcicles(g, cw, dh, t);
                g.ResetTransform();
            }
        }

        private void DrawWeatherParticles(Graphics g, int w, int h)
        {
            if (_weatherParticle.Length == 0)
            {
                if (_particles.Count > 0) _particles.Clear();
                _lastParticleType = "";
                return;
            }
            if (_weatherParticle != _lastParticleType)
            {
                _lastParticleType = _weatherParticle;
                _particles.Clear();
                _lastParticleTick = 0;
            }
            double now = DateTime.UtcNow.Ticks / 10000000.0;
            double dt = now - _lastParticleTick;
            if (dt <= 0 || dt > 0.1) dt = 0.033;
            bool warmup = (_lastParticleTick == 0);
            _lastParticleTick = now;

            float bottom = h - 3f;
            float chh = (float)(_charH * _scale);
            float cw = (float)(_charW * _scale);
            float cx = w / 2f;
            float top = bottom - chh;
            Random rng = _rng;

            if (_particles.Count < 70)
            {
                double rate = 0;
                if (_weatherParticle == "rain") rate = 30;
                else if (_weatherParticle == "snow") rate = 14;
                else if (_weatherParticle == "hot") rate = 10;
                else if (_weatherParticle == "cold") rate = 8;
                int n = (int)(rate * dt);
                if (rng.NextDouble() < rate * dt - n) n++;
                if (warmup) n = (_weatherParticle == "rain") ? 42 : (_weatherParticle == "snow") ? 22 : 12;
                for (int i = 0; i < n; i++)
                {
                    WeatherParticle p = new WeatherParticle();
                    p.type = _weatherParticle;
                    p.phase = (float)(rng.NextDouble() * Math.PI * 2);
                    bool spread = warmup;
                    if (p.type == "rain")
                    {
                        p.x = (float)(rng.NextDouble() * (w + 20) - 10);
                        p.y = spread ? (float)(rng.NextDouble() * h) : (float)(rng.NextDouble() * 14 - 14);
                        p.vy = h * (1.25f + (float)rng.NextDouble() * 0.5f);
                        p.vx = p.vy * 0.22f;
                        p.size = 7f + (float)rng.NextDouble() * 5f;
                        p.amp = 0f;
                        p.maxLife = (int)((h + 30) / p.vy * 1000);
                    }
                    else if (p.type == "snow")
                    {
                        p.x = (float)(rng.NextDouble() * (w + 16) - 8);
                        p.y = spread ? (float)(rng.NextDouble() * h) : (float)(rng.NextDouble() * 10 - 10);
                        p.vy = 26f + (float)rng.NextDouble() * 26f;
                        p.vx = 4f + (float)rng.NextDouble() * 6f;
                        p.size = 1.6f + (float)rng.NextDouble() * 2.2f;
                        p.amp = 9f + (float)rng.NextDouble() * 8f;
                        p.maxLife = 3200;
                    }
                    else if (p.type == "hot")
                    {
                        p.x = cx + (float)(rng.NextDouble() - 0.5) * cw * 0.8f;
                        p.y = spread ? top + (float)(rng.NextDouble() * chh * 0.8f) : top + (float)(rng.NextDouble() * chh * 0.4f);
                        p.vy = -(55f + (float)rng.NextDouble() * 35f);
                        p.vx = (float)(rng.NextDouble() - 0.5) * 14f;
                        p.size = 3f + (float)rng.NextDouble() * 3.5f;
                        p.amp = 6f + (float)rng.NextDouble() * 5f;
                        p.maxLife = 1600;
                    }
                    else // cold
                    {
                        p.x = (float)(rng.NextDouble() * w);
                        p.y = (float)(rng.NextDouble() * h);
                        p.vy = -(8f + (float)rng.NextDouble() * 12f);
                        p.vx = (float)(rng.NextDouble() - 0.5) * 10f;
                        p.size = 2f + (float)rng.NextDouble() * 2.5f;
                        p.amp = 10f + (float)rng.NextDouble() * 8f;
                        p.maxLife = 2200;
                    }
                    p.life = spread ? (int)(p.maxLife * (0.35 + rng.NextDouble() * 0.6)) : p.maxLife;
                    _particles.Add(p);
                }
            }

            _particles.RemoveAll(delegate(WeatherParticle p)
            {
                p.life -= (int)(dt * 1000);
                if (p.life <= 0) return true;
                float k = (float)p.life / p.maxLife;
                p.x += p.vx * (float)dt;
                p.y += p.vy * (float)dt;
                float drawX = p.x + (float)(Math.Sin(now * 2.2 + p.phase) * p.amp);
                float prog = 1f - k;
                float a = prog < 0.15f ? prog / 0.15f : (prog > 0.7f ? (1f - prog) / 0.3f : 1f);
                int alpha = (int)(165 * a);
                if (alpha <= 3) return true;
                if (p.type == "rain")
                {
                    using (Pen pen = new Pen(Color.FromArgb(alpha, 160, 200, 255), Math.Max(1f, p.size * 0.09f)))
                    {
                        g.DrawLine(pen, drawX, p.y, drawX - p.vx * 0.06f, p.y - p.vy * 0.06f);
                    }
                }
                else
                {
                    float s = p.size * (1f + (1f - k) * 0.8f);
                    Color col = (p.type == "snow") ? Color.FromArgb(alpha, 245, 250, 255)
                             : (p.type == "hot") ? Color.FromArgb(alpha, 255, 235, 210)
                             : Color.FromArgb(alpha, 215, 235, 255);
                    using (SolidBrush b = new SolidBrush(col))
                    {
                        g.FillEllipse(b, drawX - s / 2f, p.y - s / 2f, s, s);
                    }
                }
                return false;
            });
        }

        private void DrawIcicles(Graphics g, float cw, float chh, double t)
        {
            float shim = (float)(Math.Sin(t * 2.2) * 0.5 + 0.5);
            int n = 5;
            using (SolidBrush b = new SolidBrush(Color.FromArgb(215, 200, 235, 255)))
            {
                for (int i = 0; i < n; i++)
                {
                    float x = -cw / 2f + cw * (i + 0.5f) / n;
                    float len = (6f + (i % 3) * 5f) * (float)_scale;
                    PointF[] tri = new PointF[]
                    {
                        new PointF(x - 4f * (float)_scale, -chh),
                        new PointF(x + 4f * (float)_scale, -chh),
                        new PointF(x, -chh + len)
                    };
                    g.FillPolygon(b, tri);
                }
            }
            using (SolidBrush b = new SolidBrush(Color.FromArgb((int)(140 + 90 * shim), 255, 255, 255)))
            {
                g.FillEllipse(b, cw * 0.2f, -chh + chh * 0.1f, cw * 0.05f, cw * 0.05f);
                g.FillEllipse(b, -cw * 0.25f, -chh + chh * 0.28f, cw * 0.035f, cw * 0.035f);
            }
        }

        private static string HttpGetUtf8(string url, string referer)
        {
            using (WebClient wc = new WebClient())
            {
                wc.Encoding = Encoding.UTF8;
                wc.Headers[HttpRequestHeader.UserAgent] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)";
                if (!string.IsNullOrEmpty(referer))
                    wc.Headers[HttpRequestHeader.Referer] = referer;
                return wc.DownloadString(url);
            }
        }

        private void LocateCity(out string code, out string name)
        {
            code = "";
            name = "";
            StringBuilder diag = new StringBuilder();
            diag.AppendLine("== 定位过程 ==");

            // 1) 本地定位优先：Windows 位置服务（WiFi / GPS / 基站，精度街道级）
            string localFail = "";
            _locateLocalOk = TryLocalLocation(out _locateLat, out _locateLon, out localFail);
            if (_locateLocalOk)
            {
                diag.AppendLine(string.Format(CultureInfo.InvariantCulture, "本地定位: 成功 ({0:F5}, {1:F5})", _locateLat, _locateLon));
                name = CityFromLatLon(_locateLat, _locateLon);
                if (!string.IsNullOrEmpty(name))
                {
                    diag.AppendLine("本地逆地理最近城市: " + name);
                    code = CityNameToCode(name);
                    if (string.IsNullOrEmpty(code)) code = CityCodeSearch(name);
                    if (!string.IsNullOrEmpty(code))
                    {
                        diag.AppendLine("城市码: " + code);
                        FinishLocate(diag);
                        return;
                    }
                    diag.AppendLine("城市码查找失败");
                }
                else diag.AppendLine("本地逆地理: 最近城市超过 500km，忽略");
            }
            else
            {
                diag.AppendLine("本地定位: 失败 - " + localFail);
                if (localFail.IndexOf("权限", StringComparison.Ordinal) >= 0 && !_locatePermissionNotified)
                {
                    _locatePermissionNotified = true;
                    SafeBubble("想用电脑本地定位（更准），请开启位置权限：\nWindows 设置 → 隐私 → 位置 → 允许应用访问位置\n开启后重启桌宠生效，现在先用 IP 定位代替。");
                }
            }

            // 2) IP 兜底：ipip.net（国内专业库，对移动/联通 IP 精度高）→ 搜狐 → ip-api（坐标逆地理优先 → 文本兜底）
            string city = "";
            try
            {
                string t = HttpGetUtf8("http://myip.ipip.net", null);
                diag.AppendLine("ipip.net 返回: " + t.Trim());
                city = ParseIpipCity(t);
                if (!string.IsNullOrEmpty(city)) diag.AppendLine("ipip.net 解析城市: " + city);
            }
            catch (Exception ex) { diag.AppendLine("ipip.net 请求异常: " + ex.Message); }
            if (!string.IsNullOrEmpty(city))
            {
                name = NormalizeCity(city);
                code = CityNameToCode(name);
                if (string.IsNullOrEmpty(code)) code = CityCodeSearch(name);
                if (!string.IsNullOrEmpty(code))
                {
                    diag.AppendLine("IP定位(ipip.net): " + city + " → " + name + " (" + code + ")");
                    FinishLocate(diag);
                    return;
                }
                diag.AppendLine("ipip.net 城市解析失败: " + city + " → " + name);
            }

            try
            {
                string s = HttpGetUtf8("http://pv.sohu.com/cityjson", null);
                diag.AppendLine("搜狐返回: " + s.Trim());
                Match m = Regex.Match(s, "\"cname\"\\s*:\\s*\"([^\"]+)\"");
                if (m.Success)
                {
                    city = m.Groups[1].Value;
                    if (city == "未知" || city.Length < 2) city = "";
                }
            }
            catch (Exception ex) { diag.AppendLine("搜狐请求异常: " + ex.Message); }
            if (!string.IsNullOrEmpty(city))
            {
                name = NormalizeCity(city);
                code = CityNameToCode(name);
                if (string.IsNullOrEmpty(code)) code = CityCodeSearch(name);
                if (!string.IsNullOrEmpty(code))
                {
                    diag.AppendLine("IP定位(搜狐): " + city + " → " + name + " (" + code + ")");
                    FinishLocate(diag);
                    return;
                }
                diag.AppendLine("搜狐城市解析失败: " + city + " → " + name);
            }

            // ip-api：坐标逆地理优先（比 city 文本更可信），失败再用文本
            try
            {
                string j = HttpGetUtf8("http://ip-api.com/json/?lang=zh-CN&fields=status,city,regionName,lat,lon", null);
                diag.AppendLine("ip-api 返回: " + j.Trim());
                if (j.Contains("\"status\":\"success\""))
                {
                    double ilat = 0, ilon = 0;
                    Match mlat = Regex.Match(j, "\"lat\"\\s*:\\s*([-0-9.]+)");
                    Match mlon = Regex.Match(j, "\"lon\"\\s*:\\s*([-0-9.]+)");
                    if (mlat.Success && mlon.Success &&
                        double.TryParse(mlat.Groups[1].Value, NumberStyles.Float, CultureInfo.InvariantCulture, out ilat) &&
                        double.TryParse(mlon.Groups[1].Value, NumberStyles.Float, CultureInfo.InvariantCulture, out ilon))
                    {
                        string coordCity = CityFromLatLon(ilat, ilon);
                        diag.AppendLine(string.Format(CultureInfo.InvariantCulture, "ip-api 坐标 ({0:F3},{1:F3}) 逆地理: {2}", ilat, ilon, coordCity.Length > 0 ? coordCity : "(无匹配)"));
                        if (!string.IsNullOrEmpty(coordCity))
                        {
                            name = coordCity;
                            code = CityNameToCode(name);
                            if (string.IsNullOrEmpty(code)) code = CityCodeSearch(name);
                            if (!string.IsNullOrEmpty(code))
                            {
                                diag.AppendLine("IP定位(ip-api 坐标): " + name + " (" + code + ")");
                                FinishLocate(diag);
                                return;
                            }
                        }
                    }
                    // 文本兜底
                    Match mc = Regex.Match(j, "\"city\"\\s*:\\s*\"([^\"]+)\"");
                    if (mc.Success) city = mc.Groups[1].Value;
                    else
                    {
                        Match mr = Regex.Match(j, "\"regionName\"\\s*:\\s*\"([^\"]+)\"");
                        if (mr.Success) city = mr.Groups[1].Value;
                    }
                }
            }
            catch (Exception ex) { diag.AppendLine("ip-api 请求异常: " + ex.Message); }
            if (!string.IsNullOrEmpty(city))
            {
                name = NormalizeCity(city);
                code = CityNameToCode(name);
                if (string.IsNullOrEmpty(code)) code = CityCodeSearch(name);
                diag.AppendLine("IP定位(ip-api 文本): " + city + " → " + name + " (" + code + ")");
            }
            else
            {
                diag.AppendLine("所有定位源均失败");
                name = "";
                code = "";
            }
            FinishLocate(diag);
        }

        private void FinishLocate(StringBuilder diag)
        {
            _locateDiag = diag.ToString();
            AppendLocateLog(_locateDiag);
        }

        private void AppendLocateLog(string text)
        {
            try
            {
                string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "DesktopPet");
                Directory.CreateDirectory(dir);
                File.AppendAllText(Path.Combine(dir, "locate.log"),
                    DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "\n" + text + "\n\n", Encoding.UTF8);
            }
            catch { }
        }

        // 本地定位：调用 Windows 位置服务（WinRT Geolocator）拿经纬度。
        // 失败时通过 failReason 说明原因（权限 / 超时 / 无信号 / 异常），由上层回退 IP 定位。
        private bool TryLocalLocation(out double lat, out double lon, out string failReason)
        {
            lat = 0;
            lon = 0;
            try
            {
                Geolocator g = new Geolocator();
                g.DesiredAccuracy = PositionAccuracy.High;
                Windows.Foundation.IAsyncOperation<Geoposition> op = g.GetGeopositionAsync(TimeSpan.FromSeconds(25), TimeSpan.FromSeconds(5));
                var task = op.AsTask();
                if (!task.Wait(30000))
                {
                    failReason = "定位超时（30 秒无结果）";
                    return false;
                }
                if (op.Status != Windows.Foundation.AsyncStatus.Completed)
                {
                    failReason = "定位失败（状态 " + op.Status + "）";
                    return false;
                }
                Geoposition pos = op.GetResults();
                if (pos == null || pos.Coordinate == null)
                {
                    failReason = "无定位结果（无 GPS / WiFi 信号或位置服务未就绪）";
                    return false;
                }
                lat = pos.Coordinate.Point.Position.Latitude;
                lon = pos.Coordinate.Point.Position.Longitude;
                failReason = "";
                return true;
            }
            catch (UnauthorizedAccessException)
            {
                failReason = "位置权限未开启（Windows 设置 → 隐私 → 位置）";
                return false;
            }
            catch (Exception ex)
            {
                failReason = "异常: " + ex.Message;
                return false;
            }
        }

        // 右键菜单"定位信息"：重新定位一次并把详细过程显示出来
        private void ShowLocateInfo()
        {
            ThreadPool.QueueUserWorkItem(delegate
            {
                string code, name;
                LocateCity(out code, out name);
                string msg = "【定位信息】\n" + _locateDiag
                    + "\n当前天气城市: " + (name.Length > 0 ? name : "未设置（走北京兜底）");
                SafeBubble(msg);
            });
        }

        // 经纬度 -> 最近城市（Haversine 距离，内置城市经纬度表，完全本地计算）
        private const double EarthRadiusKm = 6371.0;

        private static string CityFromLatLon(double lat, double lon)
        {
            if (CityLocs.Count == 0) return "";
            string best = "";
            double bestDist = double.MaxValue;
            double latR = lat * Math.PI / 180.0;
            foreach (KeyValuePair<string, double[]> kv in CityLocs)
            {
                double clat = kv.Value[0] * Math.PI / 180.0;
                double dLat = latR - clat;
                double dLon = (lon - kv.Value[1]) * Math.PI / 180.0;
                double a = Math.Sin(dLat / 2) * Math.Sin(dLat / 2) +
                           Math.Cos(latR) * Math.Cos(clat) * Math.Sin(dLon / 2) * Math.Sin(dLon / 2);
                double dist = EarthRadiusKm * 2 * Math.Atan2(Math.Sqrt(a), Math.Sqrt(1 - a));
                if (dist < bestDist) { bestDist = dist; best = kv.Key; }
            }
            // 最近城市超过 500km（定位在国外或明显异常）时返回空，让上层走 IP 兜底
            return bestDist <= 500 ? best : "";
        }

        // 省级名称 -> 省会城市（仅当 IP 定位只返回省级时兜底，避免"吉林省"被当成"吉林市"）
        private static readonly Dictionary<string, string> ProvinceCapitals = new Dictionary<string, string>()
        {
            { "河北", "石家庄" }, { "山西", "太原" }, { "辽宁", "沈阳" }, { "吉林", "长春" },
            { "黑龙江", "哈尔滨" }, { "江苏", "南京" }, { "浙江", "杭州" }, { "安徽", "合肥" },
            { "福建", "福州" }, { "江西", "南昌" }, { "山东", "济南" }, { "河南", "郑州" },
            { "湖北", "武汉" }, { "湖南", "长沙" }, { "广东", "广州" }, { "海南", "海口" },
            { "四川", "成都" }, { "贵州", "贵阳" }, { "云南", "昆明" }, { "陕西", "西安" },
            { "甘肃", "兰州" }, { "青海", "西宁" }, { "内蒙古", "呼和浩特" }, { "广西", "南宁" },
            { "西藏", "拉萨" }, { "宁夏", "银川" }, { "新疆", "乌鲁木齐" }, { "台湾", "台北" },
            { "香港", "香港" }, { "澳门", "澳门" },
        };

        // ipip.net 返回文本格式："当前 IP：x.x.x.x  来自于：中国 广东 深圳  移动(AS56040)"
        // 直辖市格式如"中国 北京 北京"或"中国 上海 电信"
        private static string ParseIpipCity(string text)
        {
            if (string.IsNullOrEmpty(text)) return "";
            Match m = Regex.Match(text, "来自于[:：]\\s*中国\\s+([^\\s]+)\\s+([^\\s]+)");
            if (!m.Success) return "";
            string a = m.Groups[1].Value; // 省 / 直辖市
            string b = m.Groups[2].Value; // 市 / 运营商
            if (a == "北京" || a == "上海" || a == "天津" || a == "重庆") return a;
            if (b == "移动" || b == "联通" || b == "电信" || b == "铁通") return a;
            return b;
        }

        private static string NormalizeCity(string city)
        {
            if (string.IsNullOrEmpty(city)) return "";
            string s = city.Trim();
            // 原始串里是否带"市"：带则说明定位到了市级，省名不该再映射成省会
            // （如"吉林省吉林市"应保留"吉林"，只有"吉林省"才映射"长春"）
            bool hadCity = s.Contains("市");
            string province = "";
            // 1) 先拆出省级部分（省 / 自治区 / 自治州 / 自治县），剩下的应是市名
            string[] provSuf = { "维吾尔自治区", "壮族自治区", "回族自治区", "自治区", "自治州", "自治县", "省" };
            foreach (string t in provSuf)
            {
                int idx = s.IndexOf(t);
                if (idx >= 0)
                {
                    province = s.Substring(0, idx + t.Length);
                    s = s.Substring(idx + t.Length);
                    break;
                }
            }
            // 2) 循环去掉市级 / 县级后缀
            string[] suf = { "特别行政区", "市", "盟", "县", "地区" };
            bool changed = true;
            while (changed)
            {
                changed = false;
                foreach (string t in suf)
                {
                    if (s.EndsWith(t))
                    {
                        s = s.Substring(0, s.Length - t.Length);
                        changed = true;
                        break;
                    }
                }
            }
            s = s.Trim();
            // 3) 只剩省名（如"广东省"）→ 映射省会
            if (s.Length == 0)
            {
                foreach (KeyValuePair<string, string> kv in ProvinceCapitals)
                {
                    if (province.StartsWith(kv.Key)) return kv.Value;
                }
                return "";
            }
            // 4) 无后缀直接拼接的"四川成都"这类，剥掉省名
            if (!hadCity)
            {
                foreach (KeyValuePair<string, string> kv in ProvinceCapitals)
                {
                    if (s.StartsWith(kv.Key) && s.Length > kv.Key.Length)
                    {
                        s = s.Substring(kv.Key.Length).Trim();
                        break;
                    }
                }
            }
            // 5) 纯省名（如 ip-api 的 regionName"吉林"）→ 映射省会
            if (!hadCity && ProvinceCapitals.ContainsKey(s)) return ProvinceCapitals[s];
            return s;
        }

        private static readonly Dictionary<string, string> CityCodes = new Dictionary<string, string>()
        {
            { "北京", "101010100" }, { "上海", "101020100" }, { "天津", "101030100" }, { "重庆", "101040100" },
            { "哈尔滨", "101050101" }, { "长春", "101060101" }, { "沈阳", "101070101" }, { "呼和浩特", "101080101" },
            { "石家庄", "101090101" }, { "太原", "101100101" }, { "西安", "101110101" }, { "济南", "101120101" },
            { "乌鲁木齐", "101130101" }, { "拉萨", "101140101" }, { "西宁", "101150101" }, { "兰州", "101160101" },
            { "银川", "101170101" }, { "郑州", "101180101" }, { "南京", "101190101" }, { "武汉", "101200101" },
            { "杭州", "101210101" }, { "合肥", "101220101" }, { "福州", "101230101" }, { "南昌", "101240101" },
            { "长沙", "101250101" }, { "贵阳", "101260101" }, { "成都", "101270101" }, { "广州", "101280101" },
            { "昆明", "101290101" }, { "南宁", "101300101" }, { "海口", "101310101" }, { "香港", "101320101" },
            { "澳门", "101330101" }, { "台北", "101340101" },
            { "深圳", "101280601" }, { "珠海", "101280701" }, { "佛山", "101280800" }, { "东莞", "101281601" },
            { "中山", "101281701" }, { "惠州", "101280301" }, { "汕头", "101280501" }, { "湛江", "101281001" },
            { "江门", "101281101" }, { "肇庆", "101280901" }, { "青岛", "101120201" }, { "大连", "101070201" },
            { "厦门", "101230201" }, { "苏州", "101190401" }, { "宁波", "101210401" }, { "无锡", "101190201" },
            { "温州", "101210701" }, { "泉州", "101230501" }, { "烟台", "101120501" }, { "徐州", "101190801" },
            { "常州", "101191101" }, { "南通", "101190501" }, { "洛阳", "101180901" }, { "开封", "101180801" },
            { "保定", "101090201" }, { "唐山", "101090501" }, { "廊坊", "101090601" }, { "秦皇岛", "101091101" },
            { "邯郸", "101091001" }, { "吉林", "101060201" }, { "大庆", "101050901" }, { "绵阳", "101270401" },
            { "乐山", "101271401" }, { "宜宾", "101271101" }, { "桂林", "101300501" }, { "柳州", "101300301" },
            { "三亚", "101310201" }, { "遵义", "101260201" }, { "咸阳", "101110200" }, { "宝鸡", "101110901" },
        };

        // 城市经纬度表（WGS-84 近似值）：本地定位拿到经纬度后找最近城市
        private static readonly Dictionary<string, double[]> CityLocs = new Dictionary<string, double[]>()
        {
            // 直辖市
            { "北京", new double[] { 39.9042, 116.4074 } }, { "上海", new double[] { 31.2304, 121.4737 } },
            { "天津", new double[] { 39.3434, 117.3616 } }, { "重庆", new double[] { 29.5630, 106.5516 } },
            // 省会
            { "哈尔滨", new double[] { 45.8038, 126.5349 } }, { "长春", new double[] { 43.8171, 125.3235 } },
            { "沈阳", new double[] { 41.8057, 123.4315 } }, { "呼和浩特", new double[] { 40.8424, 111.7490 } },
            { "石家庄", new double[] { 38.0428, 114.5149 } }, { "太原", new double[] { 37.8706, 112.5489 } },
            { "西安", new double[] { 34.3416, 108.9398 } }, { "济南", new double[] { 36.6512, 117.1201 } },
            { "乌鲁木齐", new double[] { 43.8256, 87.6168 } }, { "拉萨", new double[] { 29.6520, 91.1721 } },
            { "西宁", new double[] { 36.6171, 101.7782 } }, { "兰州", new double[] { 36.0611, 103.8343 } },
            { "银川", new double[] { 38.4872, 106.2309 } }, { "郑州", new double[] { 34.7466, 113.6254 } },
            { "南京", new double[] { 32.0603, 118.7969 } }, { "武汉", new double[] { 30.5928, 114.3055 } },
            { "杭州", new double[] { 30.2741, 120.1551 } }, { "合肥", new double[] { 31.8206, 117.2272 } },
            { "福州", new double[] { 26.0745, 119.2965 } }, { "南昌", new double[] { 28.6820, 115.8579 } },
            { "长沙", new double[] { 28.2282, 112.9388 } }, { "贵阳", new double[] { 26.6470, 106.6302 } },
            { "成都", new double[] { 30.5728, 104.0668 } }, { "广州", new double[] { 23.1291, 113.2644 } },
            { "昆明", new double[] { 24.8801, 102.8329 } }, { "南宁", new double[] { 22.8170, 108.3665 } },
            { "海口", new double[] { 20.0440, 110.1999 } },
            { "香港", new double[] { 22.3193, 114.1694 } }, { "澳门", new double[] { 22.1987, 113.5439 } },
            { "台北", new double[] { 25.0330, 121.5654 } },
            // 主要地级市
            { "深圳", new double[] { 22.5431, 114.0579 } }, { "珠海", new double[] { 22.2707, 113.5767 } },
            { "佛山", new double[] { 23.0218, 113.1219 } }, { "东莞", new double[] { 23.0207, 113.7518 } },
            { "中山", new double[] { 22.5176, 113.3928 } }, { "惠州", new double[] { 23.1115, 114.4158 } },
            { "汕头", new double[] { 23.3535, 116.6822 } }, { "湛江", new double[] { 21.2707, 110.3594 } },
            { "江门", new double[] { 22.5786, 113.0816 } }, { "肇庆", new double[] { 23.0468, 112.4723 } },
            { "青岛", new double[] { 36.0671, 120.3826 } }, { "大连", new double[] { 38.9140, 121.6147 } },
            { "厦门", new double[] { 24.4798, 118.0894 } }, { "苏州", new double[] { 31.2989, 120.5853 } },
            { "宁波", new double[] { 29.8683, 121.5440 } }, { "无锡", new double[] { 31.4912, 120.3119 } },
            { "温州", new double[] { 27.9938, 120.6994 } }, { "泉州", new double[] { 24.8741, 118.6757 } },
            { "烟台", new double[] { 37.4638, 121.4479 } }, { "徐州", new double[] { 34.2058, 117.2841 } },
            { "常州", new double[] { 31.8107, 119.9741 } }, { "南通", new double[] { 31.9802, 120.8943 } },
            { "洛阳", new double[] { 34.6197, 112.4540 } }, { "开封", new double[] { 34.7971, 114.3074 } },
            { "保定", new double[] { 38.8740, 115.4646 } }, { "唐山", new double[] { 39.6305, 118.1802 } },
            { "廊坊", new double[] { 39.5378, 116.6837 } }, { "秦皇岛", new double[] { 39.9355, 119.5997 } },
            { "邯郸", new double[] { 36.6256, 114.5391 } }, { "吉林", new double[] { 43.8378, 126.5496 } },
            { "大庆", new double[] { 46.5893, 125.1039 } }, { "绵阳", new double[] { 31.4675, 104.6796 } },
            { "乐山", new double[] { 29.5521, 103.7657 } }, { "宜宾", new double[] { 28.7513, 104.6417 } },
            { "桂林", new double[] { 25.2736, 110.2900 } }, { "柳州", new double[] { 24.3264, 109.4282 } },
            { "三亚", new double[] { 18.2528, 109.5119 } }, { "遵义", new double[] { 27.7254, 106.9273 } },
            { "咸阳", new double[] { 34.3294, 108.7089 } }, { "宝鸡", new double[] { 34.3619, 107.2373 } },
        };

        private static string CityNameToCode(string name)
        {
            if (string.IsNullOrEmpty(name)) return "";
            if (CityCodes.ContainsKey(name)) return CityCodes[name];
            foreach (KeyValuePair<string, string> kv in CityCodes)
            {
                if (kv.Key.Contains(name) || name.Contains(kv.Key)) return kv.Value;
            }
            return "";
        }

        private static string CityCodeSearch(string name)
        {
            try
            {
                string s = HttpGetUtf8("http://toy1.weather.com.cn/search?cityname=" + Uri.EscapeDataString(name), "http://www.weather.com.cn/");
                Match m = Regex.Match(s, "\"ref\"\\s*:\\s*\"(\\d+)");
                if (m.Success) return m.Groups[1].Value;
            }
            catch { }
            return "";
        }

        private void PromptCity()
        {
            string input = ShowPrompt("设置城市", "输入城市名（如：广州）或城市代码（如：101280101）：", _cityName);
            if (string.IsNullOrEmpty(input)) return;
            input = input.Trim();
            string code = "";
            string name = "";
            if (Regex.IsMatch(input, "^\\d+$"))
            {
                code = input;
            }
            else
            {
                name = NormalizeCity(input);
                code = CityNameToCode(name);
                if (string.IsNullOrEmpty(code)) code = CityCodeSearch(name);
            }
            if (string.IsNullOrEmpty(code))
            {
                SafeBubble("没找到这个城市(>_<)\n试试输入城市代码？");
                return;
            }
            _cityCode = code;
            if (string.IsNullOrEmpty(name)) name = input;
            _cityName = name;
            _cityLocated = true; // 手动设置后本会话不再自动重新定位
            SaveSettings();
            QueryWeather(true);
        }

        private static string ShowPrompt(string title, string prompt, string defaultValue)
        {
            using (Form f = new Form())
            {
                f.Text = title;
                f.FormBorderStyle = FormBorderStyle.FixedDialog;
                f.StartPosition = FormStartPosition.CenterScreen;
                f.ClientSize = new Size(380, 140);
                Label lbl = new Label { Text = prompt, Location = new Point(12, 12), AutoSize = true, MaximumSize = new Size(356, 64) };
                TextBox tb = new TextBox { Text = defaultValue, Location = new Point(12, 80), Width = 356 };
                Button ok = new Button { Text = "确定", DialogResult = DialogResult.OK, Location = new Point(196, 106), Width = 80 };
                Button cancel = new Button { Text = "取消", DialogResult = DialogResult.Cancel, Location = new Point(284, 106), Width = 80 };
                f.Controls.Add(lbl);
                f.Controls.Add(tb);
                f.Controls.Add(ok);
                f.Controls.Add(cancel);
                f.AcceptButton = ok;
                f.CancelButton = cancel;
                return f.ShowDialog() == DialogResult.OK ? tb.Text.Trim() : null;
            }
        }

        private void ShowBubble(string text)
        {
            if (_bubble != null)
            {
                _bubble.ShowBubble(text, PetScreenRect(), _topmost);
            }
        }

        private Rectangle PetScreenRect()
        {
            return new Rectangle(Location.X, Location.Y, ClientSize.Width, ClientSize.Height);
        }

        private void OnTick(object sender, EventArgs e)
        {
            if (_closing)
            {
                if (_winAlpha > 20) _winAlpha = (byte)(_winAlpha - 25);
                RenderFrame();
                if (_winAlpha <= 20) Close();
                return;
            }

            TickPomodoro();
            TickHealth();
            string today = DateTime.Now.ToString("yyyyMMdd");
            if (DateTime.Now.Hour >= 8 && _lastWeatherDay != today)
            {
                _lastWeatherDay = today;
                QueryWeather(true);
            }
            if (DateTime.UtcNow >= _nextWeatherRefresh)
            {
                QueryWeatherSilent();
            }
            if (DateTime.UtcNow >= _moodDecayAt)
            {
                _moodDecayAt = DateTime.UtcNow.AddSeconds(60);
                AddMood(-1);
            }
            TickWander();

            if (!IsAnimating() && DateTime.UtcNow >= _idleNextAt)
            {
                _idleNextAt = DateTime.UtcNow.AddMilliseconds(_rng.Next(8000, 18000));
                StartIdleAction();
            }

            if (_bubble != null && _bubble.Visible)
            {
                _bubble.Reposition(PetScreenRect());
            }

            RenderFrame();
        }

        private bool IsAnimating()
        {
            return DateTime.UtcNow < _animStart.AddMilliseconds(_animDur);
        }

        private void RenderFrame()
        {
            if (Handle == IntPtr.Zero || ClientSize.Width <= 0 || ClientSize.Height <= 0) return;
            int w = ClientSize.Width;
            int h = ClientSize.Height;
            try
            {
                using (Bitmap surface = new Bitmap(w, h, PixelFormat.Format32bppArgb))
                {
                    using (Graphics g = Graphics.FromImage(surface))
                    {
                        g.Clear(Color.Transparent);
                        g.SmoothingMode = SmoothingMode.AntiAlias;
                        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                        g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                        Pose p = ComputePose();
                        DrawPet(g, w, h, p);
                        DrawEffect(g, w, h);
                        if (_weatherFx.Length > 0) DrawWeatherFx(g, w, h, p);
                        DrawWeatherParticles(g, w, h);
                    }
                    LayeredPainter.Push(Handle, surface, Location.X, Location.Y, _winAlpha);
                }
            }
            catch { }
        }

        private struct Pose
        {
            public float sx, sy, rot, ox, oy;
        }

        private Pose ComputePose()
        {
            Pose p = new Pose();
            p.sx = 1f; p.sy = 1f; p.rot = 0f; p.ox = 0f; p.oy = 0f;
            if (_anim == "idle" || !IsAnimating())
            {
                double t = DateTime.UtcNow.Millisecond / 1600.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.018 * Math.Sin(t));
                if (_waddling)
                {
                    p.ox += (float)(3.5 * Math.Sin(_waddlePhase) * (float)_scale);
                    p.rot += (float)(2.5 * Math.Sin(_waddlePhase) * (float)_scale);
                }
                return p;
            }

            double k = (DateTime.UtcNow - _animStart).TotalMilliseconds / _animDur;
            if (k < 0) k = 0;
            if (k > 1) k = 1;
            double cw = _charW * _scale;
            double chh = _charH * _scale;

            if (_anim == "jump")
            {
                double lift = 0.26 * chh;
                if (k < 0.12)
                {
                    double q = k / 0.12;
                    p.sy = (float)(1 + 0.10 * Math.Sin(Math.PI * q));
                    p.sx = (float)(1 - 0.06 * Math.Sin(Math.PI * q));
                }
                else if (k < 0.85)
                {
                    double q = (k - 0.12) / 0.73;
                    p.oy = (float)(-lift * Math.Sin(Math.PI * q));
                }
                else
                {
                    double q = (k - 0.85) / 0.15;
                    p.sy = (float)(1 - 0.16 * Math.Sin(Math.PI * q));
                    p.sx = (float)(1 + 0.16 * Math.Sin(Math.PI * q));
                }
            }
            else if (_anim == "squash")
            {
                double v = Math.Sin(Math.PI * k);
                p.sy = (float)(1 - 0.26 * v);
                p.sx = (float)(1 + 0.26 * v);
                if (k > 0.55)
                {
                    double q = (k - 0.55) / 0.45;
                    p.oy = (float)(-0.10 * chh * Math.Sin(Math.PI * q));
                }
            }
            else if (_anim == "shake")
            {
                double decay = 1.0 - k;
                p.ox = (float)(Math.Sin(2 * Math.PI * 8 * k) * 0.035 * cw * decay);
                p.rot = (float)(Math.Sin(2 * Math.PI * 8 * k) * 4 * decay);
            }
            else if (_anim == "spin")
            {
                p.rot = (float)(360 * k);
            }
            else if (_anim == "nod")
            {
                p.rot = (float)(-10 * Math.Sin(Math.PI * k));
            }
            else if (_anim == "stretch")
            {
                p.sy = (float)(1 + 0.10 * Math.Sin(Math.PI * k));
                p.oy = (float)(-0.05 * chh * Math.Sin(Math.PI * k));
            }
            else if (_anim == "look")
            {
                p.rot = (float)(7 * Math.Sin(2 * Math.PI * k) * Math.Min(1, 2 * Math.Min(k, 1 - k)));
            }
            else if (_anim == "breath")
            {
                p.sy = (float)(1 + 0.05 * Math.Sin(2 * Math.PI * k));
                p.oy = (float)(-0.02 * chh * Math.Sin(2 * Math.PI * k));
            }
            else if (_anim == "talk")
            {
                p.rot = (float)(2 * Math.Sin(2 * Math.PI * 3 * k));
            }
            else if (_anim == "pose1" || _anim == "pose2")
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
            return p;
        }

        private void DrawPet(Graphics g, int w, int h, Pose p)
        {
            Bitmap src = CurrentPose();
            if (src == null) src = _char;
            if (src == null) return;
            float cx = w / 2f;
            float bottom = h - 3f;
            float cw = (float)(_charW * _scale) * p.sx;
            float chh = (float)(_charH * _scale) * p.sy;
            g.TranslateTransform(cx, bottom + p.oy);
            g.RotateTransform(p.rot);
            g.TranslateTransform(p.ox, 0f);
            if (src == _char)
            {
                g.DrawImage(src, new RectangleF(-cw / 2f, -chh, cw, chh));
            }
            else
            {
                float fit = Math.Min(cw / src.Width, chh / src.Height);
                float dw = src.Width * fit;
                float dh = src.Height * fit;
                g.DrawImage(src, new RectangleF(-dw / 2f, -dh, dw, dh));
            }
            g.ResetTransform();
        }

        private Bitmap CurrentPose()
        {
            if (_poseImg == "pose1") return _pose1;
            if (_poseImg == "pose2") return _pose2;
            return null;
        }

        private void DrawEffect(Graphics g, int w, int h)
        {
            if (_effect.Length == 0) return;
            double t = (DateTime.UtcNow - _effectStart).TotalMilliseconds / _effectDur;
            if (t < 0 || t > 1) return;
            int alpha = (int)(255 * (1.0 - t));
            if (alpha <= 4) return;

            float chh = (float)(_charH * _scale);
            float baseY = h - 3f - chh - 4f;
            float baseX = w / 2f;
            float drift = 34f * (float)_scale * (float)t;

            if (_effect == "bang")
            {
                DrawBang(g, baseX, baseY - drift, Math.Max(14f, w * 0.09f), alpha);
            }
            else if (_effect == "poji")
            {
                DrawSweat(g, baseX + w * 0.12f, baseY - drift, Math.Max(10f, w * 0.05f), alpha);
            }
            else if (_effect == "laugh")
            {
                DrawHeart(g, baseX - w * 0.10f, baseY - 20f - drift, Math.Max(10f, w * 0.06f), alpha);
                DrawHeart(g, baseX + w * 0.10f, baseY - 8f - drift, Math.Max(10f, w * 0.05f), alpha);
            }
            else if (_effect == "star")
            {
                DrawSparkle(g, baseX, baseY - 14f - drift, Math.Max(12f, w * 0.07f), alpha, (float)(t * 180));
                DrawSparkle(g, baseX - w * 0.14f, baseY - 4f - drift * 0.8f, Math.Max(8f, w * 0.045f), alpha, (float)(-t * 120));
                DrawSparkle(g, baseX + w * 0.13f, baseY - 6f - drift * 0.9f, Math.Max(8f, w * 0.045f), alpha, (float)(t * 90));
            }
            else if (_effect == "zzz")
            {
                DrawZzz(g, baseX + w * 0.10f, baseY - drift, Math.Max(11f, w * 0.055f), alpha);
            }
            else if (_effect == "music")
            {
                DrawMusic(g, baseX, baseY - 10f - drift, Math.Max(11f, w * 0.055f), alpha);
            }
            else if (_effect == "talk")
            {
                DrawHeart(g, baseX, baseY - 6f - drift, Math.Max(9f, w * 0.05f), alpha);
            }
            else if (_effect == "heart")
            {
                DrawHeart(g, baseX, baseY - 6f - drift, Math.Max(9f, w * 0.05f), alpha);
                DrawHeart(g, baseX - w * 0.09f, baseY - 20f - drift, Math.Max(8f, w * 0.05f), alpha);
            }
        }

        private void DrawHeart(Graphics g, float x, float y, float s, int alpha)
        {
            using (GraphicsPath path = new GraphicsPath())
            {
                path.AddEllipse(x - s * 0.9f, y - s * 0.65f, s, s);
                path.AddEllipse(x, y - s * 0.65f, s, s);
                path.AddPolygon(new PointF[] {
                    new PointF(x - s * 0.95f, y - s * 0.25f),
                    new PointF(x + s * 0.95f, y - s * 0.25f),
                    new PointF(x, y + s * 0.95f) });
                using (SolidBrush b = new SolidBrush(Color.FromArgb(alpha, 255, 105, 180)))
                {
                    g.FillPath(b, path);
                }
            }
        }

        private void DrawBang(Graphics g, float x, float y, float s, int alpha)
        {
            using (Font f = new Font("Microsoft YaHei", s * 1.1f, FontStyle.Bold))
            using (SolidBrush b = new SolidBrush(Color.FromArgb(alpha, 240, 80, 80)))
            {
                g.DrawString("!", f, b, x - s * 0.35f, y - s * 0.7f);
            }
        }

        private void DrawSweat(Graphics g, float x, float y, float s, int alpha)
        {
            using (GraphicsPath path = new GraphicsPath())
            {
                path.AddEllipse(x - s * 0.5f, y - s * 0.2f, s, s * 1.2f);
                path.AddPolygon(new PointF[] {
                    new PointF(x - s * 0.5f, y + s * 0.15f),
                    new PointF(x + s * 0.5f, y + s * 0.15f),
                    new PointF(x, y - s * 0.85f) });
                using (SolidBrush b = new SolidBrush(Color.FromArgb(alpha, 130, 200, 255)))
                {
                    g.FillPath(b, path);
                }
            }
        }

        private void DrawSparkle(Graphics g, float x, float y, float s, int alpha, float rot)
        {
            using (GraphicsPath path = new GraphicsPath())
            {
                PointF[] pts = new PointF[8];
                for (int i = 0; i < 8; i++)
                {
                    double ang = Math.PI / 4.0 * i + rot * Math.PI / 180.0;
                    double r = (i % 2 == 0) ? s * 0.55f : s * 0.18f;
                    pts[i] = new PointF(x + (float)(Math.Cos(ang) * r), y + (float)(Math.Sin(ang) * r));
                }
                path.AddPolygon(pts);
                using (SolidBrush b = new SolidBrush(Color.FromArgb(alpha, 255, 210, 70)))
                {
                    g.FillPath(b, path);
                }
            }
        }

        private void DrawZzz(Graphics g, float x, float y, float s, int alpha)
        {
            using (Font f = new Font("Microsoft YaHei", s, FontStyle.Bold))
            using (SolidBrush b = new SolidBrush(Color.FromArgb(alpha, 150, 195, 255)))
            {
                g.DrawString("Z", f, b, x, y - s * 2.2f);
                g.DrawString("z", f, b, x + s * 0.7f, y - s * 1.3f);
                g.DrawString("z", f, b, x + s * 1.3f, y - s * 0.5f);
            }
        }

        private void DrawMusic(Graphics g, float x, float y, float s, int alpha)
        {
            using (SolidBrush b = new SolidBrush(Color.FromArgb(alpha, 160, 110, 255)))
            {
                g.FillEllipse(b, x - s * 0.7f, y + s * 0.2f, s * 1.1f, s * 0.9f);
                g.FillRectangle(b, x - s * 0.15f, y - s * 1.3f, s * 0.32f, s * 1.7f);
                using (GraphicsPath path = new GraphicsPath())
                {
                    path.AddBezier(
                        new PointF(x + s * 0.15f, y - s * 1.3f),
                        new PointF(x + s * 0.9f, y - s * 1.1f),
                        new PointF(x + s * 0.85f, y - s * 0.4f),
                        new PointF(x + s * 0.35f, y - s * 0.35f));
                    using (Pen pen = new Pen(Color.FromArgb(alpha, 160, 110, 255), s * 0.22f))
                    {
                        pen.StartCap = LineCap.Round;
                        pen.EndCap = LineCap.Round;
                        g.DrawPath(pen, path);
                    }
                }
            }
        }

        internal static void RunSelfTest(string outDir)
        {
            PetForm f = new PetForm();
            f.CreateControl();
            f.RenderFrame();
            System.IO.File.WriteAllText(
                System.IO.Path.Combine(outDir, "layered_result.txt"),
                "UpdateLayeredWindow ok=" + LayeredPainter.LastUpdateOk.ToString());
            LayeredPainter.LastUpdateOk = false;
            string[] anims = new string[] { "idle", "jump", "squash", "shake", "pose1", "pose2", "nod", "stretch", "talk" };
            foreach (string a in anims)
            {
                f._anim = a;
                f._animStart = DateTime.UtcNow;
                f._animDur = 600;
                f._poseImg = (a == "pose1" || a == "pose2") ? a : "";
                f._effect = "star";
                f._effectStart = DateTime.UtcNow;
                f._effectDur = 500;
                f.SaveFrame(System.IO.Path.Combine(outDir, "frame_" + a + ".png"));
            }
            BubbleForm b = new BubbleForm();
            f._weatherFx = "";
            f._weatherParticle = "rain";
            f.SaveFrame(System.IO.Path.Combine(outDir, "frame_rain.png"));
            f._weatherFx = "";
            f._weatherParticle = "snow";
            f.SaveFrame(System.IO.Path.Combine(outDir, "frame_snow.png"));
            f._weatherFx = "hot";
            f._weatherParticle = "hot";
            f.EnsureWeatherOverlays(f._char);
            f.SaveFrame(System.IO.Path.Combine(outDir, "frame_hot.png"));
            f._anim = "pose1";
            f._poseImg = "pose1";
            f._weatherFx = "hot";
            f.SaveFrame(System.IO.Path.Combine(outDir, "frame_hot_pose1.png"));
            f._weatherFx = "cold";
            f._weatherParticle = "cold";
            f.SaveFrame(System.IO.Path.Combine(outDir, "frame_cold.png"));
            f._weatherFx = "";
            f._weatherParticle = "";
            b.CreateControl();
            b.SetText("测试气泡内容，看看文字排版～", 220, 60);
            b.SaveFrame(System.IO.Path.Combine(outDir, "bubble.png"));
            b.Close();
            try
            {
                string pf = f._phrasesPath;
                System.IO.File.WriteAllText(pf, "[点击]\n测试台词一号\n测试台词二号\n[姿势]\n姿势台词A\n", new System.Text.UTF8Encoding(true));
                f.LoadPhrases();
                System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "phrases_result.txt"),
                    "tap=" + f._tapPhrases.Count.ToString() + " first=" + f._tapPhrases[0] + " pose=" + f._posePhrases.Count.ToString());
                try { System.IO.File.Delete(pf); } catch { }
            }
            catch { }
            try
            {
                string testImg = System.IO.Path.Combine(outDir, "cutout_test.png");
                Bitmap t = new Bitmap(200, 200, PixelFormat.Format32bppArgb);
                using (Graphics g = Graphics.FromImage(t))
                {
                    g.Clear(Color.White);
                    using (SolidBrush brush = new SolidBrush(Color.Red))
                    {
                        g.FillEllipse(brush, 40, 40, 120, 120);
                    }
                }
                t.Save(testImg, ImageFormat.Png);
                t.Dispose();
                Bitmap cut = PrepareCharacterImage(testImg);
                int transparent = 0;
                if (cut != null)
                {
                    BitmapData bd = cut.LockBits(new Rectangle(0, 0, cut.Width, cut.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
                    int stride = bd.Stride;
                    byte[] px = new byte[stride * cut.Height];
                    Marshal.Copy(bd.Scan0, px, 0, px.Length);
                    for (int i = 3; i < px.Length; i += 4)
                    {
                        if (px[i] < 128) transparent++;
                    }
                    cut.UnlockBits(bd);
                    cut.Dispose();
                }
                System.IO.File.WriteAllText(System.IO.Path.Combine(outDir, "cutout_result.txt"),
                    "transparent=" + transparent.ToString() + " size=" + (cut == null ? "null" : "ok"));
                try { System.IO.File.Delete(testImg); } catch { }
            }
            catch { }
            Environment.Exit(0);
        }

        internal void SaveFrame(string path)
        {
            if (ClientSize.Width <= 0 || ClientSize.Height <= 0) return;
            int w = ClientSize.Width;
            int h = ClientSize.Height;
            using (Bitmap bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb))
            {
                using (Graphics g = Graphics.FromImage(bmp))
                {
                    g.Clear(Color.Transparent);
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    Pose p = ComputePose();
                    DrawPet(g, w, h, p);
                    DrawEffect(g, w, h);
                    if (_weatherFx.Length > 0) DrawWeatherFx(g, w, h, p);
                    DrawWeatherParticles(g, w, h);
                }
                bmp.Save(path, ImageFormat.Png);
            }
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            if (_menu != null && _menu.Visible)
            {
                _menuWasOpen = true;
                CloseMenu();
                return;
            }
            if (e.Button == MouseButtons.Left)
            {
                _mouseDown = true;
                _dragging = false;
                _downScreen = Cursor.Position;
                _grabOffset = new Point(Cursor.Position.X - Location.X, Cursor.Position.Y - Location.Y);
                Native.SetCapture(Handle);
            }
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (_mouseDown && !_dragging)
            {
                Point cur = Cursor.Position;
                if (Math.Abs(cur.X - _downScreen.X) > 5 || Math.Abs(cur.Y - _downScreen.Y) > 5)
                {
                    _dragging = true;
                    _effect = "bang";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 400;
                }
            }
            if (_dragging)
            {
                Point cur = Cursor.Position;
                Location = new Point(cur.X - _grabOffset.X, cur.Y - _grabOffset.Y);
                ClampToScreen();
            }
        }

        protected override void OnMouseUp(MouseEventArgs e)
        {
            base.OnMouseUp(e);
            if (_menuWasOpen)
            {
                _menuWasOpen = false;
                if (e.Button == MouseButtons.Right && _menu != null)
                {
                    Native.ReleaseCapture();
                    _menu.Show(this, e.Location);
                    InstallMenuHooks();
                }
                return;
            }
            if (e.Button == MouseButtons.Right)
            {
                if (_menu != null)
                {
                    Native.ReleaseCapture();
                    _menu.Show(this, e.Location);
                    InstallMenuHooks();
                }
                return;
            }
            if (e.Button == MouseButtons.Left)
            {
                Native.ReleaseCapture();
                bool wasDragging = _dragging;
                _mouseDown = false;
                _dragging = false;
                if (wasDragging)
                {
                    AddMood(4);
                    _effect = "heart";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 700;
                    ShowBubble(_dropPhrases[_rng.Next(_dropPhrases.Count)]);
                }
                else
                {
                    TriggerRandomInteraction();
                }
            }
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            base.OnMouseEnter(e);
            Native.SetCapture(Handle);
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            base.OnMouseLeave(e);
            if (!_mouseDown)
            {
                Native.ReleaseCapture();
            }
        }

        protected override void OnMouseWheel(MouseEventArgs e)
        {
            base.OnMouseWheel(e);
            double factor = e.Delta > 0 ? 1.1 : 1.0 / 1.1;
            ApplyScale(_scale * factor, true);
        }

    }

    internal class BubbleForm : Form
    {
        private string _text = "";
        private System.Windows.Forms.Timer _timer;
        private DateTime _hideAt;
        private byte _alpha = 255;
        private bool _above = true;
        private Font _font;
        private Size _textSize;
        private Rectangle _lastPetRect;

        public BubbleForm()
        {
            Text = "气泡";
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            TopMost = true;
            _timer = new System.Windows.Forms.Timer();
            _timer.Interval = 30;
            _timer.Tick += OnTick;
            _font = new Font("Microsoft YaHei", 13f);
        }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= Native.WS_EX_LAYERED | Native.WS_EX_TRANSPARENT | Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE;
                return cp;
            }
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            int ex = Native.GetWindowLong(Handle, Native.GWL_EXSTYLE);
            ex |= Native.WS_EX_LAYERED | Native.WS_EX_TRANSPARENT | Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE;
            Native.SetWindowLong(Handle, Native.GWL_EXSTYLE, ex);
        }

        public void ShowBubble(string text, Rectangle petRect, bool topmost)
        {
            _text = text ?? "";
            _lastPetRect = petRect;
            TopMost = topmost;

            SizeF sz;
            using (Bitmap tmp = new Bitmap(1, 1))
            using (Graphics g = Graphics.FromImage(tmp))
            {
                sz = g.MeasureString(_text, _font, 230);
            }
            _textSize = new Size((int)Math.Ceiling(sz.Width), (int)Math.Ceiling(sz.Height));

            int pad = 12;
            int tail = 14;
            int bw = _textSize.Width + pad * 2 + 10;
            int bh = _textSize.Height + pad * 2 + tail;
            Size = new Size(bw, bh);
            LayoutAroundPet(petRect);

            Render();
            if (!Visible) Show();
            _hideAt = DateTime.UtcNow.AddMilliseconds(3200);
            _alpha = 255;
            _timer.Start();
        }

        public void Reposition(Rectangle petRect)
        {
            if (!Visible) return;
            _lastPetRect = petRect;
            LayoutAroundPet(petRect);
            Render();
        }

        private void LayoutAroundPet(Rectangle petRect)
        {
            int bw = ClientSize.Width;
            int bh = ClientSize.Height;
            int x = petRect.X + petRect.Width / 2 - bw / 2;
            int y = petRect.Y - bh - 8;
            _above = true;
            if (y < 0)
            {
                y = petRect.Bottom + 8;
                _above = false;
            }
            Rectangle wa = Screen.FromPoint(new Point(petRect.X, petRect.Y)).WorkingArea;
            if (x < wa.X + 4) x = wa.X + 4;
            if (x + bw > wa.Right - 4) x = wa.Right - 4 - bw;
            Location = new Point(x, y);
        }

        private void OnTick(object sender, EventArgs e)
        {
            if (DateTime.UtcNow >= _hideAt)
            {
                if (_alpha > 30) _alpha = (byte)(_alpha - 22);
                else
                {
                    _timer.Stop();
                    Hide();
                    return;
                }
                Render();
            }
        }

        internal void SetText(string text, int w, int h)
        {
            _text = text ?? "";
            _above = true;
            Size = new Size(w, h);
        }

        internal void SaveFrame(string path)
        {
            if (ClientSize.Width <= 0 || ClientSize.Height <= 0) return;
            RenderSurface(ClientSize.Width, ClientSize.Height).Save(path, ImageFormat.Png);
        }

        private Bitmap RenderSurface(int w, int h)
        {
            Bitmap surface = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(surface))
            {
                g.Clear(Color.Transparent);
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;

                Rectangle body = new Rectangle(2, 2, w - 5, h - 18);
                using (GraphicsPath path = RoundedRect(body, 13))
                {
                    using (SolidBrush bg = new SolidBrush(Color.FromArgb(_alpha > 245 ? (byte)238 : _alpha, 255, 255, 255)))
                    {
                        g.FillPath(bg, path);
                    }
                    using (Pen pen = new Pen(Color.FromArgb(_alpha, 200, 200, 205), 1.2f))
                    {
                        g.DrawPath(pen, path);
                    }
                }
                int cx = w / 2;
                Point[] tri;
                if (_above)
                {
                    tri = new Point[] { new Point(cx - 9, h - 17), new Point(cx + 9, h - 17), new Point(cx, h - 2) };
                }
                else
                {
                    tri = new Point[] { new Point(cx - 9, 17), new Point(cx + 9, 17), new Point(cx, 2) };
                }
                using (SolidBrush tb = new SolidBrush(Color.FromArgb(_alpha > 245 ? (byte)238 : _alpha, 255, 255, 255)))
                {
                    g.FillPolygon(tb, tri);
                }

                RectangleF textRect = new RectangleF(9, 8, w - 18, h - 26);
                using (SolidBrush tb2 = new SolidBrush(Color.FromArgb(_alpha, 60, 60, 70)))
                {
                    StringFormat sf = new StringFormat();
                    sf.Alignment = StringAlignment.Center;
                    sf.LineAlignment = StringAlignment.Near;
                    sf.Trimming = StringTrimming.None;
                    g.DrawString(_text, _font, tb2, textRect, sf);
                    sf.Dispose();
                }
            }
            return surface;
        }

        private void Render()
        {
            if (Handle == IntPtr.Zero || ClientSize.Width <= 0 || ClientSize.Height <= 0) return;
            int w = ClientSize.Width;
            int h = ClientSize.Height;
            try
            {
                using (Bitmap surface = RenderSurface(w, h))
                {
                    LayeredPainter.Push(Handle, surface, Location.X, Location.Y, _alpha);
                }
            }
            catch { }
        }

        private static GraphicsPath RoundedRect(Rectangle r, int radius)
        {
            GraphicsPath path = new GraphicsPath();
            int d = radius * 2;
            path.AddArc(r.X, r.Y, d, d, 180, 90);
            path.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            path.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            path.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            path.CloseFigure();
            return path;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && _font != null)
            {
                _font.Dispose();
                _font = null;
            }
            base.Dispose(disposing);
        }
    }
}
