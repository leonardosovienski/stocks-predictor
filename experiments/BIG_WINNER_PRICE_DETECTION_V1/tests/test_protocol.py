from __future__ import annotations
import json, math, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"lib"))
import common, evaluation_stage as ev, freeze, outcome_stage as out, signal_stage as sig

def rows(n=10,direction="HIGHER_IS_BETTER"):
    base=[{"ticker":f"T{i:02d}3","detector_id":"D","signal_asof":"2020-01-31",
        "detector_scorable":True,"universe_eligible":True,"score":float(i)} for i in range(n)]
    return common.rank_rows(base,direction)

class RequiredProtocolTests(unittest.TestCase):
    def test_01_signal_stage_cannot_read_outcomes(self):
        with self.assertRaises(PermissionError):sig.assert_outcome_firewall(["labels/outcomes.csv"])
        sig.assert_dependency_firewall(ROOT/"lib"/"signal_stage.py")
    def test_02_freeze_prevents_later_mutation(self):
        row={k:"" for k in common.SIGNAL_FIELDS}; row.update(rows(1)[0]); row.update(config_hash="c",code_commit="x",dataset_hash="d",input_hash="i",replay_fidelity="EXACT",historical_scientific_status="H",not_scorable_reason="",execution_time="2020-02-03")
        with tempfile.TemporaryDirectory() as d:
            path=freeze.freeze_rows([row],Path(d)/"f",{"code_commit":"x","config_hash":"c","dataset_hashes":{"d":"h"}}); freeze.verify_freeze(path)
            (path.parent/"signals.csv").write_text("tamper",encoding="utf-8")
            with self.assertRaises(ValueError):freeze.verify_freeze(path)
    def test_03_labels_require_valid_freeze(self):
        with self.assertRaises(FileNotFoundError):out.load_frozen("missing/MANIFEST.json")
    def test_04_next_open_execution(self):self.assertEqual(common.next_session("2020-01-31",["2020-01-31","2020-02-03"]),"2020-02-03")
    def test_05_historical_universe(self):
        sessions=[f"2020-01-{i:02d}" for i in range(1,29)]
        series={"AAAA3":{"dates":sessions,"volumes":[1]*28,"closes":[1]*28}}
        self.assertEqual(sig.historical_universe("2020-01-28",sessions,series,{},lookback=5,min_history=5),["AAAA3"])
        self.assertEqual(sig.historical_universe("2020-01-28",sessions,series,{"AAAA3":[("2020-01-10",None)]},lookback=5,min_history=5),[])
    def test_06_detector_scorability(self):self.assertIsNone(sig._score("MOMENTUM_12_1",[1]*10,[1]*10))
    def test_07_missing_never_zero(self):self.assertIsNone(sig._score("VOLUME_SURGE",[1]*300,[1]*10))
    def test_08_top20_deterministic(self):self.assertEqual(sum(r["selected"] for r in rows()),2)
    def test_09_tie_break_deterministic(self):
        base=[{"ticker":t,"detector_id":"D","signal_asof":"x","detector_scorable":True,"score":1} for t in ["B","A","C","D","E"]]
        self.assertEqual([r["ticker"] for r in common.rank_rows(base,"HIGHER_IS_BETTER") if r["selected"]],["A"])
    def test_10_direction_frozen(self):self.assertEqual(common.DETECTORS["LOW_VOL_252"][0],"LOWER_IS_BETTER")
    def test_11_price_index_excludes_cash(self):self.assertEqual(out.price_index(["a","b"],[100,90]),[100,90])
    def test_12_split_continuity(self):self.assertEqual(out.price_index(["a","b"],[100,50],[("b",.5)]),[50,50])
    def test_13_reverse_split_continuity(self):self.assertEqual(out.price_index(["a","b"],[10,100],[("b",10)]),[100,100])
    def test_14_stock_bonus_continuity(self):self.assertEqual(out.price_index(["a","b"],[110,100],bonuses=[("b",100/110)]),[100,100])
    def test_15_ticker_substitution_continuity(self):
        d,v=out.substitute_continuity(["a"],[10],["b"],[5],.5); self.assertEqual((d,v),(["a","b"],[5,5]))
    def test_16_terminal_corporate_events(self):self.assertFalse(out.calculate_outcome("2020-01-02",["2020-01-02","2021-01-01"],[1,2],["2020-01-02","2021-01-01"],terminal_event="UNRESOLVED")["outcome_estimable"])
    def test_17_terminal_quote_staleness_five(self):
        s=[f"2020-01-{i:02d}" for i in range(1,11)]; self.assertEqual(out.terminal_session_status(s,"2020-01-05","2020-01-10"),"OK"); self.assertEqual(out.terminal_session_status(s,"2020-01-04","2020-01-10"),"TERMINAL_QUOTE_STALE")
    def test_18_ranking_invariance_momentum(self):self.assertTrue(sig.scale_invariant(lambda x:x[-22]/x[-253]-1,list(range(1,254))))
    def test_19_ranking_invariance_vol(self):self.assertTrue(sig.scale_invariant(lambda x:sig._score("LOW_VOL_252",x,[1]*300),list(range(1,254))))
    def test_20_ranking_invariance_high(self):self.assertTrue(sig.scale_invariant(lambda x:sig._score("52W_HIGH",x,[1]*300),list(range(1,254))))
    def test_21_outcome_horizon(self):
        dates=["2020-01-02","2021-01-01","2021-01-04"]; r=out.calculate_outcome("2020-01-02",dates,[100,130,140],dates); self.assertTrue(r["BIG_WINNER_PRICE_12M"]); self.assertEqual(r["horizon_end"],"2021-01-01")
    def test_22_episode_construction(self):
        r=[{"ticker":"A","signal_asof":f"2020-0{i}-01","BIG_WINNER_PRICE_12M":v} for i,v in enumerate([True,False,True],1)]; self.assertEqual(len(out.create_episodes(r)),2)
    def test_23_unknown_does_not_close_episode(self):
        r=[{"ticker":"A","signal_asof":f"2020-0{i}-01","BIG_WINNER_PRICE_12M":v} for i,v in enumerate([True,None,True],1)]; self.assertEqual(len(out.create_episodes(r)),1); self.assertTrue(out.create_episodes(r)[0]["boundary_uncertain"])
    def test_24_episode_detection(self):
        e={"ticker":"A","episode_start":"a","episode_end":"c"}; s=[{"ticker":"A","signal_asof":"b","detector_scorable":True,"selected":True}]; self.assertEqual(out.classify_episode(e,s,100,200,120)["classification"],"EARLY_HIT")
    def test_25_early_hit_formula(self):
        e={"ticker":"A","episode_start":"a","episode_end":"c"}; s=[{"ticker":"A","signal_asof":"b","detector_scorable":True,"selected":True}]; self.assertAlmostEqual(out.classify_episode(e,s,100,200,140)["fraction_of_move_remaining"],.6)
    def test_26_matched_random_correct_universe(self):
        r=[]
        for month in ["a","b"]:
            for i in range(5):r.append({"signal_asof":month,"selected":i==0,"BIG_WINNER_PRICE_12M":i==0})
        self.assertEqual(len(ev.matched_random(r,25,1)),25)
    def test_27_complete_case_same_observability(self):
        r=[{"signal_asof":"a","selected":True,"BIG_WINNER_PRICE_12M":None},{"signal_asof":"a","selected":False,"BIG_WINNER_PRICE_12M":False}]
        self.assertTrue(math.isnan(ev.matched_random(r,1,1)[0]))
    def test_28_partial_id_formulas(self):
        r=[{"selected":True,"BIG_WINNER_PRICE_12M":True},{"selected":True,"BIG_WINNER_PRICE_12M":None},{"selected":False,"BIG_WINNER_PRICE_12M":False}]
        p=common.partial_id(r[:2],r); self.assertEqual((p["precision_lower"],p["precision_upper"]),(.5,1)); self.assertEqual(p["base_rate_upper"],2/3)
    def test_29_block_bootstrap_cross_sections(self):self.assertEqual(ev.moving_block([(1,2,1,4)]*5,lambda x:len(x),2,10,1),[5]*10)
    def test_30_positive_leakage_control(self):
        r=[{"selected":False,"BIG_WINNER_PRICE_12M":v} for v in [True,False,False]]; self.assertTrue(ev.positive_leakage_control(r))
    def test_31_negative_score_permutation(self):
        r=[{"signal_asof":"a","selected":i<2,"BIG_WINNER_PRICE_12M":i==0} for i in range(5)]; self.assertIsInstance(ev.negative_permutation(r),float)
    def test_32_empirical_p_formula(self):self.assertEqual(ev.empirical_p(.5,[.4,.5,.6]),.75)
    def test_33_holm_monotone(self):
        p=ev.holm({"a":.01,"b":.02,"c":.5}); self.assertLessEqual(p["a"],p["b"]); self.assertLessEqual(p["b"],p["c"])

if __name__=="__main__":unittest.main()
