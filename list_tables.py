import sqlite3
db = sqlite3.connect("aos.db")
cursor = db.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("--- TABLES ---")
for row in cursor.fetchall():
    print(row[0])

db.close()
