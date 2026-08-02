Add-Type @"
using System;
using System.Runtime.InteropServices;
public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
public class WinApi {
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
}
"@
$targetPid = (Get-Process -Name "桌宠").Id
$found = @()
$cb = [WinApi+EnumWindowsProc]{
    param($hwnd, $lparam)
    $pid2 = 0
    [WinApi]::GetWindowThreadProcessId($hwnd, [ref]$pid2) | Out-Null
    if ($pid2 -eq $targetPid -and [WinApi]::IsWindowVisible($hwnd)) {
        $r = New-Object RECT
        [WinApi]::GetWindowRect($hwnd, [ref]$r) | Out-Null
        $sb = New-Object System.Text.StringBuilder 256
        [WinApi]::GetWindowText($hwnd, $sb, 256) | Out-Null
        $script:found += [PSCustomObject]@{ Hwnd = $hwnd; Title = $sb.ToString(); L=$r.Left; T=$r.Top; R=$r.Right; B=$r.Bottom; W=$r.Right-$r.Left; H=$r.Bottom-$r.Top }
    }
    return $true
}
[WinApi]::EnumWindows($cb, [IntPtr]::Zero) | Out-Null
$script:found | Format-List
