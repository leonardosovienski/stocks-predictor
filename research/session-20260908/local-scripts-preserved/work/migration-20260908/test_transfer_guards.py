"""Adversarial transport checks using synthetic archives and temporary folders."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

PATH = Path(__file__).resolve().parents[2] / "outputs/EXPORTACAO_STOCKS_20260908/RESTAURAR.py"
SPEC = importlib.util.spec_from_file_location("restore", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TransferGuards(unittest.TestCase):
    def fixture(self, root, payload=b"known data", declared_sha=None, extra=False, missing=False):
        name = "project/data/example.txt"
        with zipfile.ZipFile(root / "stocks-001.zip", "w") as archive:
            if not missing:
                archive.writestr(name, payload)
            if extra:
                archive.writestr("project/undeclared.txt", b"extra")
        manifest = {"files": [{"path": name, "archive": "stocks-001.zip", "size": len(payload),
                               "mtime_ns": 0, "sha256": declared_sha or hashlib.sha256(payload).hexdigest()}],
                    "file_count": 1, "uncompressed_bytes": len(payload)}
        (root / "MANIFESTO.json").write_text(json.dumps(manifest), encoding="utf-8")
        controls = {p.name: {"bytes": p.stat().st_size, "sha256": MODULE.digest(p)}
                    for p in root.iterdir() if p.is_file()}
        (root / "CHECKSUMS.json").write_text(json.dumps(controls), encoding="utf-8")

    def test_valid_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            self.assertEqual(MODULE.restore(root)["payloads_verified"], 1)

    def test_path_traversal_and_windows_devices(self):
        with tempfile.TemporaryDirectory() as temp:
            for name in ("../escape", "/absolute", "C:/outside", "a\\..\\b", "x/CON", "x/NUL.txt", "x/a."):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    MODULE.safe_path(Path(temp), name)

    def test_payload_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, declared_sha="0" * 64)
            with self.assertRaisesRegex(ValueError, "Changed payload"):
                MODULE.restore(root)

    def test_missing_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, missing=True)
            with self.assertRaisesRegex(ValueError, "missing manifest"):
                MODULE.restore(root)

    def test_undeclared_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root, extra=True)
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                MODULE.restore(root)

    def test_corrupt_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            with (root / "stocks-001.zip").open("ab") as stream:
                stream.write(b"damage")
            with self.assertRaisesRegex(ValueError, "Missing or changed"):
                MODULE.restore(root)

    def test_destination_must_be_new(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            with self.assertRaises(FileExistsError):
                MODULE.restore(root, root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
