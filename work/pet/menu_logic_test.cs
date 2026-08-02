using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace DesktopPet
{
    internal class PetTestForm : PetForm
    {
        public void FireRightUp(int x, int y)
        {
            OnMouseUp(new MouseEventArgs(MouseButtons.Right, 1, x, y, 0));
        }

        public void FireLeftDown(int x, int y)
        {
            OnMouseDown(new MouseEventArgs(MouseButtons.Left, 1, x, y, 0));
        }

        public void FireLeftUp(int x, int y)
        {
            OnMouseUp(new MouseEventArgs(MouseButtons.Left, 1, x, y, 0));
        }

        public object GetField(string name)
        {
            FieldInfo fi = typeof(PetForm).GetField(name, BindingFlags.NonPublic | BindingFlags.Instance);
            return fi == null ? null : fi.GetValue(this);
        }

        public object InvokeMethod(string name, params object[] args)
        {
            MethodInfo mi = typeof(PetForm).GetMethod(name, BindingFlags.NonPublic | BindingFlags.Instance);
            return mi == null ? null : mi.Invoke(this, args);
        }
    }

    internal static class MenuLogicTest
    {
        private static void Log(string path, string text)
        {
            File.AppendAllText(path, text + "\r\n");
        }

        [STAThread]
        private static void Main(string[] args)
        {
            string logPath = (args.Length > 0) ? args[0] : "menu_logic_result.txt";
            try { File.Delete(logPath); } catch { }

            PetTestForm f = new PetTestForm();
            f.Show();
            Application.DoEvents();

            // 1) 右键弹菜单
            f.FireRightUp(10, 10);
            Application.DoEvents();
            bool visible1 = MenuVisible(f);
            IntPtr mouseHook1 = (IntPtr)f.GetField("_menuHookMouse");
            IntPtr keyHook1 = (IntPtr)f.GetField("_menuHookKey");
            Log(logPath, "after right-click: menuVisible=" + visible1 +
                " mouseHook=" + (mouseHook1 != IntPtr.Zero) +
                " keyHook=" + (keyHook1 != IntPtr.Zero));

            if (!visible1)
            {
                Log(logPath, "FAIL: menu did not open");
                f.Close();
                return;
            }

            // 2) 判定逻辑：菜单外某点 → 应判定为“不在菜单内”（可安全关闭）
            ContextMenuStrip menu = (ContextMenuStrip)f.GetField("_menu");
            Point inside = new Point(menu.Location.X + 5, menu.Location.Y + 5);
            Point outside = new Point(menu.Location.X - 60, menu.Location.Y - 60);
            bool insideHit = (bool)f.InvokeMethod("IsPointInsideMenu", inside);
            bool outsideHit = (bool)f.InvokeMethod("IsPointInsideMenu", outside);
            Log(logPath, "IsPointInsideMenu: inside=" + insideHit + " outside=" + outsideHit);

            // 3) 模拟钩子判定“点在菜单外”→ 关闭菜单并卸载钩子
            f.InvokeMethod("CloseMenu");
            Application.DoEvents();
            bool visible2 = MenuVisible(f);
            IntPtr mouseHook2 = (IntPtr)f.GetField("_menuHookMouse");
            IntPtr keyHook2 = (IntPtr)f.GetField("_menuHookKey");
            Log(logPath, "after CloseMenu: menuVisible=" + visible2 +
                " mouseHook=" + (mouseHook2 != IntPtr.Zero) +
                " keyHook=" + (keyHook2 != IntPtr.Zero));

            // 4) 再次弹菜单，Esc 应关闭
            f.FireRightUp(10, 10);
            Application.DoEvents();
            bool visible3 = MenuVisible(f);
            IntPtr kbd = System.Runtime.InteropServices.Marshal.AllocHGlobal(8);
            System.Runtime.InteropServices.Marshal.WriteInt32(kbd, Native.VK_ESCAPE);
            f.InvokeMethod("MenuKeyHookProc", 0, new IntPtr(Native.WM_KEYDOWN), kbd);
            System.Runtime.InteropServices.Marshal.FreeHGlobal(kbd);
            Application.DoEvents();
            bool visible4 = MenuVisible(f);
            Log(logPath, "Esc close: before=" + visible3 + " after=" + visible4);

            // 5) 再弹菜单，点击宠物本身（左键）→ 关闭且不触发互动
            f.FireRightUp(10, 10);
            Application.DoEvents();
            f.FireLeftDown(10, 10);
            f.FireLeftUp(10, 10);
            Application.DoEvents();
            bool visible5 = MenuVisible(f);
            string effect = (string)f.GetField("_effect");
            Log(logPath, "pet click close: menuVisible=" + visible5 + " effect='" + effect + "'");

            f.Close();
            Log(logPath, "=== done ===");
        }

        private static bool MenuVisible(PetTestForm f)
        {
            ContextMenuStrip menu = (ContextMenuStrip)f.GetField("_menu");
            return menu != null && menu.Visible;
        }
    }
}
