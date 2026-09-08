"""Reproduz as rodadas H18/H19 entregues, offline e sem instalacao."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import subprocess
import sys
import zipfile

EXPECTED_SHA256='ce8d1573257f962884dec8078c3a6f042fcb2b0ca3c1927e1ba583069ff57364'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    directory=Path(__file__).resolve().parent
    archive=directory/'STOCKS_H18_H19_TESTADOS.zip'
    with archive.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=EXPECTED_SHA256:raise ValueError('O ZIP difere do pacote testado.')
    extracted=directory.parent/'work'/('value-ready-'+EXPECTED_SHA256[:12])
    marker=extracted/'.extraction-complete'
    if not marker.exists():
        if extracted.exists():raise FileExistsError('Extracao incompleta preservada: '+str(extracted))
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not (extracted/name).resolve().is_relative_to(extracted.resolve()):
                    raise ValueError('Caminho fora da pasta de extracao')
            z.extractall(extracted)
        marker.write_text(EXPECTED_SHA256,encoding='utf-8')
    if marker.read_text(encoding='utf-8')!=EXPECTED_SHA256:raise ValueError('Extracao de outro pacote')
    command=[sys.executable,str(extracted/'rodar_pesquisa.py')]
    if args.verify_only:command.append('--verify-only')
    else:
        output=args.output_dir or directory/('stocks-reexecucao-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        command.extend(['--output-dir',str(output.resolve())])
    subprocess.run(command,check=True)


if __name__=='__main__':main()
