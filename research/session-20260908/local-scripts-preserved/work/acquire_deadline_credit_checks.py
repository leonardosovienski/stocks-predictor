"""A contractual deadline is only a candidate for a B3 credit-date check."""
from concurrent.futures import ThreadPoolExecutor
import json
from probe_credit_sections import get
from source_utils import OUT

jobs = [(d,s) for d,s in [('2020-12-03','05'),('2021-05-31','05'),
    ('2023-05-31','05'),('2024-05-31','04-1'),('2023-05-05','05'),
    ('2024-05-15','04-1'),('2025-04-10','04-1'),('2025-12-30','04-1'),
    ('2021-10-22','05'),('2023-11-20','05')]]
with ThreadPoolExecutor(max_workers=4) as pool:
    records = list(pool.map(get,jobs))
with (OUT/'deadline-credit-acquisition-12.json').open('x',encoding='utf-8') as f:
    json.dump(records,f,indent=2)
for r in records: print(r)
