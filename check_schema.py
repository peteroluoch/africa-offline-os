import sqlite3
db = sqlite3.connect("aos.db")
cursor = db.cursor()

cursor.execute("PRAGMA table_info(telegram_users)")
print("--- TELEGRAM USERS SCHEMA ---")
for row in cursor.fetchall():
    print(row)

cursor.execute("PRAGMA table_info(operators)")
print("\n--- OPERATORS SCHEMA ---")
for row in cursor.fetchall():
    print(row)

db.close()
