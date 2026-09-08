"""Executa o pacote H17 entregue, sem instalacao e sem alterar o banco operacional."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import subprocess
import sys
import zipfile

EXPECTED_SHA256='5096bf505dc72f930ffbccbc93dfe255aa37682a467ee13bf8c93846e66d2341'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    directory=Path(__file__).resolve().parent
    archive=directory/'stocks-h17-pronto-final.zip'
    with archive.open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=EXPECTED_SHA256:
        raise ValueError('O ZIP difere do pacote testado.')
    extracted=directory.parent/'work'/('h17-ready-'+EXPECTED_SHA256[:12])
    marker=extracted/'.extraction-complete'
    if not marker.exists():
        if extracted.exists():
            raise FileExistsError('Existe uma extracao incompleta; preserve-a para diagnostico: '+str(extracted))
        with zipfile.ZipFile(archive) as z:
            for name in z.namelist():
                if not (extracted/name).resolve().is_relative_to(extracted.resolve()):
                    raise ValueError('Caminho fora da pasta de extracao')
            z.extractall(extracted)
        marker.write_text(EXPECTED_SHA256,encoding='utf-8')
    if marker.read_text(encoding='utf-8')!=EXPECTED_SHA256:
        raise ValueError('Extracao pertence a outro pacote')
    command=[sys.executable,str(extracted/'rodar_h17.py')]
    if args.verify_only:
        command.append('--verify-only')
    else:
        output=args.output or directory/('h17-reexecucao-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
        command.extend(['--output',str(output.resolve())])
    subprocess.run(command,check=True)


if __name__=='__main__':
    main()
