from __future__ import annotations

import sqlite3


def connect(sqlite_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA synchronous=NORMAL;")  # Speed optimization for WAL
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
