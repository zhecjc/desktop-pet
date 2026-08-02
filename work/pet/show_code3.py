src = open(r'work\pet\DesktopPet.cs', 'r', encoding='utf-8-sig').read()
for marker in ['private bool LoadCharacterFromFolder', 'private void ApplySavedCharacter', 'private static Bitmap TryLoadBitmap', 'private void RefreshCharacterMenu']:
    i = src.find(marker)
    if i >= 0:
        print('=== ' + marker + ' ===')
        print(src[i:i+800])
        print()

