"""Read-only commands must not create evidence or migrate an old schema."""
from contextlib import closing
import hashlib
import sqlite3

import pytest

import db
import main


def legacy_db(path):
    with closing(sqlite3.connect(path)) as conn:
        conn.execute('CREATE TABLE prices_raw (ticker TEXT)')
        conn.execute("INSERT INTO prices_raw VALUES ('EXAMPLE3')")
        conn.commit()


def test_status_on_missing_database_does_not_create_it(tmp_path, monkeypatch):
    path = tmp_path / 'absent' / 'stocks.db'
    monkeypatch.setenv(db.DB_PATH_ENV, str(path))
    assert main.status() == 0
    assert not path.parent.exists()


def test_status_does_not_migrate_a_legacy_schema(tmp_path, monkeypatch):
    path = tmp_path / 'stocks.db'; legacy_db(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setenv(db.DB_PATH_ENV, str(path))
    monkeypatch.setattr(db, 'get_connection', lambda *a, **k: pytest.fail('writer used by status'))
    assert main.status() == 0
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [('prices_raw',)]


def test_read_connection_enforces_no_writes_and_requires_existing_source(tmp_path):
    path = tmp_path / 'stocks.db'
    with pytest.raises(FileNotFoundError):
        db.get_readonly_connection(path)
    assert not path.exists()
    legacy_db(path)
    with closing(db.get_readonly_connection(path)) as conn:
        assert conn.execute('SELECT COUNT(*) FROM prices_raw').fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError, match='readonly'):
            conn.execute('DELETE FROM prices_raw')


@pytest.mark.parametrize('command', ['analyst', 'splits-review'])
def test_consultative_cli_paths_use_readonly_connection(tmp_path, monkeypatch, command):
    path = tmp_path / 'stocks.db'; legacy_db(path)
    monkeypatch.setenv(db.DB_PATH_ENV, str(path))
    monkeypatch.setattr(db, 'get_connection', lambda *a, **k: pytest.fail('writer used by read-only command'))

    def consult(conn, *args, **kwargs):
        assert conn.execute('PRAGMA query_only').fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError, match='readonly'):
            conn.execute('DELETE FROM prices_raw')
        return 0

    if command == 'analyst':
        import analyst
        monkeypatch.setattr(analyst, 'write_brief', consult)
        assert main.cmd_analyst([]) == 0
    else:
        import adjust
        monkeypatch.setattr(adjust, 'export_candidates_csv', consult)
        assert main.cmd_splits_review([str(tmp_path / 'review.csv')]) == 0
