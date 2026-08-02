import sqlite3
conn = sqlite3.connect(r"C:\Users\zhezhe\AppData\Roaming\KuGou8\playlistV3.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("TABLES:", tables)
for (t,) in tables:
    try:
        cols = [c[1] for c in cur.execute("PRAGMA table_info(%s)" % t).fetchall()]
        print("\nTABLE:", t, cols)
        cur.execute("SELECT * FROM %s LIMIT 5" % t)
        for row in cur.fetchall():
            print("  ", str(row)[:300])
    except Exception as e:
        print("ERR", t, e)
