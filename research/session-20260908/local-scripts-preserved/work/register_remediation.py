"""Register bounded repair scope before integration diagnostics."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

root = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
repo = root / "work/stocks-predictor"
spec = {
    "protocol_id": "H20_REVIEW_REMEDIATION_1",
    "registered_at_utc": datetime.now(timezone.utc).isoformat(),
    "base_commit": "c1bfa15",
    "scope": "Resolve code, integrity, reporting and workflow findings from the chat review; do not tune or promote a strategy.",
    "frozen_rules": "Reuse the three H20 arms, common valid universe, top20%, retain30%, weight tolerance2.5%, signal-date integer sizing and assumed one-side costs0.18%/0.36%; no new factor, date selection or parameter fit.",
    "implementation": "Add an optional pure signal policy to the existing continuous cash engine, leaving its default H19 path unchanged. Select using actual positions. Freeze selected integer quantities/weight tolerance at signal; process reviewed corporate/cash events, month transitions, sales, tax reserves, buys, settlement and liquidation with the existing chronological book.",
    "source_gate": "Verify all manifests/payloads and exact H20 snapshot identity before historical readiness. Require a separately reviewed H20 continuous coverage attestation bound to signal and source hashes and the conservative union of eligible intervals plus known successor requirements. The old H19 gate or a caller-supplied boolean is not H20 source certification.",
    "historical_work_this_repair": "Read-only coverage/integrity diagnostics only. No new historical profit evaluation while full source coverage is absent. Preserve old observations and packaged code; route new reproductions through full verification.",
    "validation": "Synthetic complete multi-period books with hand-computable cash/tax outcomes, actual vs intended incumbents, integer/fractional funding, blocked/unpaid claims, weight bands, mandatory exits, corporate deliveries and failures; unchanged H19 regression and old H20 marks; full tests and wheel outside checkout.",
    "reporting": "Track every review finding separately as resolved or source-dependent. Synthetic profit and historical mark change must never appear as historical/future net profit. No presumption that fewer name changes save proportional costs.",
    "stopping_rule": "Resolve authorized code and documentation defects, measure the source gap, and stop parameter expansion. Do not approve absent data, overwrite protected datasets or equate a small accounting demonstration with evidence of alpha.",
    "budget": {"configurations_administrative": 53, "historical_evaluations_administrative": 55, "new_return_configurations": 0, "new_historical_return_evaluations": 0, "no_intact_holdout": True},
    "new_dependencies": [], "real_orders": False, "spending": False,
}
path = repo / "docs/research/2026-09-08-h20-remediation-protocol.json"
with path.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(spec, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(hashlib.sha256(path.read_bytes()).hexdigest())
