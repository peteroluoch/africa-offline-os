from aos.db.engine import connect, get_journal_mode


def test_sqlite_engine_uses_wal_mode(tmp_path) -> None:
    db_path = tmp_path / "aos.db"
    conn = connect(str(db_path))
    try:
        assert get_journal_mode(conn).lower() == "wal"
    finally:
        conn.close()
