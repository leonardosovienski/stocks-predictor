"""Read-only helpers for primary-source reconstruction (no evaluation code)."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(r'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907')
BASE = ROOT / 'work/h19-cash-expanded-source'
OUT = ROOT / 'work/source-closure-20260908'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def norm(s):
    return ' '.join(unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().split())

MONTHS = {v: i + 1 for i, v in enumerate('janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro'.split())}
DATE = re.compile(r'\b(\d{1,2})\s*(?:de\s+(' + '|'.join(MONTHS) + r')\s*(?:de\s*)?|([/.-])(\d{1,2})\3)(\d{4})\b')

def dates(s):
    result = []
    for m in DATE.finditer(s):
        try:
            d = date(int(m[5]), MONTHS[m[2]] if m[2] else int(m[4]), int(m[1])).isoformat()
        except ValueError:
            continue
        result.append((d, m.start(), m.end()))
    return result

def amounts(s, amount):
    result = []
    for m in re.finditer(r'(?<!\d)(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2,}(?!\d)', s):
        value = Decimal(m[0].replace('.', '').replace(',', '.'))
        # Candidate matching to stated decimal precision only; never approval.
        quantum = Decimal(1).scaleb(value.as_tuple().exponent)
        if abs(value - Decimal(amount)) <= max(quantum, Decimal('0.00000000001')):
            result.append((str(value), m.start(), m.end()))
    return result

def pages(name):
    p = BASE / name
    if not p.exists():
        p = OUT / 'new-primary' / name
    for suffix in ('.extracted.json', '.complete-text.json', '.text.json'):
        q = p.with_suffix(suffix)
        if q.exists():
            return read(q)
    raise FileNotFoundError(name)
