"""Archive final reviewed sources and update the current handoff, without returns."""
import json
from pathlib import Path
import shutil
from source_utils import ROOT, OUT, read

CHAT=Path(r'C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2')
repo=ROOT/'work/stocks-predictor'; archive=repo/'research/session-20260908/source-closure'
archive.mkdir(exist_ok=True)
audit=read(OUT/'integrated-readiness-12.json');snap=read(OUT/'cash-closure-12.json')
cash=snap['cash_events'];cards=read(OUT/'cash-review-cards.json')
unpaid={r['event_id'] for r in cash if r['payment_date'] is None}
pending=dict(source_manifest_sha256=audit['source_manifest_sha256'],status=audit['status'],
    future_profit_projection=None,new_historical_return_evaluations=0,
    missing_payment_dates=[{k:c[k] for k in ['event_id','ticker','isin','ex_date','action','gross_per_share','approval_date']}
        for c in cards if c['event_id'] in unpaid],
    missing_net_values=[r for r in cash if r['net_per_share'] is None],
    other_issues=[r for r in audit['issues'] if r['kind'] not in
        {'CASH_EVENT_FIELD','CASH_KNOWLEDGE_DATE','CASH_COVERAGE','H20_ADDITIONAL_CASH_INTERVAL'}],
    inventory_intervals_without_attestation=audit['conservative_required_intervals'],
    additional_documented_inventory_gap=dict(ticker='BRDT3',ex_date='2020-08-03',payment_date='2020-09-30',
        action='RENDIMENTO',components=['.01042971957','.00090991873'],withholding_rate='.20',
        source='cvm-complete-0338.pdf',pages=[1,2],
        reason='Primary notice contains monetary corrections absent from the778 frozen cash rights. Not silently added, not assigned zero.'),
    closure_rule='Unknown dates/net/tax basis, unresolved identity, incomplete inventory and future realization remain blocked; a source hash is not an execution preregistration.')
for name,value in [('PENDENCIAS_STOCKS.json',pending),('PRONTIDAO_FONTES_12.json',audit),
                   ('RECONSTRUCAO_FONTES_12.json',snap)]:
    (archive/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['source_utils.py','closure_helpers.py','assemble_source_closure.py',
             'build_source_closure7.py','build_source_closure8.py','build_source_closure9.py',
             'build_source_closure10.py','build_source_closure11.py','build_source_closure12.py',
             'render_source_pages.py','prepare_source_delivery.py']:
    shutil.copyfile(CHAT/'work'/name,archive/name)
shutil.copyfile(OUT/'parser-validation.json',archive/'parser-validation-before-incomplete-row-fix.json')
top='''## Revisão de fontes e pendências (08/09/2026 UTC)

Pedido do operador: resolver também as fontes pendentes. Protocolo0700f82,
SHA da8b91a7a263d9870822c58af85b4a47f2c051e932ecb3099fea986ba4456c49,
anterior à reconstrução. Nenhuma nova avaliação de retorno; 53/55 preservados.
As versões01–12 permanecem preservadas fora de bancos e ledgers.

Entrada atual: work/source-closure-20260908/execution-inputs-12.
Manifesto b9dfab5fb2dc67f7fcdd71f52b325a3a1d442917c116f514fd09f11926876f7e.
788 arquivos verificados;754 arquivos de fonte, dos quais753 publicações/fontes
primárias e1 reconstrução local derivada.365.198 cotações. Os778 direitos
originais são preservados em801 linhas de pagamento, com9 cronogramas e32
parcelas. Datas ausentes:356→37; valores líquidos ausentes:389 registros
originais→66 linhas derivadas.8 desdobramentos inteiros integrados;28 eventos
societários ainda exigem termos, entrega ou base fiscal.1.248 intervalos de
inventário permanecem sem certificação integral. Estas contagens se sobrepõem.

Falhas corrigidas nesta revisão: associações entre JCP/dividendos retiradas;
reconciliação de parcelas sem pagar o total original duas vezes; retificações
ligadas ao aviso original; datas TIM corrigidas; tabelas em imagem revisadas;
fonte derivada não contada como primária. Créditos B3 com aprovação ausente
agora aparecem em incomplete_rows e exigem fonte adicional para associação;
não são descartados silenciosamente nem promovidos a dados completos.
Líquidos de atualização Selic usam prazo documentado e regraPF específica.
Os líquidos2026 tratados aqui são retenção no pagamento, não imposto mínimo
anual pessoal. Capital devolvido, base fiscal e frações continuam dependentes
do livro e das fontes aplicáveis. SLC2019: data provada, unidades antes/depois
do desdobramento ainda não reconciliadas. BRDT2020: aviso contém duas
atualizações monetárias ausentes no inventário original; lacuna explicitada.

27 testes focados passam; Ruff/Pyright serão registrados com a suíte final.
A validação completa e a wheel portátil serão anexadas após este commit.
Usar py -3.13 explícito, sem venv ou instalação. Extrações01–03 usaram3.14;
as materializações04–12 e os testes finais usam o Python global3.13.

Resultado econômico: BLOCKED_MISSING_EVIDENCE; lucro e projeção permanecem
null. Não houve ordens, custos, agentes, escrita nos bancos ou ajusteH1–H20.
O protocolo de fontes não libera retornos: ainda é necessária pré-inscrição
específica vinculada ao hash final das fontes, após completar a evidência.
Evidências e fila completa: research/session-20260908/source-closure.

'''
p=repo/'HANDOFF.md';old=p.read_text(encoding='utf-8')
marker='## Correções concluídas da revisão (08/09/2026 UTC)'
assert marker in old
p.write_text(top+old[old.index(marker):],encoding='utf-8',newline='\n')
for name in ['STOCKS_CURRENT_STATE.md','docs/continuation/UPDATE_20260908.md']:
    p=repo/name;old=p.read_text(encoding='utf-8')
    p.write_text(top+old,encoding='utf-8',newline='\n')
p=repo/'pyproject.toml';t=p.read_text(encoding='utf-8')
old='"stocks_predictor/buffered_rebalance.py"]'
assert old in t
t=t.replace(old,'"stocks_predictor/buffered_rebalance.py", "stocks_predictor/cash_source_audit.py", "stocks_predictor/source_closure.py"]')
p.write_text(t,encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in audit.items() if k!='issues'}))
