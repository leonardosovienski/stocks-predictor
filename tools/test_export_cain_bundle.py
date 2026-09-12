"""Producer exporter regressions using fictional committed source fixtures."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from research_bundle import digest, validate
from export_cain_bundle import export

SOURCE = "docs/engineering/2026-09-11-architecture/evidence/real-v020.json"
SAMPLE = '{"status":"UNKNOWN","scope":"fictional fixture","capital_enabled":false,"source_sha256":"0000000000000000000000000000000000000000000000000000000000000000","rows":1,"inspection":{"historical_publication_certified":false,"sources":[{"source_id":"TEST-DATASET-001","observed_at":"2026-09-11T00:00:00Z","source_url":"opaque:test","sha256":"0000000000000000000000000000000000000000000000000000000000000000"}]}}'


class ExportTests(unittest.TestCase):
    def setUp(self):
        area = Path("C:/STOCKS/work/bundle-export-tests")
        area.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=area)
        self.base = Path(self.temporary.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        self.source = self.root / SOURCE
        self.source.parent.mkdir(parents=True, exist_ok=True)
        self.source.write_bytes(SAMPLE.encode())
        self.commit()
        self.expected = {SOURCE: digest(self.source.read_bytes())}

    def commit(self):
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "fictional fixture",
            ],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def run_export(self, destination="out", expected=None):
        return export(
            self.root,
            self.expected if expected is None else expected,
            self.base / destination,
            "2026-09-11T00:00:00Z",
        )

    def test_deterministic_read_only_unknown(self):
        first = self.run_export()
        second = self.run_export("other")
        self.assertEqual(first, second)
        validate(first)
        self.assertEqual(self.expected[SOURCE], digest(self.source.read_bytes()))
        self.assertTrue(all(e["event_at"] is None for e in first["entities"]))
        self.assertEqual(subprocess.check_output(["git", "-C", str(self.root), "status", "--porcelain"]), b"")

    def test_unexpected_source(self):
        with self.assertRaises(ValueError):
            self.run_export(expected={"private.env": "0" * 64})

    def test_hash_mismatch(self):
        with self.assertRaises(ValueError):
            self.run_export(expected={SOURCE: "0" * 64})

    def test_missing(self):
        self.source.unlink()
        with self.assertRaises((ValueError, OSError)):
            self.run_export()

    def test_changed(self):
        self.source.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.run_export()

    def test_existing_output(self):
        self.run_export()
        with self.assertRaises(FileExistsError):
            self.run_export()

    def test_inside_checkout(self):
        with self.assertRaises(ValueError):
            export(self.root, self.expected, self.root / "out", "2026-09-11T00:00:00Z")

    def test_malformed_committed(self):
        self.source.write_bytes(b"malformed")
        self.commit()
        with self.assertRaises((ValueError, KeyError)):
            self.run_export(expected={SOURCE: digest(self.source.read_bytes())})

    def test_sensitive_content(self):
        self.source.write_bytes(b'{"api_key":"FAKE_SECRET_TEST_ONLY"}')
        self.commit()
        with self.assertRaisesRegex(ValueError, "SENSITIVE_CONTENT"):
            self.run_export(expected={SOURCE: digest(self.source.read_bytes())})


if __name__ == "__main__":
    unittest.main()
