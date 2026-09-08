"""Verifica, extrai e reproduz offline a validacao Stocks. Python 3.13."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent
PACKAGE=ROOT/'STOCKS_VALIDACAO_LUCRO_TESTADA.zip'
EXPECTED='7b3722cd2bf10fcc82ca25c93c8aec82a32609ac3619baf3d881b6a1ed217a36'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT.parent/'work/profit-validation-reproduction')
parser.add_argument('--verify-only',action='store_true')
args=parser.parse_args()
with PACKAGE.open('rb') as stream:
    if hashlib.file_digest(stream,'sha256').hexdigest()!=EXPECTED:raise ValueError('Pacote alterado')
base=ROOT.parent/'work'/('profit-validation-ready-'+EXPECTED[:12])
if not base.exists():
    base.mkdir(parents=True)
    with zipfile.ZipFile(PACKAGE) as z:
        for name in z.namelist():
            if not (base/name).resolve().is_relative_to(base.resolve()):raise ValueError('Caminho inseguro no pacote')
        z.extractall(base)
    (base/'.extraction-complete').write_text(EXPECTED,encoding='utf-8')
elif not (base/'.extraction-complete').exists():raise ValueError('Extracao anterior incompleta; use uma pasta nova')
command=[sys.executable,str(base/'rodar_validacao.py'),'--output-dir',str(args.output_dir.resolve())]
if args.verify_only:command.append('--verify-only')
subprocess.run(command,check=True)
