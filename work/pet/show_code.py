src = open(r"work\pet\DesktopPet.cs", "r", encoding="utf-8-sig").read()
for marker in ['private static void Main', 'foreach (string a in anims)', 'else if (_anim == "pose1")']:
    i = src.find(marker)
    if i >= 0:
        print("=== " + marker + " ===")
        print(src[i:i+700])
        print()
