"""Append-only prospective evidence ledger and shadow decision artifacts."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
from pathlib import Path

from .big_winner_v2 import MODEL_ID, canonical_hash

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS ledger_events(
  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL CHECK(event_type IN ('DECISION','CORRECTION')),
  logical_key TEXT NOT NULL,
  decision_timestamp TEXT NOT NULL,
  model_identity TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  previous_event_hash TEXT,
  event_hash TEXT NOT NULL UNIQUE,
  development_backfill INTEGER NOT NULL CHECK(development_backfill IN (0,1)),
  prospective_evidence_eligible INTEGER NOT NULL CHECK(prospective_evidence_eligible IN (0,1)),
  correction_of TEXT,
  UNIQUE(event_type, logical_key, payload_hash)
);
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger_events
BEGIN SELECT RAISE(ABORT, 'append-only ledger: UPDATE forbidden'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger_events
BEGIN SELECT RAISE(ABORT, 'append-only ledger: DELETE forbidden'); END;
"""


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def _latest_hash(conn) -> str | None:
    row = conn.execute("SELECT event_hash FROM ledger_events ORDER BY sequence DESC LIMIT 1").fetchone()
    return row[0] if row else None


def append_decision(conn, decision: dict, *, decision_timestamp: str,
                    development_backfill: bool, final_freeze_timestamp: str,
                    final_freeze_commit: str) -> dict:
    if decision["model_identity"] != MODEL_ID:
        raise ValueError("model identity mismatch")
    dt.datetime.fromisoformat(decision_timestamp)
    observation_after_freeze = decision["signal_asof"] > final_freeze_timestamp[:10]
    eligible = bool(not development_backfill and observation_after_freeze and final_freeze_commit)
    logical_key = canonical_hash({"signal_asof":decision["signal_asof"],
        "model_identity":decision["model_identity"], "config_hash":decision["config_hash"],
        "dataset_hash":decision["dataset_hash"]})
    payload_json = json.dumps(decision, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
    existing = conn.execute("SELECT payload_hash,event_hash,prospective_evidence_eligible FROM ledger_events WHERE event_type='DECISION' AND logical_key=?", (logical_key,)).fetchone()
    if existing:
        if existing[0] != payload_hash:
            raise ValueError("duplicate logical decision with different payload")
        return {"status":"IDEMPOTENT_EXISTING", "logical_key":logical_key,
                "event_hash":existing[1], "prospective_evidence_eligible":bool(existing[2])}
    previous = _latest_hash(conn)
    event_hash = canonical_hash({"event_type":"DECISION","logical_key":logical_key,
        "decision_timestamp":decision_timestamp,"payload_hash":payload_hash,
        "previous_event_hash":previous,"development_backfill":development_backfill,
        "prospective_evidence_eligible":eligible})
    conn.execute("INSERT INTO ledger_events(event_type,logical_key,decision_timestamp,model_identity,payload_json,payload_hash,previous_event_hash,event_hash,development_backfill,prospective_evidence_eligible) VALUES('DECISION',?,?,?,?,?,?,?,?,?)",
        (logical_key,decision_timestamp,MODEL_ID,payload_json,payload_hash,previous,event_hash,int(development_backfill),int(eligible)))
    conn.commit()
    return {"status":"APPENDED","logical_key":logical_key,"event_hash":event_hash,
            "prospective_evidence_eligible":eligible}


def append_correction(conn, logical_key: str, correction: dict, decision_timestamp: str) -> dict:
    original = conn.execute("SELECT event_hash FROM ledger_events WHERE event_type='DECISION' AND logical_key=?", (logical_key,)).fetchone()
    if not original:
        raise ValueError("correction target not found")
    previous = _latest_hash(conn); payload_json=json.dumps(correction,sort_keys=True,separators=(",", ":"))
    payload_hash=hashlib.sha256(payload_json.encode()).hexdigest()
    event_hash=canonical_hash({"event_type":"CORRECTION","logical_key":logical_key,
        "decision_timestamp":decision_timestamp,"payload_hash":payload_hash,
        "previous_event_hash":previous,"correction_of":original[0]})
    conn.execute("INSERT INTO ledger_events(event_type,logical_key,decision_timestamp,model_identity,payload_json,payload_hash,previous_event_hash,event_hash,development_backfill,prospective_evidence_eligible,correction_of) VALUES('CORRECTION',?,?,?,?,?,?,?,?,?,?)",
        (logical_key,decision_timestamp,MODEL_ID,payload_json,payload_hash,previous,event_hash,0,0,original[0]))
    conn.commit(); return {"status":"CORRECTION_APPENDED","event_hash":event_hash}


def verify_chain(conn) -> dict:
    previous=None; count=eligible=backfills=0
    for row in conn.execute("SELECT event_type,logical_key,decision_timestamp,payload_hash,previous_event_hash,event_hash,development_backfill,prospective_evidence_eligible,correction_of FROM ledger_events ORDER BY sequence"):
        event_type,key,timestamp,payload_hash,recorded_previous,event_hash,backfill,is_eligible,correction_of=row
        if recorded_previous != previous: raise ValueError("ledger chain discontinuity")
        payload={"event_type":event_type,"logical_key":key,"decision_timestamp":timestamp,
            "payload_hash":payload_hash,"previous_event_hash":previous}
        if event_type=="DECISION": payload.update(development_backfill=bool(backfill),prospective_evidence_eligible=bool(is_eligible))
        else: payload["correction_of"]=correction_of
        if canonical_hash(payload)!=event_hash: raise ValueError("ledger event hash mismatch")
        previous=event_hash; count+=1; eligible+=is_eligible; backfills+=backfill
    return {"status":"VALID","events":count,"development_backfill_count":backfills,
            "prospective_eligible_decision_count":eligible,"head_hash":previous}


def write_artifact(path: str | Path, decision: dict, ledger_receipt: dict) -> Path:
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    artifact={"decision":decision,"ledger_receipt":ledger_receipt}
    artifact["artifact_hash"]=canonical_hash(artifact)
    if path.exists():
        existing=json.loads(path.read_text(encoding="utf-8"))
        if existing!=artifact: raise FileExistsError("immutable decision artifact already differs")
        return path
    path.write_text(json.dumps(artifact,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return path


def stable_decision_receipt(receipt: dict) -> dict:
    """Remove append-attempt status so idempotent retries reproduce the artifact."""
    return {key:receipt[key] for key in ("logical_key","event_hash","prospective_evidence_eligible")}
