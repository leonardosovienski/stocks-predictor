from pathlib import Path
from urllib.request import Request, urlopen
import re
from html import unescape
from concurrent.futures import ThreadPoolExecutor

BASE=Path(__file__).resolve().parent/'value-event-terms'
def fetch(ticker):
    url='https://www.fundamentus.com.br/fatos_relevantes.php?papel='+ticker
    raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read()
    (BASE/(ticker+'-document-index.html')).write_bytes(raw)
    text=raw.decode('latin1')
    for row in re.findall(r'<tr\b.*?</tr>',text,flags=re.S|re.I):
        if any(day in row for day in ('05/11/2021','01/07/2022','27/06/2022','31/07/2024','22/07/2024','30/05/2025')):
            print(ticker,unescape(re.sub('<[^>]+>',' ',row)),re.findall('href=[\"\']([^\"\']+)',row),flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(fetch,['LCAM3','IGTI11','SOMA3','CRFB3']))
