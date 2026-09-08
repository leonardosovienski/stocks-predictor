"""Reproduce only the frozen source-readiness audit; no network, trades or returns."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('auditoria-reproduzida.json'))
    args=parser.parse_args()
    if sys.version_info[:2] != (3,13):
        raise RuntimeError('Use o Python global3.13: py -3.13 -I REPRODUZIR_FONTES.py')
    if args.output.exists():
        raise FileExistsError('Escolha outro --output; auditorias existentes são preservadas.')
    root=Path(__file__).resolve().parent
    manifest=json.loads((root/'PACKAGE_SHA256.json').read_text(encoding='utf-8'))
    for name,expected in manifest.items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or digest(path)!=expected:
            raise ValueError('Conteúdo do pacote alterado: '+name)
    wheel,=sorted((root/'wheel').glob('*.whl'))
    sys.path.insert(0,str(wheel))
    from stocks_predictor import source_closure
    if not str(source_closure.__file__).startswith(str(wheel)):
        raise RuntimeError('O módulo não veio da wheel verificada.')
    result=source_closure.audit(root/'baseline',root/'inputs',root/'signals.json',root/'source-protocol.json')
    raw=(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n').encode('utf-8')
    if raw!=(root/'expected-audit.json').read_bytes():
        raise ValueError('Resultado diferente da auditoria congelada.')
    with args.output.open('xb') as stream:stream.write(raw)
    print(json.dumps(dict(reproduction='REPRODUCED_BYTE_FOR_BYTE',economic_status=result['status'],
        input_files_verified=result['verified_input_files'],primary_files=result['verified_primary_files'],
        profit=result['profit'],future_profit_projection=result['future_profit_projection'],
        new_historical_return_evaluations=0,output_sha256=hashlib.sha256(raw).hexdigest())))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
