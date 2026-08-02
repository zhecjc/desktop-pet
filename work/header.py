with open(r"C:\Users\zhezhe\AppData\Roaming\KuGou8\playlistV3.db", "rb") as f:
    data = f.read(64)
print(data)
print(data[:16].hex())
with open(r"C:\Users\zhezhe\AppData\Roaming\KuGou8\KGMusicV3.db", "rb") as f:
    data2 = f.read(16)
print(data2)
print(data2.hex())
