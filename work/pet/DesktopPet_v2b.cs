using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;

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

        public const int GWL_EXSTYLE = -20;
        public const int WS_EX_LAYERED = 0x00080000;
        public const int WS_EX_TOOLWINDOW = 0x00000080;
        public const int WS_EX_NOACTIVATE = 0x08000000;
        public const int WS_EX_TRANSPARENT = 0x00000020;
        public const int ULW_ALPHA = 0x00000002;
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
            using (new System.Threading.Mutex(true, "DesktopPet_SingleInstance_zh", out createdNew))
            {
                if (!createdNew) return;
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
        private ToolStripMenuItem[] _miSizes;

        private byte _winAlpha = 255;
        private bool _closing;

        private string _settingsPath;

        private static readonly string[] TapPhrases = new string[]
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

        private static readonly string[] IdlePhrases = new string[]
        {
            "呼…好安静呀～",
            "这里是我的地盘！",
            "主人加油，我陪着你～",
            "Zzz… 不许吵我…",
            "今天也是美好的一天～",
        };

        private static readonly string[] DropPhrases = new string[]
        {
            "放我下来啦！",
            "轻拿轻放！",
            "举高高！再来一次！",
            "呼，站稳了～",
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
            LoadCharacter();
            LoadSettings();
            ApplyScale(_scale, false);

            Rectangle wa = Screen.PrimaryScreen.WorkingArea;
            Location = new Point(wa.Right - ClientSize.Width - 40, wa.Bottom - ClientSize.Height - 30);

            _bubble = new BubbleForm();
            BuildMenu();

            _timer = new System.Windows.Forms.Timer();
            _timer.Interval = 33;
            _timer.Tick += OnTick;
            _idleNextAt = DateTime.UtcNow.AddMilliseconds(_rng.Next(8000, 16000));
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
                           "topmost=" + (_topmost ? "1" : "0") + "\r\n";
                File.WriteAllText(_settingsPath, s);
            }
            catch { }
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
        }

        private static string PercentText(double s)
        {
            return ((int)Math.Round(s * 100)).ToString() + "%";
        }
        private void TriggerRandomInteraction()
        {
            int r = _rng.Next(6);
            switch (r)
            {
                case 0: StartAnim("jump", 900, "bang", 500); break;
                case 1: StartAnim("squash", 750, "poji", 600); break;
                case 2: StartAnim("shake", 750, "laugh", 700); break;
                case 3: StartAnim("spin", 1050, "star", 900); break;
                case 4: StartAnim("nod", 800, "talk", 700); break;
                default: StartAnim("talk", 1100, "music", 800); break;
            }
            ShowBubble(TapPhrases[_rng.Next(TapPhrases.Length)]);
        }

        private void StartIdleAction()
        {
            int r = _rng.Next(5);
            switch (r)
            {
                case 0: StartAnim("nod", 800, "", 0); break;
                case 1: StartAnim("stretch", 1300, "zzz", 900); break;
                case 2: StartAnim("look", 1400, "", 0); break;
                case 3: StartAnim("breath", 900, "zzz", 700); break;
                default: StartAnim("squash", 700, "poji", 500); break;
            }
            if (_rng.Next(4) == 0)
            {
                ShowBubble(IdlePhrases[_rng.Next(IdlePhrases.Length)]);
            }
        }

        private void StartAnim(string name, double durMs, string effect, double effectMs)
        {
            _anim = name;
            _animStart = DateTime.UtcNow;
            _animDur = durMs;
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
            return p;
        }

        private void DrawPet(Graphics g, int w, int h, Pose p)
        {
            if (_char == null) return;
            float cx = w / 2f;
            float bottom = h - 3f;
            float cw = (float)(_charW * _scale) * p.sx;
            float chh = (float)(_charH * _scale) * p.sy;
            g.TranslateTransform(cx, bottom + p.oy);
            g.RotateTransform(p.rot);
            g.TranslateTransform(p.ox, 0f);
            g.DrawImage(_char, new RectangleF(-cw / 2f, -chh, cw, chh));
            g.ResetTransform();
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
            string[] anims = new string[] { "idle", "jump", "squash", "shake", "spin", "nod", "stretch", "talk" };
            foreach (string a in anims)
            {
                f._anim = a;
                f._animStart = DateTime.UtcNow;
                f._animDur = 600;
                f._effect = "star";
                f._effectStart = DateTime.UtcNow;
                f._effectDur = 500;
                f.SaveFrame(System.IO.Path.Combine(outDir, "frame_" + a + ".png"));
            }
            BubbleForm b = new BubbleForm();
            b.CreateControl();
            b.SetText("测试气泡内容，看看文字排版～", 220, 60);
            b.SaveFrame(System.IO.Path.Combine(outDir, "bubble.png"));
            b.Close();
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
                }
                bmp.Save(path, ImageFormat.Png);
            }
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
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
            if (e.Button == MouseButtons.Right)
            {
                if (_menu != null)
                {
                    UpdateSizeChecks();
                    _menu.Show(this, e.Location);
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
                    _effect = "heart";
                    _effectStart = DateTime.UtcNow;
                    _effectDur = 700;
                    ShowBubble(DropPhrases[_rng.Next(DropPhrases.Length)]);
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

        private void UpdateSizeChecks()
        {
            if (_miSizes == null) return;
            int best = 0;
            double bestDiff = double.MaxValue;
            for (int i = 0; i < _miSizes.Length; i++)
            {
                double s = 0.5 + 0.25 * i;
                if (i >= 3) s = 1.0 + 0.25 * (i - 2);
                if (i >= 5) s = 2.0;
                double diff = Math.Abs(_scale - s);
                if (diff < bestDiff) { bestDiff = diff; best = i; }
            }
            for (int i = 0; i < _miSizes.Length; i++)
            {
                _miSizes[i].Checked = (i == best);
            }
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
