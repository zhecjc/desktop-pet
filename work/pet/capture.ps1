Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$bmp = New-Object System.Drawing.Bitmap($wa.Width, $wa.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($wa.Left, $wa.Top, 0, 0, $bmp.Size)
$g.Dispose()
$bmp.Save("work\pet\screen_full.png", [System.Drawing.Imaging.ImageFormat]::Png)
# 分析右下角区域（桌宠默认位置附近）：找非桌面像素
$colors = @{}
$sx = [Math]::Max(0, $wa.Width - 900)
$sy = [Math]::Max(0, $wa.Height - 900)
for ($y = $sy; $y -lt $wa.Height; $y += 3) {
  for ($x = $sx; $x -lt $wa.Width; $x += 3) {
    $c = $bmp.GetPixel($x, $y)
    $key = "{0},{1},{2}" -f ($c.R -band 0xF0), ($c.G -band 0xF0), ($c.B -band 0xF0)
    if ($colors.ContainsKey($key)) { $colors[$key]++ } else { $colors[$key] = 1 }
  }
}
$colors.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 12 | ForEach-Object { "{0} x{1}" -f $_.Key, $_.Value }
$bmp.Dispose()
