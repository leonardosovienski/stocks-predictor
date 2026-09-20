"""Run one no-capital BIG_WINNER shadow decision."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from stocks_predictor.big_winner_shadow import run_shadow
PROGRAM=ROOT/"experiments"/"BIG_WINNER_IMPROVEMENT_PROGRAM_V1"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--database",type=Path,required=True)
    parser.add_argument("--ledger",type=Path,required=True)
    parser.add_argument("--artifacts",type=Path,required=True)
    parser.add_argument("--asof",required=True)
    parser.add_argument("--execution-time",required=True)
    parser.add_argument("--code-commit",required=True)
    parser.add_argument("--decision-timestamp")
    parser.add_argument("--prospective",action="store_true",help="Only use for genuinely post-freeze market observations")
    args=parser.parse_args()
    result=run_shadow(database_path=args.database,ledger_path=args.ledger,
        artifact_directory=args.artifacts,selection_freeze_path=PROGRAM/"V2_SELECTION_FREEZE.yaml",
        final_freeze_path=PROGRAM/"V2_FINAL_FREEZE.json",asof=args.asof,
        execution_time=args.execution_time,code_commit=args.code_commit,
        decision_timestamp=args.decision_timestamp,development_backfill=not args.prospective)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
