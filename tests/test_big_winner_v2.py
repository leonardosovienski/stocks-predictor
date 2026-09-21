from __future__ import annotations
import datetime as dt
import hashlib, sqlite3, tempfile, unittest
from pathlib import Path

from stocks_predictor import big_winner_v2 as model
from stocks_predictor import prospective_big_winner as ledger

REPO=Path(__file__).resolve().parents[1]
PROGRAM=REPO/"experiments"/"BIG_WINNER_IMPROVEMENT_PROGRAM_V1"

def decision(asof="2026-09-30"):
    dates=[(dt.date(2025,1,1)+dt.timedelta(days=i)).isoformat() for i in range(253)]
    return model.generate_decision(asof,"2026-10-01",
        {"AAAA3":(dates,list(range(1,254))), "BBBB3":(dates,list(range(253,0,-1)))},
        {},{"code_commit":"abc","config_hash":"cfg","dataset_hash":"data","source_versions":["v"]})

class BigWinnerV2Tests(unittest.TestCase):
    def test_selection_freeze_hash_and_identity(self):
        data=model.verify_selection_freeze(PROGRAM/"V2_SELECTION_FREEZE.yaml")
        self.assertEqual(data["v2_identifier"],model.MODEL_ID)

    def test_final_freeze_hash_and_identity(self):
        data=model.verify_final_freeze(PROGRAM/"V2_FINAL_FREEZE.json")
        self.assertEqual(data["final_v2_identifier"],model.MODEL_ID)

    def test_pit_boundary_ignores_asof_and_future(self):
        dates=[(dt.date(2020,1,1)+dt.timedelta(days=i)).isoformat() for i in range(260)]
        closes=[float(i+1) for i in range(260)]
        base=model.momentum_12_1(dates,closes,"9999-01-01")
        closes[-22]=1_000_000
        self.assertNotEqual(base,model.momentum_12_1(dates,closes,"9999-01-01"))
        # A value exactly at asof is excluded.
        self.assertEqual(model.momentum_12_1(dates+["9999-01-01"],closes+[99_000],"9999-01-01"),model.momentum_12_1(dates,closes,"9999-01-01"))

    def test_deterministic_ranking_and_tie_break(self):
        first=model.rank({"BBBB3":1.0,"AAAA3":1.0,"CCCC3":0.0})
        second=model.rank({"CCCC3":0.0,"AAAA3":1.0,"BBBB3":1.0})
        self.assertEqual(first,second); self.assertEqual(first[0]["ticker"],"AAAA3")

    def test_selection_fraction_ceil_twenty_percent(self):
        ranked=model.rank({f"T{i}":float(i) for i in range(6)})
        self.assertEqual(sum(r["selected"] for r in ranked),2)

    def test_decision_is_deterministic(self):
        self.assertEqual(decision(),decision())

    def test_dataset_and_config_hashes_present(self):
        d=decision(); self.assertEqual(d["dataset_hash"],"data"); self.assertEqual(d["config_hash"],"cfg")

    def test_ticker_only_identity_is_explicit_missing_state(self):
        self.assertEqual(decision()["ranking"][0]["security_identity"]["identity_status"],"TICKER_ONLY_PIT_IDENTITY_NOT_AVAILABLE")

    def test_corporate_action_continuity_and_future_boundary(self):
        dates=["2020-01-01","2020-01-02","2020-01-03"]
        self.assertEqual(model.apply_share_count_continuity(dates,[100,50,50],[("2020-01-02",.5),("2020-01-03",2)],"2020-01-02"),[50,50,50])

    def test_append_only_update_and_delete_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite")
            receipt=ledger.append_decision(conn,decision(),decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=False,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            with self.assertRaises(sqlite3.IntegrityError):conn.execute("UPDATE ledger_events SET payload_hash='x'")
            with self.assertRaises(sqlite3.IntegrityError):conn.execute("DELETE FROM ledger_events")
            conn.rollback(); self.assertEqual(receipt["status"],"APPENDED"); conn.close()

    def test_idempotent_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite"); args=dict(decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=False,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            ledger.append_decision(conn,decision(),**args); again=ledger.append_decision(conn,decision(),**args)
            self.assertEqual(again["status"],"IDEMPOTENT_EXISTING"); self.assertEqual(conn.execute("select count(*) from ledger_events").fetchone()[0],1); conn.close()

    def test_duplicate_key_changed_payload_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite"); args=dict(decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=False,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            original=decision(); ledger.append_decision(conn,original,**args); changed=dict(original); changed["decision_reason"]="changed"
            with self.assertRaises(ValueError):ledger.append_decision(conn,changed,**args)
            conn.close()

    def test_backfill_excluded_from_prospective_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite")
            result=ledger.append_decision(conn,decision("2025-01-31"),decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=True,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            self.assertFalse(result["prospective_evidence_eligible"]); conn.close()

    def test_prospective_start_requires_post_freeze_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite")
            result=ledger.append_decision(conn,decision(),decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=False,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            self.assertTrue(result["prospective_evidence_eligible"]); conn.close()

    def test_correction_appends_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite")
            r=ledger.append_decision(conn,decision(),decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=False,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            ledger.append_correction(conn,r["logical_key"],{"reason":"administrative"},"2026-10-02T00:00:00+00:00")
            self.assertEqual(conn.execute("select count(*) from ledger_events").fetchone()[0],2); self.assertEqual(ledger.verify_chain(conn)["status"],"VALID"); conn.close()

    def test_intermediate_outcomes_do_not_mature_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=ledger.connect(Path(tmp)/"ledger.sqlite"); r=ledger.append_decision(conn,decision(),decision_timestamp="2026-10-01T00:00:00+00:00",development_backfill=False,final_freeze_timestamp="2026-09-19T00:00:00+00:00",final_freeze_commit="sha")
            metrics={"price_return":.1,"time_to_10":None,"time_to_20":None,"time_to_30":None,"maximum_adverse_excursion":-.05,"maximum_favorable_excursion":.12,"outcome_status":"INTERMEDIATE"}
            self.assertFalse(ledger.append_outcome_observation(conn,r["logical_key"],"2026-11-01T00:00:00+00:00",1,metrics)["primary_endpoint_mature"])
            self.assertTrue(ledger.append_outcome_observation(conn,r["logical_key"],"2027-10-01T00:00:00+00:00",12,{**metrics,"outcome_status":"FINAL"})["primary_endpoint_mature"]); conn.close()

    def test_artifact_is_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"decision.json"; ledger.write_artifact(path,decision(),{"status":"APPENDED"}); ledger.write_artifact(path,decision(),{"status":"APPENDED"})
            with self.assertRaises(FileExistsError):ledger.write_artifact(path,decision(),{"status":"different"})

    def test_idempotent_receipt_is_artifact_stable(self):
        appended={"status":"APPENDED","logical_key":"k","event_hash":"h","prospective_evidence_eligible":False}
        existing={**appended,"status":"IDEMPOTENT_EXISTING"}
        self.assertEqual(ledger.stable_decision_receipt(appended),ledger.stable_decision_receipt(existing))

    def test_historical_artifacts_preserved(self):
        expected={
          REPO/"experiments"/"BIG_WINNER_DETECTION_V1"/"frozen_signals"/"MANIFEST.json":"85eac17353d5833a27c7dac57232afaf16b4321dfcc97b4ed5c24593e23ba402",
          REPO/"experiments"/"BIG_WINNER_PRICE_DETECTION_V1"/"frozen_signals"/"MANIFEST.json":"805b27c739f7e6444551cb1541f8a92c13512444e99ed0659a1b73870e01d507",
          REPO/"experiments"/"BIG_WINNER_PRICE_DETECTION_V1"/"FINAL_SCORECARD.json":"dd3d75cd3f17dc3a50ed56ec1c60e198ee0b1a4d632c40dc2225f93475f68aec"}
        for path,digest in expected.items():
            canonical=path.read_bytes().replace(b"\r\n",b"\n")
            self.assertEqual(hashlib.sha256(canonical).hexdigest(),digest)

if __name__=="__main__":unittest.main()
