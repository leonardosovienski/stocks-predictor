"""Capture a declared list of public sources without modifying earlier captures."""
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location('r5_acquire', Path(__file__).resolve().parents[1] / 'profit_validation/acquire.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
plan = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if len(plan) > 60 or len({row[0] for row in plan}) != len(plan):
    raise ValueError('Duplicate paths or URL budget exceeded')
module.SOURCES = plan
module.main(sys.argv[2])
