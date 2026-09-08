"""Migration tests use synthetic data and never open research databases."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import pytest

SPEC = importlib.util.spec_from_file_location("data_transfer", Path(__file__).resolve().parents[1] / "tools/data_transfer.py")
transfer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transfer)


def zip_bytes(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    return out.getvalue()


def fixture(tmp_path, files):
    snapshot = tmp_path / "snapshot"
    rows = []
    for name, payload in files.items():
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        rows.append({"path": name, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    manifest = tmp_path / "original.json"
    manifest.write_text(json.dumps({"files": rows}), encoding="utf-8")
    archive = tmp_path / "data.zip"
    return snapshot, manifest, archive


def test_round_trip_preserves_data_and_strips_code_in_nested_deliveries(tmp_path):
    raw = zip_bytes({"facts.csv": b"a,b\n1,2\n"})
    inner = zip_bytes({"run.py": b"do not run", "unique.txt": b"only inside nested archive"})
    mixed = zip_bytes({"nested.zip": inner, "data/raw.zip": raw, "go.ps1": b"do not run"})
    args = fixture(tmp_path, {"project/data/raw.zip": raw, "session/mixed.zip": mixed,
                             "project/mixed-copy.zip": mixed, "project/data/a.txt": b"same",
                             "session/b.txt": b"same", "project/main.py": b"print('code')",
                             "python313-packages/library/__init__.py": b"library"})
    result = transfer.build(*args)
    dest = tmp_path / "restored"
    receipt = transfer.verify(args[2], dest)
    assert receipt["project_code_in_zip"] is False
    assert result["unique_objects"] == 3
    assert (dest / "project/data/raw.zip").read_bytes() == raw
    assert (dest / "unpacked-archives/session/mixed.zip.contents/nested.zip.contents/unique.txt").read_bytes() == b"only inside nested archive"
    assert (dest / "unpacked-archives/project/mixed-copy.zip.contents/data/raw.zip").read_bytes() == raw
    assert not list(dest.rglob("*.py")) and not list(dest.rglob("*.ps1"))
    (dest / "project/data/a.txt").write_bytes(b"changed")
    assert (dest / "session/b.txt").read_bytes() == b"same"  # independent copies, not hardlinks


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/outside", "a\\..\\b", "a/NUL.txt", "a/CON", "a/x.", "a//b"])
def test_rejects_unsafe_paths(name):
    with pytest.raises(ValueError, match="Unsafe path"):
        transfer.validate_name(name)


def test_refuses_existing_destination_and_archive(tmp_path):
    args = fixture(tmp_path, {"project/data/test.txt": b"good"})
    transfer.build(*args)
    with pytest.raises(FileExistsError):
        transfer.build(*args)
    with pytest.raises(FileExistsError):
        transfer.verify(args[2], tmp_path)


def test_rejects_changed_source_and_corrupt_transport(tmp_path):
    args = fixture(tmp_path, {"project/data/test.txt": b"good"})
    (args[0] / "project/data/test.txt").write_bytes(b"evil")
    with pytest.raises(ValueError, match="Source changed"):
        transfer.build(*args)
    args[2].write_bytes(b"invalid")
    args[2].with_suffix(".json").write_text(json.dumps({"bytes": 7, "sha256": "0" * 64}), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        transfer.verify(args[2])


def test_rejects_undeclared_and_missing_payloads(tmp_path):
    args = fixture(tmp_path, {"project/data/test.txt": b"good"})
    transfer.build(*args)
    with zipfile.ZipFile(args[2], "a") as archive:
        archive.writestr("unexpected.py", b"code")
    transfer.write_json(args[2].with_suffix(".json"), {"bytes": args[2].stat().st_size, "sha256": transfer.digest(args[2])})
    with pytest.raises(ValueError, match="Undeclared"):
        transfer.verify(args[2])


def test_prefix_restore_and_conflicting_windows_case(tmp_path):
    args = fixture(tmp_path, {"project/data/a.txt": b"one", "session/b.txt": b"two"})
    transfer.build(*args)
    dest = tmp_path / "filtered"
    assert transfer.verify(args[2], dest, "project/data")["restored_files"] == 1
    assert not (dest / "session").exists()
    with pytest.raises(ValueError, match="No files match"):
        transfer.verify(args[2], tmp_path / "empty", "unknown")
    conflict = tmp_path / "conflict"
    conflict.mkdir()
    args2 = fixture(conflict, {"project/A.txt": b"a", "project/a.txt": b"a"})
    with pytest.raises(ValueError, match="Duplicate destination"):
        transfer.build(*args2)
