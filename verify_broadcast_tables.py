import sqlite3
from aos.db.engine import connect

def check_tables():
    conn = connect("aos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected = ['broadcasts', 'broadcast_audit_logs', 'broadcast_deliveries']
    for table in expected:
        if table in tables:
            print(f"✅ Table {table} exists.")
            cursor.execute(f"PRAGMA table_info({table})")
            info = cursor.fetchall()
            print(f"Columns: {[col[1] for col in info]}")
        else:
            print(f"❌ Table {table} is missing.")
    conn.close()

if __name__ == "__main__":
    check_tables()
