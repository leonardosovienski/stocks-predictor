"""Bounded read-only export selection using the existing domain implementation.

Never runs simulate_selected or writes into a source database. Only metadata is
returned; selected price bytes stay in the producer and redistribution is UNKNOWN.
"""

from contextlib import closing
from pathlib import Path
import json
import sys
import tempfile

from research_bundle import digest, sha
from research_bundle.files import no_links, safe_mkdirs, safe_open, transfer

BACKUP = "work/architecture-20260911/real-v020/backup/snapshot.sqlite"
MAX_DATABASE = 64_000_000
MAX_ROWS = 500


def select_metadata(root, expected_sha, spec):
    sha(expected_sha)
    if set(spec) != {"source_ids", "observed_before", "start", "end"}:
        raise ValueError("Explicit DatasetSelection fields required")
    if type(spec["source_ids"]) is not list or not 1 <= len(spec["source_ids"]) <= 4:
        raise ValueError("At most four explicit source IDs")
    # Import only the producer-owned stdlib data adapter. No other domain/Core.
    code_root = Path(__file__).resolve().parents[1]
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from stocks_predictor.dataset_selection import DatasetSelection, materialize
    from stocks_predictor import operational_store

    selection = DatasetSelection(**{**spec, "source_ids": tuple(spec["source_ids"])})
    if selection.start != selection.end:
        raise ValueError("Export selection must be exactly one session")
    area = no_links(Path(root).absolute().parent)
    temporary = area / "work/bundle-selections"
    safe_mkdirs(temporary)
    for suffix in ("-wal", "-journal"):
        sidecar = area / (BACKUP + suffix)
        if sidecar.exists():
            no_links(sidecar)
            if sidecar.stat().st_size:
                raise ValueError("Backup must be a standalone closed snapshot")
    with tempfile.TemporaryDirectory(dir=temporary) as scratch:
        copy = Path(scratch) / "snapshot.sqlite"
        with safe_open(area, BACKUP) as source, copy.open("xb") as destination:
            transfer(source, destination, limit=MAX_DATABASE, expected_sha=expected_sha)
        # Bound before calling the existing selector (which returns in-memory bars).
        with closing(operational_store._open(copy)) as db:
            db.execute("PRAGMA query_only=ON")
            placeholders = ",".join("?" for _ in selection.source_ids)
            rows = db.execute(
                "SELECT count(*) FROM prices_raw WHERE source_file IN ("
                + placeholders
                + ") AND date>=? AND date<=?",
                (*selection.source_ids, selection.start, selection.end),
            ).fetchone()[0]
            if not 1 <= rows <= MAX_ROWS:
                raise ValueError("Selection row budget exceeded or empty")
        receipt = materialize(copy, selection)
        receipt.pop("bars")
    receipt.update(
        scope="Read-only export selection, not a historical experiment input claim",
        redistribution="UNKNOWN",
        historical_publication_certified=False,
        source_backup_sha256=expected_sha,
        source_backup=BACKUP,
        selector_code_sha256=digest((code_root / "stocks_predictor/dataset_selection.py").read_bytes()),
    )
    # Recheck immutable source before returning any receipt.
    with safe_open(area, BACKUP) as source:
        transfer(source, limit=MAX_DATABASE, expected_sha=expected_sha)
    return json.loads(json.dumps(receipt, allow_nan=False))
