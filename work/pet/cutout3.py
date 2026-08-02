# -*- coding: utf-8 -*-
src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()

frm = """                try { System.IO.File.Delete(pf); } catch { }
            }
            catch { }
            Environment.Exit(0);"""
to = """                try { System.IO.File.Delete(pf); } catch { }
            }
            catch { }
            try
            {
                string testImg = System.IO.Path.Combine(outDir, "cutout_test.png");
                Bitmap t = new Bitmap(200, 200, PixelFormat.Format32bppArgb);
                using (Graphics g = Graphics.FromImage(t))
                {
                    g.Clear(Color.White);
                    using (SolidBrush b = new SolidBrush(Color.Red))
                    {
                        g.FillEllipse(b, 40, 40, 120, 120);
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
            Environment.Exit(0);"""
n = src.count(frm)
print("match:", n)
if n == 1:
    src = src.replace(frm, to)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("cutout selftest added, len:", len(src))
else:
    print("FAIL")
