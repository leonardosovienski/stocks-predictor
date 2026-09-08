"""Archive the additive source revision before testing the committed checkout."""
import json
import shutil
from source_utils import ROOT, OUT, read
from pathlib import Path

chat=Path(r'C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2')
repo=ROOT/'work/stocks-predictor';archive=repo/'research/session-20260908/source-closure'
snap=read(OUT/'cash-closure-13.json');a=read(OUT/'integrated-readiness-13.json')
old=read(archive/'PENDENCIAS_STOCKS.json')
cards={r['event_id']:r for r in read(OUT/'cash-review-cards.json')}
cash=read(OUT/'execution-inputs-13/cash-events.json')
pending={**old,'source_revision':13,'source_manifest_sha256':a['source_manifest_sha256'],
    'missing_payment_dates':[{k:r[k] for k in ['event_id','ticker','isin','ex_date','action','gross_per_share']}
        | {'approval_date':cards[r['event_id']]['approval_date'],
           'unresolved_payment_evidence':r.get('unresolved_payment_evidence')} for r in cash if not r['payment_date']],
    'missing_net_values':[r for r in cash if r['net_per_share'] is None],
    'other_issues':[r for r in a['issues'] if r['kind'] not in
                    {'CASH_COVERAGE','CASH_EVENT_FIELD','H20_ADDITIONAL_CASH_INTERVAL'}],
    'raw_records_preserved':778,'unique_declared_entitlements':777,
    'duplicate_raw_record_mapped_without_second_payment':snap['duplicate_lineage'],
    'quote_coverage_end':'2026-04-01','last_observed_exchange_session':'2026-08-27',
    'correction_to_prior_report':'Quote coverage ends April1; the frozen exchange-session list extends through August27. '
        'The earlier report incorrectly described both as ending April1.',
    'rejected_incomplete_primary_download':snap['rejected_primary_downloads']}
(archive/'PENDENCIAS_STOCKS_12.json').write_bytes((archive/'PENDENCIAS_STOCKS.json').read_bytes())
(archive/'PENDENCIAS_STOCKS.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(archive/'PENDENCIAS_STOCKS_13.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(OUT/'integrated-readiness-13.json',archive/'PRONTIDAO_FONTES_13.json')
for pattern in ['*13*.json']:
    for p in OUT.glob(pattern):shutil.copyfile(p,archive/p.name)
for name in ['acquire_followup13.py','index_followup13.py','acquire_overlooked13.py',
             'build_source_closure13.py','create_source13_fixtures.py','verify_source_closure13.py',
             'prepare_source_closure13.py','assemble_source_closure.py']:
    shutil.copyfile(chat/'work'/name,archive/(name if name!='assemble_source_closure.py' else 'assemble_source_closure13.py'))
section='''## Complemento de fontes — revisão 13 (08/09/2026 UTC)

Entrada atual: work/source-closure-20260908/execution-inputs-13, manifesto
7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b.
12 datas preenchidas; uma duplicata Hypera conciliada com documentos da
companhia. As 778 linhas brutas permanecem preservadas: representam 777
direitos distintos, materializados em 800 pagamentos com 9 cronogramas.
Datas ausentes 37→24; líquidos ausentes 66→54 linhas derivadas.
14 datas de formulários continuam apenas como candidatas: prazo máximo ou
cronograma agregado superado não é confirmação de recebimento.

O seletor de documentos inclui Relatório Proventos e avisos sem assunto,
começa na aprovação e limita também a data de envio: uma retificação tardia
não existia na data original do evento. 174 candidatos mantidos, todas as
versões preservadas. Deduplicação exige registros B3 idênticos e revisão
explícita de uma única distribuição na companhia; parcelas Iguatemi não
são eliminadas automaticamente. Não houve ajuste de parâmetros ou retornos.

827 arquivos de entrada, 791 fontes primárias e 1 reconstrução derivada;
365.198 cotações. Correção do relatório anterior: a cobertura de cotações
termina em 01/04/2026, mas a lista de pregões vai até 27/08/2026.
O PDF parcial Hapvida ITR não serve como prova; o prospecto integral contém
a confirmação do pagamento GNDI. Alguns relatórios CVM têm preenchimento
NUL após EOF: os bytes originais foram preservados, sem truncar ou editar.

Continuam 28 entradas societárias e 1.248 intervalos sem inventário completo
certificado. Lucro e projeção continuam null/BLOCKED_MISSING_EVIDENCE.
Protocolo de fontes e H1–H20 preservados; 53/55; zero novos retornos.
Nenhuma ordem, instalação, serviço pago, agente adicional ou escrita em
banco, ledger ou quarentena. Nenhuma nova dependência de runtime.

Validação 13: auditoria 12 idêntica com código novo, auditoria 13 reproduzida;
11 adulterações rejeitadas. Suíte completa e wheel serão registradas após
o commit de código; não confundir essa validação de fontes com lucro.

'''
for name in ['HANDOFF.md','STOCKS_CURRENT_STATE.md','docs/continuation/UPDATE_20260908.md']:
    p=repo/name;p.write_text(section+p.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
print(json.dumps({'dates_remaining':len(pending['missing_payment_dates']),
    'net_remaining':len(pending['missing_net_values']),'source_manifest':a['source_manifest_sha256']}))
