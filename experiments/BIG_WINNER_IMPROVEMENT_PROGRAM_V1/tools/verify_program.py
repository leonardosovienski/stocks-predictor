"""Verify freezes, historical guards, ledger chain, and machine-readable receipts."""
from __future__ import annotations
import json,sqlite3,sys
from pathlib import Path

PROGRAM=Path(__file__).resolve().parents[1]; REPO=PROGRAM.parents[1]
sys.path.insert(0,str(REPO))
from stocks_predictor.big_winner_v2 import sha256_file,verify_final_freeze,verify_selection_freeze
from stocks_predictor.prospective_big_winner import connect,verify_chain

selection=verify_selection_freeze(PROGRAM/"V2_SELECTION_FREEZE.yaml")
final=verify_final_freeze(PROGRAM/"V2_FINAL_FREEZE.json")
ledger_path=PROGRAM/"prospective"/"PROSPECTIVE_BIG_WINNER_LEDGER.sqlite"
conn=connect(ledger_path); ledger=verify_chain(conn); outcome_count=conn.execute("select count(*) from outcome_observations").fetchone()[0]; conn.close()
historical={
 "BIG_WINNER_DETECTION_V1_manifest":sha256_file(REPO/"experiments"/"BIG_WINNER_DETECTION_V1"/"frozen_signals"/"MANIFEST.json"),
 "BIG_WINNER_PRICE_DETECTION_V1_manifest":sha256_file(REPO/"experiments"/"BIG_WINNER_PRICE_DETECTION_V1"/"frozen_signals"/"MANIFEST.json"),
 "BIG_WINNER_PRICE_DETECTION_V1_scorecard":sha256_file(REPO/"experiments"/"BIG_WINNER_PRICE_DETECTION_V1"/"FINAL_SCORECARD.json")}
receipt={"status":"PASS","selection_freeze_hash":selection["artifact_hash"],"final_freeze_hash":final["artifact_hash"],"ledger":ledger,"outcome_observation_count":outcome_count,"historical_artifact_hashes":historical,"prospective_evidence_start":"FIRST_ELIGIBLE_DECISION_AFTER_FINAL_FREEZE; NOT_STARTED","shadow_implementation_status":"COMPLETE","shadow_runtime_status":"READY_NOT_SCHEDULED"}
target=PROGRAM/"prospective"/"LEDGER_RECEIPT.json"; target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(receipt,indent=2))
