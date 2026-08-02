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

# P6: DrawPet 支持姿势图（保持角色动画拉伸，姿势图等比适配）
rep("""        private void DrawPet(Graphics g, int w, int h, Pose p)
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
        }""",
    """        private void DrawPet(Graphics g, int w, int h, Pose p)
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
        }""", "drawpet")

# P7: ComputePose 增加 pose1/pose2 分支（轻微呼吸/摇摆）
rep("""            else if (_anim == "talk")
            {
                p.rot = (float)(2 * Math.Sin(2 * Math.PI * 3 * k));
            }
            return p;""",
    """            else if (_anim == "talk")
            {
                p.rot = (float)(2 * Math.Sin(2 * Math.PI * 3 * k));
            }
            else if (_anim == "pose1")
            {
                double t = DateTime.UtcNow.TimeOfDay.TotalMilliseconds / 900.0 * 2.0 * Math.PI;
                p.sy = (float)(1.0 + 0.02 * Math.Sin(t));
                p.oy = (float)(-2.0 * Math.Sin(t) * (float)_scale);
            }
            else if (_anim == "pose2")
            {
                double t = DateTime.UtcNow.TimeOfDay.TotalMilliseconds / 1100.0 * 2.0 * Math.PI;
                p.rot = (float)(2.0 * Math.Sin(t));
                p.oy = (float)(-1.5 * Math.Sin(t * 2) * (float)_scale);
            }
            return p;""", "poseposes")

# P8: 自检动画列表（去掉 spin，加 pose1/pose2）
rep("""            string[] anims = new string[] { "idle", "jump", "squash", "shake", "spin", "nod", "stretch", "talk" };""",
    """            string[] anims = new string[] { "idle", "jump", "squash", "shake", "pose1", "pose2", "nod", "stretch", "talk" };""", "selftest")

with open(r"work\pet\DesktopPet.cs", "w", encoding="utf-8-sig") as f:
    f.write(src)
print("saved P6-P8, len:", len(src))
