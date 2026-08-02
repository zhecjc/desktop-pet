src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()
for marker in ['private void BuildMenu()', 'private void OnTick', 'private void SaveSettings()', 'private void LoadSettings()', 'private void ClampToScreen()']:
    i = src.find(marker)
    if i >= 0:
        print("=== " + marker + " ===")
        print(src[i:i+1200])
        print()
