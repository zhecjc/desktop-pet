# -*- coding: utf-8 -*-
import sys

src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()

frm = """            b.SetText("测试气泡内容，看看文字排版～", 220, 60);
            b.SaveFrame(System.IO.Path.Combine(outDir, "bubble.png"));
            b.Close();
            Environment.Exit(0);"""
to = """            b.SetText("测试气泡内容，看看文字排版～", 220, 60);
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
            Environment.Exit(0);"""
n = src.count(frm)
print("match:", n)
if n == 1:
    src = src.replace(frm, to)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("selftest phrases added, len:", len(src))
else:
    print("FAIL")
