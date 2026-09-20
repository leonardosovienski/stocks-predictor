"""Finalize the pre-implementation selection freeze using canonical hashes."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "V2_SELECTION_FREEZE.yaml"

def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

data = json.loads(PATH.read_text(encoding="utf-8"))
config_fields = {key: data[key] for key in ("v2_identifier", "feature_definitions", "score_definitions",
    "feature_directions", "combination_rule", "weights", "threshold", "ranking_rule",
    "universe_contract", "target_contract", "pit_contract", "execution_contract")}
data["config_hash"] = digest(config_fields)
payload = dict(data); payload.pop("artifact_hash", None)
data["artifact_hash"] = digest(payload)
PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(data["config_hash"], data["artifact_hash"])
