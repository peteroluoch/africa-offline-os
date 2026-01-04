from __future__ import annotations

import sqlite3


def connect(sqlite_path: str) -> sqlite3.Connection:
    """
    Connect to SQLite with production-grade settings.
    
    Optimizations:
    - WAL mode: Crash-safe, concurrent reads
    - NORMAL synchronous: Balance safety/performance
    - 64MB cache: Reduce disk I/O
    - MEMORY temp store: Faster temp operations
    """
    conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    
    # CRITICAL: WAL mode for crash safety and concurrent reads
    conn.execute("PRAGMA journal_mode=WAL;")
    # Power failure hardening: NORMAL is faster than FULL but still very safe with WAL
    conn.execute("PRAGMA synchronous=NORMAL;")
    
    # Run a quick integrity check on startup
    try:
        cursor = conn.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        if result[0] != "ok":
            # In a real environment, we'd log this to the persistent system log
            print(f"DATABASE INTEGRITY WARNING: {result[0]}")
    except Exception as e:
        print(f"FAILED TO RUN INTEGRITY CHECK: {e}")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA synchronous=NORMAL;")  # Balance safety/performance
    
    # Performance optimizations for edge deployment
    conn.execute("PRAGMA cache_size=-64000;")   # 64MB cache (negative = KB)
    conn.execute("PRAGMA temp_store=MEMORY;")   # Use RAM for temp tables
    conn.execute("PRAGMA mmap_size=268435456;") # 256MB memory-mapped I/O
    
    # Set row factory for dict-like access
    conn.row_factory = sqlite3.Row
    
    return conn

from contextlib import contextmanager


@contextmanager
def transaction(conn: sqlite3.Connection):
    """
    Context manager for atomic SQLite transactions.
    Rolls back on any exception.
    """
    try:
        conn.execute("BEGIN TRANSACTION;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def get_journal_mode(conn: sqlite3.Connection) -> str:
    row = conn.execute("PRAGMA journal_mode;").fetchone()
    return str(row[0]) if row else ""
