import sqlite3
import json

db = sqlite3.connect("aos.db")
db.row_factory = sqlite3.Row
cursor = db.cursor()

print("--- OPERATORS ---")
cursor.execute("SELECT id, username, role_id FROM operators")
for row in cursor.fetchall():
    print(dict(row))

print("\n--- TELEGRAM USERS ---")
cursor.execute("SELECT chat_id, username, roles FROM telegram_users")
for row in cursor.fetchall():
    user = dict(row)
    user['roles'] = json.loads(user['roles'])
    print(user)

db.close()
