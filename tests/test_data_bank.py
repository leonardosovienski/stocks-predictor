"""Recovery regression tests use synthetic archives, never research sources."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

from tools.data_bank import digest, inspect_database, restore


class DataBankTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "seed.db"
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("CREATE TABLE prices_raw(date TEXT, ticker TEXT)")
            conn.execute("INSERT INTO prices_raw VALUES ('2020-01-02','TEST3')")
            conn.commit()

    def archive(self, entries, declared_sha=None):
        rows, objects = [], {}
        for name, data in entries.items():
            sha = declared_sha or hashlib.sha256(data).hexdigest()
            rows.append({"path": name, "sha256": sha, "size": len(data)})
            objects[sha] = data
        manifest = {"format": "stocks-data-only-v1", "files": rows,
                    "file_count": len(rows), "restored_bytes": sum(r["size"] for r in rows)}
        path = self.root / "data.zip"
        with zipfile.ZipFile(path, "x") as archive:
            archive.writestr("MANIFESTO_DADOS.json", json.dumps(manifest))
            for sha, data in objects.items():
                archive.writestr("objects/" + sha, data)
        return path

    def test_deduplicates_aliases_and_keeps_bundle_independent(self):
        payload = self.db.read_bytes()
        archive = self.archive({"project/a.db": payload, "research/b.db": payload,
                                "evidence/notice.txt": b"original evidence"})
        before = digest(archive)
        dest = self.root / "recovered"
        result = restore(archive, before, dest, {"source": "evidence"})
        self.assertEqual(result["database_paths"], 2)
        self.assertEqual(result["database_unique_objects"], 1)
        self.assertEqual(result["databases"][0]["inspection"]["status"], "INTEGRITY_PASS")
        self.assertFalse(result["source_completeness_certified"])
        self.assertEqual(digest(archive), before)
        copied = dest / "bundles/source/notice.txt"
        copied.write_bytes(b"changed derived copy")
        source_sha = hashlib.sha256(b"original evidence").hexdigest()
        self.assertEqual((dest / "objects" / source_sha).read_bytes(), b"original evidence")
        self.assertEqual(Path(result["databases"][0]["local_path"]).read_bytes(), payload)

    def test_read_only_inspection_leaves_no_journals_and_closes_file(self):
        before = self.db.read_bytes()
        result = inspect_database(self.db)
        self.assertEqual(result["tables"]["prices_raw"]["date_ranges"]["date"]["max"], "2020-01-02")
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(list(self.root.glob("seed.db-*")), [])
        self.db.rename(self.root / "moved.db")  # also checks closed Windows handles

    def test_nonempty_wal_prevents_false_integrity_certificate(self):
        archive = self.archive({"project/a.db": self.db.read_bytes(),
                                "project/A.DB-WAL": b"pending transaction bytes"})
        result = restore(archive, digest(archive), self.root / "recovered")
        self.assertEqual(result["databases"][0]["inspection"]["status"],
                         "REQUIRES_JOURNAL_AWARE_NORMALIZATION")
        self.assertEqual(len(result["path_map"]), 2)

    def test_valid_hash_of_invalid_sqlite_never_emits_catalog(self):
        archive = self.archive({"project/a.db": b"not a sqlite database"})
        dest = self.root / "recovered"
        with self.assertRaises(sqlite3.DatabaseError):
            restore(archive, digest(archive), dest)
        self.assertFalse((dest / "catalog.json").exists())

    def test_bad_archive_digest_writes_nothing(self):
        archive = self.archive({"project/a.db": self.db.read_bytes()})
        dest = self.root / "recovered"
        with self.assertRaisesRegex(ValueError, "Archive checksum"):
            restore(archive, "0" * 64, dest)
        self.assertFalse(dest.exists())

    def test_bad_object_digest_never_emits_catalog(self):
        archive = self.archive({"project/a.db": self.db.read_bytes()}, "0" * 64)
        dest = self.root / "recovered"
        with self.assertRaisesRegex(ValueError, "Restored object hash"):
            restore(archive, digest(archive), dest)
        self.assertFalse((dest / "catalog.json").exists())

    def test_existing_destination_is_preserved(self):
        archive = self.archive({"project/a.db": self.db.read_bytes()})
        with self.assertRaises(FileExistsError):
            restore(archive, digest(archive), self.root)
        self.assertTrue(self.db.exists())

    def test_path_traversal_rejected_before_writing(self):
        archive = self.archive({"../escape.db": self.db.read_bytes()})
        dest = self.root / "recovered"
        with self.assertRaisesRegex(ValueError, "Unsafe path"):
            restore(archive, digest(archive), dest)
        self.assertFalse(dest.exists())

    def test_budget_rejected_before_writing(self):
        archive = self.archive({"project/a.db": self.db.read_bytes()})
        dest = self.root / "recovered"
        with self.assertRaisesRegex(ValueError, "budget"):
            restore(archive, digest(archive), dest, max_bytes=1)
        self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main()
