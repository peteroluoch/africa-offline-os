import sqlite3
db = sqlite3.connect("aos.db")
db.row_factory = sqlite3.Row
cursor = db.cursor()

cursor.execute("SELECT * FROM roles")
print("--- ROLES ---")
for row in cursor.fetchall():
    print(dict(row))

db.close()
