"""Focused stdlib checks; no producer runtime or scientific fixtures."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("exporter", Path(__file__).with_name("export_cain_status.py"))
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

class ExportChecks(unittest.TestCase):
    def test_admission_layout_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "source"
            source = root / "STOCKS_CURRENT_STATE.md"
            source.parent.mkdir(parents=True)
            raw = "| Retorno líquido pessoal e operação real | Não aptos |\n".encode("utf-8")
            source.write_bytes(raw)
            expected = hashlib.sha256(raw).hexdigest()
            def git(args, **kwargs):
                return "a" * 40 if "rev-parse" in args else b""
            with patch.object(exporter.subprocess, "check_output", side_effect=git):
                result = exporter.export(root, expected, base / "publication.json")
                self.assertEqual(result["records"], 1)
                with self.assertRaises(FileExistsError):
                    exporter.export(root, expected, base / "publication.json")
                with self.assertRaises(ValueError):
                    exporter.export(root, "0" * 64, base / "wrong.json")
                with self.assertRaises(ValueError):
                    exporter.export(root, expected, root / "not-permitted.json")
                source.write_bytes(raw + raw)
                with self.assertRaises(ValueError):
                    exporter.export(root, hashlib.sha256(raw + raw).hexdigest(), base / "duplicate.json")
                self.assertFalse((base / "duplicate.json").exists())

if __name__ == "__main__":
    unittest.main()
