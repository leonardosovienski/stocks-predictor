"""Bounded public-source capture for R5; originals never overwritten."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

SOURCES = [
    ('COTAHIST_A2017.ZIP', 'https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A2017.ZIP'),
    ('faber-tactical.pdf', 'https://mebfaber.com/wp-content/uploads/2016/05/SSRN-id962461.pdf'),
    ('fnet-fs2024.pdf', 'https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=672335'),
    ('fnet-ago2025.pdf', 'https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=941503'),
    ('rico-costs.html', 'https://www.rico.com.vc/custos/'),
    ('xp-costs.html', 'https://www.xpi.com.br/custos-operacionais/'),
    ('receita-tax.html', 'https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/bolsa-de-valores'),
    ('receita-exemption.html', 'https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/isencoes'),
]


def main(output):
    output = Path(output).resolve()
    if not output.is_relative_to(Path(r'C:\STOCKS').resolve()):
        raise ValueError('Local project files must stay under C:\\STOCKS')
    output.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES:
        path = output/name
        if path.exists() or path.with_suffix(path.suffix+'.receipt.json').exists():
            raise FileExistsError(path)
        receipt = {'url':url, 'requested_at_utc':datetime.now(timezone.utc).isoformat()}
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'StocksResearch/1.0 (public-source research)'})
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read(150_000_001)
                if len(data) > 150_000_000:
                    raise ValueError('Source exceeds bounded capture size')
                receipt.update(status=response.status, final_url=response.url,
                               content_type=response.headers.get('Content-Type'))
            path.write_bytes(data)
            receipt.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                           signature=data[:8].hex(),path=str(path))
        except Exception as error:
            receipt['error'] = str(error)
        receipt['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
        path.with_suffix(path.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
