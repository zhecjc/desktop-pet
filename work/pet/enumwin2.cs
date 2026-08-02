using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class EnumWin2 {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }

    public static EnumWindowsProc _cb;
    public static uint _target;
    public static List<string> _results = new List<string>();

    public static bool Callback(IntPtr hWnd, IntPtr lParam) {
        uint pid;
        GetWindowThreadProcessId(hWnd, out pid);
        if (pid == _target) {
            StringBuilder t = new StringBuilder(512); GetWindowText(hWnd, t, 512);
            StringBuilder c = new StringBuilder(256); GetClassName(hWnd, c, 256);
            RECT r; GetWindowRect(hWnd, out r);
            string line = string.Format("hwnd=0x{0:X} vis={1} class={2} title=[{3}] rect=({4},{5},{6},{7})",
                hWnd.ToInt64(), IsWindowVisible(hWnd), c, t, r.Left, r.Top, r.Right, r.Bottom);
            _results.Add(line);
            Console.WriteLine(line);
        }
        return true;
    }

    public static int Main(string[] args) {
        _target = uint.Parse(args[0]);
        _cb = new EnumWindowsProc(Callback);
        bool ok = EnumWindows(_cb, IntPtr.Zero);
        Console.WriteLine("enum ok=" + ok + " totalForPid=" + _results.Count);
        return 0;
    }
}
