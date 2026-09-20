"""Finalize code hashes and canonical artifact hash for V2_FINAL_FREEZE."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

PROGRAM=Path(__file__).resolve().parents[1]; REPO=PROGRAM.parents[1]; PATH=PROGRAM/"V2_FINAL_FREEZE.json"
def file_hash(path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()
data=json.loads(PATH.read_text(encoding="utf-8"))
for relative in list(data["code_hashes"]):data["code_hashes"][relative]=file_hash(REPO/relative)
payload=dict(data);payload.pop("artifact_hash",None);data["artifact_hash"]=canonical(payload)
PATH.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(data["artifact_hash"])
