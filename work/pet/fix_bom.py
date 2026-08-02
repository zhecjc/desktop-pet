# -*- coding: utf-8 -*-
src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()

frm = """        private static string DecodeText(byte[] bytes)
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
        }"""
to = """        private static string DecodeText(byte[] bytes)
        {
            try
            {
                string s = new System.Text.UTF8Encoding(false, true).GetString(bytes);
                if (s.Length > 0 && s[0] == '\\uFEFF') s = s.Substring(1);
                return s;
            }
            catch
            {
                try { return System.Text.Encoding.GetEncoding(936).GetString(bytes); }
                catch { return System.Text.Encoding.Default.GetString(bytes); }
            }
        }"""
n = src.count(frm)
print("match:", n)
if n == 1:
    src = src.replace(frm, to)
    with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
        f.write(src)
    print("BOM fix applied")
else:
    print("FAIL")
