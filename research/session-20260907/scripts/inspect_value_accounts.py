from pathlib import Path
import csv,io,zipfile
p=Path.cwd()/'work/source-acquisition/dfp_cia_aberta_2023.zip'
names={'00.000.000/0001-91','07.526.557/0001-00','47.960.950/0001-21','09.346.601/0001-25'}
with zipfile.ZipFile(p) as z:
 for statement in ('BPP_con','DRE_con','BPP_ind','DRE_ind'):
  print(statement)
  for r in csv.DictReader(io.TextIOWrapper(z.open(f'dfp_cia_aberta_{statement}_2023.csv'),encoding='latin-1'),delimiter=';'):
   if r['CNPJ_CIA'] not in names or r['ORDEM_EXERC']!='ÚLTIMO':continue
   code=r['CD_CONTA'];desc=r['DS_CONTA'].lower()
   if ('patrim' in desc and len(code)==4) or ('controladores' in desc) or (('lucro' in desc or 'preju' in desc) and 'período' in desc):
    print(r['CNPJ_CIA'],r['VERSAO'],r['CD_CONTA'],r['DS_CONTA'],r['VL_CONTA'],r['ESCALA_MOEDA'])
