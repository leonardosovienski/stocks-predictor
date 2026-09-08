"""Repete o diagnostico H17 offline, com dados e regras lacrados."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'code'))
from stocks_predictor.discovery_h17 import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files_sha256'].items():
        with (ROOT/name).open('rb') as stream:
            observed = hashlib.file_digest(stream, 'sha256').hexdigest()
        if observed != expected:
            raise ValueError('Arquivo diferente do lacre: '+name)
    if args.verify_only:
        print('Integridade dos arquivos: PASS. Nenhum resultado calculado.')
        return
    output = args.output or ROOT/'results'/('h17-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    result = run(ROOT/'data/quotes.db', ROOT/'data/snapshots.json', ROOT/'data/events.json',
                 ROOT/'data/identity', ROOT/'protocol.json', output)
    print('Diagnostico H17 concluido. Resultado: '+result['status'])
    print('Arquivo: '+str(output.resolve()))
    print('E um diagnostico exploratorio de precos, sem estimativa de lucro executavel.')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
