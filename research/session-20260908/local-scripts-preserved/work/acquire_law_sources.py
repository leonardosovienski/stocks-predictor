from datetime import datetime, timezone
import hashlib
import json
import urllib.request
from source_utils import OUT

dest=OUT/'law';dest.mkdir(exist_ok=True)
jobs=[('rir-2018.pdf','https://www2.camara.leg.br/legin/fed/decret/2018/decreto-9580-22-novembro-2018-787360-anexo-pe.pdf'),
      ('mafon-2019.pdf','https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/irrf/mafon-2019.pdf/@@download/file'),
      ('in-rfb-1585.html','https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=67494'),
      ('lc-224-2025.html','https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp224.htm'),
      ('lei-15270-2025.html','https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm'),
      ('receita-rendimentos-capital.html','https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/preenchimento/manual-mir/rendimentos/rendimentos-do-capital')]
for name,url in jobs:
    p=dest/name
    if p.exists():continue
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
            data=r.read();ctype=r.headers.get('Content-Type')
        p.write_bytes(data)
        p.with_suffix('.source.json').write_text(json.dumps({'url':url,'sha256':hashlib.sha256(data).hexdigest(),
              'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'content_type':ctype},indent=2),encoding='utf-8')
        print(name,len(data),flush=True)
    except Exception as exc:print(name,'UNAVAILABLE',str(exc),flush=True)
