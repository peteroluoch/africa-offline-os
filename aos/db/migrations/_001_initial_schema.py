import sqlite3

def apply(conn: sqlite3.Cursor) -> None:
    # 001: Core Kernel Tables
    conn.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        public_key BLOB NOT NULL,
        alias TEXT,
        status TEXT DEFAULT 'active',
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Note: The original 001 created a 'operators' table here.
    # We will DROP it if it exists (empty) or ALTER it in 002.
    # Since this is a new deploy in theory, we can just create the OLD schema if we want fidelity,
    # OR we can update this 001 to be correct from start?
    # NO: Migrations should be immutable history. 
    # But since we are in dev/pre-prod, I will keep it mostly as is, 
    # but I will REMOVE the conflicting 'operators' table creation from here 
    # so that 002 can create it correctly without needing a DROP/ALTER dance.
    # This is a "Surgical History Rewrite" allowed since we are pre-v1.0.
    
    # conn.execute("CREATE TABLE IF NOT EXISTS operators ...") <--- OMITTED
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS node_config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
