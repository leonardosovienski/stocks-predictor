"""Extrai e reproduz o pacote de reorganizações Stocks, sem instalar dependências."""
from pathlib import Path
import argparse
import hashlib
import subprocess
import sys
import zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    archive=here/'STOCKS_REORGANIZACOES_TESTADAS.zip'
    expected='e5e8b429ca89c97421ef248641ad680993ef723803d070acc621cb65867d4f64'
    with archive.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=expected:raise ValueError('O ZIP difere do pacote testado')
    destination=here.parent/'work'/('reorganization-ready-'+expected[:12])
    marker=destination/'.extraction-complete'
    if not marker.exists():
        if destination.exists():raise FileExistsError('Extracao incompleta preservada: '+str(destination))
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not (destination/name).resolve().is_relative_to(destination.resolve()):
                    raise ValueError('Caminho inseguro no ZIP')
            z.extractall(destination)
        marker.write_text(expected,encoding='utf-8')
    if marker.read_text(encoding='utf-8')!=expected:raise ValueError('Extracao de outro pacote')
    cmd=[sys.executable,str(destination/'rodar_reorganizacoes.py')]
    if args.output_dir:cmd+=['--output-dir',str(args.output_dir.resolve())]
    if args.verify_only:cmd+=['--verify-only']
    raise SystemExit(subprocess.call(cmd))

if __name__=='__main__':main()
