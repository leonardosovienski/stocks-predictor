"""Exercise the real Core migration chain in isolated databases, never original banks."""
from contextlib import closing

import db


def test_all_migrations_preserve_raw_rows_and_reopen_idempotently(tmp_path):
    path = tmp_path / 'legacy.sqlite'
    with closing(db.get_connection(path)) as conn:
        assert len(db.MIGRATIONS) == 15
        conn.execute("INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,volume_fin,qty,source_file) VALUES ('2024-01-02','TEST3','02','010',10,11,9,10,1000,100,'historical-fixture')")
        conn.commit()
        schemas = conn.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name').fetchall()
        row = conn.execute('SELECT * FROM prices_raw').fetchall()
    with closing(db.get_connection(path)) as reopened:
        assert reopened.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name').fetchall() == schemas
        assert reopened.execute('SELECT * FROM prices_raw').fetchall() == row
        assert reopened.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    with closing(db.get_readonly_connection(path)) as reader:
        assert reader.execute('SELECT * FROM prices_raw').fetchall() == row
