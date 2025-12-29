import sqlite3
import os

db_paths = ["aos.db", "data/aos.db"]
for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"Checking database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(operators)")
            columns = cursor.fetchall()
            print("Columns in 'operators' table:")
            for col in columns:
                print(col)
            
            cursor.execute("SELECT name FROM roles")
            roles = cursor.fetchall()
            print("\nRoles in database:")
            for role in roles:
                print(role[0])
            
            # Check migrations table
            cursor.execute("SELECT version_id FROM schema_migrations")
            migrations = cursor.fetchall()
            print("\nApplied migrations:")
            for m in migrations:
                print(f"Version {m[0]}")
        except Exception as e:
            print(f"Error checking {db_path}: {e}")
        
        conn.close()
        print("-" * 20)
