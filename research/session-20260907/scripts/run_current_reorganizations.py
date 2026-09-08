from pathlib import Path
import json
import sys
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'stocks-predictor'))
from stocks_predictor.discovery_reorganizations import run
if '533 passed' not in (BASE/'reorganization-tests.log').read_text(encoding='utf-8'):
    raise RuntimeError('Full suite has not completed successfully')
result=run(BASE.parent/'outputs/h18-h19-repaired-observation.json',BASE/'value-measurement-source/quotes.db',
    BASE/'value-measurement-source/identity',BASE/'value-successor-source/successors.db',BASE/'value-successor-source/identity',
    BASE/'value-measurement-source/events.json',BASE/'value-measurement-source/reviewed-jumps.json',
    BASE/'value-event-terms/reorganizations.json',BASE/'stocks-predictor/docs/research/2026-09-07-reorganization-protocol.json',
    BASE.parent/'outputs/h18-h19-reorganization-observation.json')
for r in result:
    print(json.dumps({k:v for k,v in r.items() if k not in ('overall','fixed_halves')},ensure_ascii=False))
    for name,data in [('overall',r['overall']),*r['fixed_halves'].items()]:
        print(name,json.dumps({k:v for k,v in data.items() if k not in ('selection_frequency','missing_reasons')},ensure_ascii=False))
        print('missing_reasons',data['missing_reasons'])
