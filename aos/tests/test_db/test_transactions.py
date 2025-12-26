
import pytest

from aos.db.engine import connect, transaction


@pytest.fixture
def db_conn(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    conn.execute("CREATE TABLE t1 (val TEXT);")
    yield conn
    conn.close()

def test_transaction_commit(db_conn):
    with transaction(db_conn):
        db_conn.execute("INSERT INTO t1 VALUES ('a');")

    res = db_conn.execute("SELECT val FROM t1").fetchone()
    assert res[0] == 'a'

def test_transaction_rollback(db_conn):
    try:
        with transaction(db_conn):
            db_conn.execute("INSERT INTO t1 VALUES ('b');")
            raise RuntimeError("Boom")
    except RuntimeError:
        pass

    res = db_conn.execute("SELECT val FROM t1").fetchone()
    assert res is None # Should have rolled back 'b'
