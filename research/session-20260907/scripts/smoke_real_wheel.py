from pathlib import Path
import json
import stocks_predictor
from stocks_predictor import db, simulation, stock_events, document_panel
root=Path(__file__).resolve().parent.parent
assert 'real-integration-installed' in str(stocks_predictor.__file__)
assert simulation.ENGINE_VERSION == 'stocks-causal-execution-v3'
c=db.get_connection(root/'work/wheel-real-smoke.db')
f=root/'work/stocks-predictor/tests/fixtures/real_integration'
assert stock_events.import_bonus_events(c,(f/'bonus-events.json').read_bytes())==3
assert stock_events.bonus_events(c,'ENGI11','2025-12-31')==[('2025-11-28','2025-12-02',0.1)]
assert document_panel.capital_from_viewer((f/'capital-134335.html').read_bytes(),{'ref_date':'2023-12-31'},'CVM')['total']==15753833000
c.close()
print('installed wheel outside checkout: PASS')
print('capital scale and bonus migration/import: PASS')
print('module: '+str(stocks_predictor.__file__))
