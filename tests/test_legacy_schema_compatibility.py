"""Exercise the real Core migration chain in isolated databases, never original banks."""
from contextlib import closing

import db


def test_all_migrations_preserve_raw_rows_and_reopen_idempotently(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    with closing(db.infra.connect(path)) as conn:
        db.infra.run_migrations(conn, db.MIGRATIONS[:1])
        conn.execute("INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,volume_fin,qty,source_file) VALUES ('2024-01-02','TEST3','02','010',10,11,9,10,1000,100,'historical-fixture')")
        conn.commit()
        row = [tuple(value) for value in conn.execute('SELECT * FROM prices_raw')]
    with closing(db.get_connection(path)) as conn:
        assert len(db.MIGRATIONS) == 15
        assert [tuple(value) for value in conn.execute('SELECT * FROM prices_raw')] == row
        schemas = conn.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name').fetchall()
    with closing(db.get_connection(path)) as reopened:
        assert reopened.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name').fetchall() == schemas
        assert [tuple(value) for value in reopened.execute('SELECT * FROM prices_raw')] == row
        assert [tuple(value) for value in reopened.execute('PRAGMA integrity_check')] == [('ok',)]
    with closing(db.get_readonly_connection(path)) as reader:
        assert [tuple(value) for value in reader.execute('SELECT * FROM prices_raw')] == row
