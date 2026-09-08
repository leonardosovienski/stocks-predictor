from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
sys.path[:0]=[str(REPO/'stocks_predictor'),str(ROOT/'work/runtime'),str(REPO)]
import cvm_pit
from tools.rebuild_cvm_copy import rebuild

note='''> ## Correções implementadas em cópia isolada — 2026-09-07
>
> As APIs públicas de ingestão agora gravam versões separadas, em reais,
> nas tabelas PIT da migração 0013. Base de ações desconhecida não gera
> múltiplo; retorno total exige eventos por papel e cobertura documentada.
> O novo `backtest.walk_forward` mantém quantidades, negocia após o sinal
> e contabiliza caixa/custos igualmente para estratégia e benchmark.
> Os runners julgados usam explicitamente o instrumento `legacy_*`.
> H17/H18/H19 estão bloqueadas no CLI antes de banco/ledger/desempenho:
> validar o dataset reconstruído e registrar a metodologia corrigida primeiro.
>
> [Implementação, evidências e limites](docs/research/2026-09-07-repairs.md).
> 47 testes dirigidos passaram; suíte completa será registrada na entrega.
> Parser validado no ZIP integral 2023: 475 documentos DFP e 455 FRE.
> Nenhum resultado protegido observado; nenhuma dependência de runtime nova.

'''
for name in ('HANDOFF.md','RESEARCH_FREEZE.md','STOCKS_CURRENT_STATE.md'):
    path=REPO/name
    if not path.exists():
        matches=list((REPO/'docs').rglob(name))
        if not matches:
            continue
        path=matches[0]
    s=path.read_text(encoding='utf-8')
    if 'Correções implementadas em cópia isolada' not in s:
        first,rest=s.split('\n',1)
        path.write_text(first+'\n\n'+note+rest,encoding='utf-8')

# Explicit limited demonstrator: the three issuer/ticker links already examined in
# the initial audit. No proposed broad map or inferred ticker is promoted here.
example_map={'ambev_s.a.':'ABEV3','bco_brasil_s.a.':'BBAS3','energisa_s.a.':'ENGI11'}
mapping=ROOT/'work/repair-example-map-2023.json'
mapping.write_text(json.dumps(example_map,indent=2)+'\n',encoding='utf-8')
dfp=next((ROOT/'work/raw').glob('*dfp*.zip'))
fre=next((ROOT/'work/raw').glob('*fre*.zip'))
plan={'years':[{'year':2023,'dfp_zip':str(dfp),'dfp_map':str(mapping),'fre_zip':str(fre),'fre_map':str(mapping)}]}
(ROOT/'work/repair-example-plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
copied=ROOT/'work/stocks-cvm-2023-repaired-example.db'
if not copied.exists():
    result=rebuild('C:/Users/Superleo13/stocks-predictor-work/data/stocks.db',copied,plan)
    result['scope']='2023 only, explicit three-issuer demonstrator; not a full operational backfill'
    (ROOT/'outputs/repair-copy-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name,rows in [('dfp-2023-corrigida.jsonl',cvm_pit.derive_dfp(dfp.read_bytes(),2023)),
                  ('fre-2023-documentos.jsonl',cvm_pit.derive_fre_shares(fre.read_bytes(),2023))]:
    (ROOT/'outputs'/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
print('New database copy and public-source derivations prepared without protected performance.')
