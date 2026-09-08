from pathlib import Path
import re
from html import unescape
base=Path(__file__).resolve().parent/'value-event-terms'
for ticker in ['CRFB3','IGTA3','IGTI11']:
    content=(base/(ticker+'-document-index.html')).read_text(encoding='latin1')
    print(ticker,len(content))
    for row in re.findall(r'<tr\b.*?</tr>',content,re.S):
        if ('25/04/2025' in row if ticker=='CRFB3' else ('2021' in row and ('11/' in row or '10/' in row))):
            print(unescape(re.sub('<[^>]+>',' ',row)),re.findall('href=[\"\']([^\"\']+)',row))
