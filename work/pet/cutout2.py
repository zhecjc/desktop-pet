# -*- coding: utf-8 -*-
import sys

src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()

frm = """        private static Bitmap TryLoadBitmap(string path)
        {
            try
            {
                if (File.Exists(path)) return new Bitmap(path);
            }
            catch { }
            return null;
        }"""

to = """        private static string FindImage(string dir, string baseName)
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
        }"""

n = src.count(frm)
print("match:", n)
if n == 1:
    src = src.replace(frm, to)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("cutout methods added, len:", len(src))
else:
    print("FAIL")
