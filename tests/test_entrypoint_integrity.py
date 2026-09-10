"""Invalid input must fail before opening writers; migration failures close them."""
from unittest.mock import Mock
import zipfile

import pytest

import db
import ingest_cotahist
import main


@pytest.mark.parametrize('day', ['20240201', '2024-02-30', '2024-1-2', '2020-01-01'])
def test_paper_rejects_backdate_before_opening_database(monkeypatch, day):
    writer = Mock(side_effect=AssertionError('writer opened'))
    monkeypatch.setattr(main, '_conn', writer)
    with pytest.raises(ValueError):
        main.cmd_paper([day])
    writer.assert_not_called()


@pytest.mark.parametrize('day', ['20240201', '2024-02-30', '2024-1-2'])
def test_universe_rejects_bad_date_before_opening_database(monkeypatch, day):
    writer = Mock(side_effect=AssertionError('writer opened'))
    monkeypatch.setattr(main, '_conn', writer)
    with pytest.raises(ValueError):
        main.cmd_universe([day])
    writer.assert_not_called()


def test_bad_archive_does_not_open_or_create_database(tmp_path, monkeypatch):
    writer = Mock(side_effect=AssertionError('writer opened'))
    monkeypatch.setattr(db, 'get_connection', writer)
    with pytest.raises(FileNotFoundError):
        ingest_cotahist.parse_cotahist(str(tmp_path/'missing.zip'))
    ambiguous = tmp_path/'ambiguous.zip'
    with zipfile.ZipFile(ambiguous, 'w') as archive:
        archive.writestr('A.TXT', 'unused')
        archive.writestr('B.TXT', 'unused')
    with pytest.raises(ValueError, match='ambíguo'):
        ingest_cotahist.parse_cotahist(str(ambiguous))
    writer.assert_not_called()


def test_migration_failure_closes_connection(tmp_path, monkeypatch):
    conn = Mock()
    monkeypatch.setattr(db.infra, 'connect', lambda *a, **k: conn)
    monkeypatch.setattr(db.infra, 'run_migrations', Mock(side_effect=RuntimeError('migration failed')))
    with pytest.raises(RuntimeError, match='migration failed'):
        db.get_connection(tmp_path/'isolated.db')
    conn.close.assert_called_once_with()
