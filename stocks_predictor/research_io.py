"""Durable I/O helpers of the stocks research circuit (stdlib only).

``atomic_write`` publishes bytes by write-to-temporary + fsync + ``os.replace`` so a crash
leaves either the previous file or the complete new one, never a torn file under the
final name. ``strict_json_loads`` refuses duplicate keys and NaN/Infinity.
"""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
from uuid import uuid4

from .research_faults import DISK_FAULT_POINT, FAULT_ENV


def atomic_write(path: str | Path, raw: bytes, *, fault_point: str | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fault_point is not None and os.environ.get(FAULT_ENV) == DISK_FAULT_POINT == fault_point:
        # Edge fault injection (qualification): the disk refuses the write before any byte
        # reaches the final name, exactly like a full volume.
        raise OSError(errno.ENOSPC, "No space left on device (injected)", str(path))
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def strict_json_loads(text: str | bytes):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate JSON key: {key!r}")
            out[key] = value
        return out

    def constant(name):
        raise ValueError(f"non-finite JSON constant: {name}")

    if isinstance(text, bytes):
        text = text.decode("utf-8")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


__all__ = ["atomic_write", "strict_json_loads"]
