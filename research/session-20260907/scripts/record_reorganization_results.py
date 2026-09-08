from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
OUT=ROOT/'outputs'
path=OUT/'h18-h19-reorganization-observation.json'
result=json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
changed=result['changed_returns']
old=json.loads((OUT/'h18-h19-repaired-observation.json').read_text(encoding='utf-8'))
for a,b in zip(old['trials'],result['trials']):
    assert (a['family'],a['holding_months'])==(b['family'],b['holding_months'])
    for x,y in zip(a['periods'],b['periods']):
        assert (x['asof'],x.get('entry'),x.get('exit'))==(y['asof'],y.get('entry'),y.get('exit'))
        assert [{k:m[k] for k in ('ticker','cnpj','isin','factor','selected')} for m in x['members']]==[{k:m[k] for k in ('ticker','cnpj','isin','factor','selected')} for m in y['members']]
assert len(changed)==70 and all(d['old_return'] is None for d in changed)
assert all(t['summary']['overall']['complete_periods']==t['summary']['overall']['eligible_periods'] for t in result['trials'])
audit={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'tested_code_commit':head,
    'test_suite':'533 passed in 153.45s','coverage_percent':80,'specific_tests':18,'ruff_ci_scope':'PASS',
    'pyright_configured_scope':'PASS','wheel_build':'PASS','installed_wheel_import_outside_checkout':'PASS',
    'changed_cells':70,'distinct_holding_intervals_now_measured':35,'previously_scored_returns_changed':0,
    'original_selections_and_factors_verified_identical':True,'primary_reorganizations':13,'subscription_policies':6,
    'operational_db_sha256':sha(Path(r'C:\Users\Superleo13\stocks-predictor-work\data\stocks.db')),
    'tested_prior_source_db_sha256':sha(ROOT/'work/stocks-tested-real-v2-20260907.db'),
    'result_sha256':sha(path),'protocol_semantic_sha256':'c714aee9fde793fd1e612426782dac61abe5f6231c6a0d2429e115618622a2f4'}
assert audit['operational_db_sha256']=='a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4'
assert audit['tested_prior_source_db_sha256']=='a8238568980d3303890b04590cfb5c55ab2d24c9271edd86820269336b09679a'
(OUT/'H18_H19_REORGANIZACOES_AUDITORIA.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
table=['| Configuração | Períodos medidos/elegíveis | IC médio | Diferença bruta por mês | Após desconto de 72 pb por período |',
       '|---|---:|---:|---:|---:|']
for trial in result['trials']:
    s=trial['summary']['overall']
    table.append(f"| {trial['family']} {'mensal' if trial['holding_months']==1 else 'trimestral'} | {s['complete_periods']}/{s['eligible_periods']} | {s['available_case_mean_ic']:+.5f} | {s['complete_case_spread_per_month']*100:+.4f} p.p. | {s['adverse_spread_after_72bp_per_month']*100:+.4f} p.p. |")
text='''A nova rodada H18/H19 foi executada e reproduzida em código versionado. Os 35 intervalos
antes sem medição agora têm um resultado no diagnóstico de preços mais direitos societários.
São 70 células recuperadas nas duas famílias, sem alterar nenhum retorno anteriormente medido,
nenhum fator, seleção ou data. As quatro configurações permanecem **NO_PRIORITY_UPGRADE**.

'''+ '\n'.join(table)+'''

A H19 trimestral mantém IC e diferença após custos positivos nas duas metades fixadas,
2018–2021 e 2022–2025. Seu resultado após o desconto de estresse equivale a 0,3588 p.p.
por mês, abaixo da régua de pesquisa de 0,42 p.p. A H19 mensal fica negativa nesse
estresse; a H18 tem IC negativo na primeira metade. Não houve ajuste de parâmetros.

A régua de 0,42 p.p. é uma hipótese de alocação de pesquisa, aproximadamente compatível
com R$500 anuais adicionais sobre R$10 mil. O usuário informou capital de R$5–10 mil,
mas não confirmou um lucro mínimo ou horas de manutenção. Este diagnóstico não permite
concluir REAL_EDGE_BUT_ECONOMICALLY_TOO_SMALL: o próprio edge líquido ainda não foi provado.

O resultado trimestral bruto condicionado aos antigos períodos completos era 1,0458 p.p.
por mês. Com todos os períodos medidos nesta nova definição, ficou em 0,5988 p.p.
A versão antiga superestimava a leitura favorável ao deixar períodos problemáticos de fora.
A diferença também inclui a mudança explícita de estimando para direitos societários;
não é uma comparação entre duas medições do mesmo retorno total.

As conversões usam termos finais de emissores, CVM e B3. A GNDI entrega 5,24364185943
ações HAPV e dois pagamentos, ambos com data de 29/03/2022. A LCAM entrega 0,43884446
RENT e o dividendo de fechamento. Fibria, BR Malls, Iguatemi, Aliansce, TIM, Soma,
Motiva, JBS e Natura preservam as respectivas quantidades e/ou caixa. A cisão da
Vamos mantém VAMO3 e adiciona 1,15136366 AMOB3; 28,290555% era migração do histórico
de negociação, não a proporção de entrega de ações. No Carrefour foi usada a opção
padrão de R$8,50 em dinheiro, sem escolher uma alternativa pelo resultado posterior.

Na saída de SOMA3 em 01/08/2024, AZZA3 é um direito marcado a mercado, com crédito
previsto em 05/08. Na tentativa de entrada em SOMA3 em 01/08, não há compra nem
conversão retroativa: a alocação fica em caixa. Os documentos originais e seus hashes
estão no pacote, junto às cotações B3 e aos registros de cada conversão.

Limites: quantidades fracionárias teóricas; valores brutos; direitos de subscrição
marcados a zero, sem exercício ou venda; dividendos e JCP ordinários omitidos.
Datas de pagamento refletem comunicados, não extratos de conta; algumas datas de
crédito físico continuam desconhecidas. Recebíveis não são reinvestidos. O desconto
de 36/72 pb é um cenário fixo por período, não uma apuração de giro, impostos ou custos
efetivos. As médias trimestrais foram divididas por três para comparação, não compostas.
Não é retorno total, backtest executável, estimativa de lucro líquido ou autorização de capital.

O próximo teste barato se concentra na execução da carteira trimestral congelada da H19.
A análise das seleções encontrou 40,16% de peso-alvo médio em nomes novos por rebalanceamento.
Isso não mede o giro financeiro efetivo: faltam a deriva de preços, quantidades inteiras,
eventos e liquidação. Para alcançar a mesma régua com o resultado bruto observado, o
orçamento de custos seria 0,5365% por trimestre; não se alterou a régua nem se declarou
que esse custo é alcançável. A fonte atual possui 9.812 registros de caixa não validados,
mas nenhuma das 233 posições trimestrais selecionadas tem seu intervalo integralmente
coberto pelo cadastro de proventos verificados. A prioridade é verificar se essa lacuna
pode ser resolvida a baixo custo antes de financiar nova simulação de lucro.

H18 perde prioridade; H19 permanece exploratória e sem promoção. H11 não foi reaberta:
reconstruir momentum de retorno total exige histórico limpo também na janela do sinal.
Modelos novos não resolvem essa lacuna. Regra de parada: uma comparação fixa de execução,
sem otimizar frequência, filtros, thresholds ou períodos; abandonar o aprofundamento se
a cobertura de caixa não puder ser obtida a baixo custo ou se o estresse de execução
eliminar a margem econômica. Nenhuma Proof ou amostra histórica intacta foi criada.

Próximas ações registradas: auditar cobertura primária de caixa dos membros originais;
reconciliar datas e quantidades por ISIN; resolver crédito físico e frações; medir giro
e caixa efetivos para R$5 mil e R$10 mil; aplicar a mesma régua com execução na abertura,
fechamento e pior preço. São tarefas futuras, ainda não executadas neste resultado.

Validação técnica: 533 testes passaram em 153,45 s, cobertura de 80%; Ruff no escopo do
CI, Pyright configurado, build e importação do wheel fora do checkout passaram.
Código testado: '''+head+'''. Nenhuma dependência nova de runtime.
Banco operacional e base anterior preservados por SHA-256. Orçamento conservador:
ao menos 24 configurações e 29 avaliações históricas, com busca adaptativa antiga
desconhecida. A reprodução idêntica é verificação técnica, não evidência independente.
'''
# Offline reproduction is verified separately before delivering this report.
text=text.replace('foi executada e reproduzida em código versionado','foi executada em código versionado')
(OUT/'H18_H19_REORGANIZACOES_RESULTADO.md').write_text(text,encoding='utf-8')
(REPO/'docs/research/2026-09-07-reorganization-results.md').write_text(text,encoding='utf-8')
record={'protocol_id':result['protocol_id'],'observed_at_utc':result['observed_at_utc'],'tested_code_commit':head,
        'result_sha256':sha(path),'trials':[{k:t[k] for k in ('family','holding_months','summary')} for t in result['trials']],
        'minimum_cumulative_configurations':24,'minimum_cumulative_return_evaluations':29,'proof_trials':0,
        'same_historical_cohorts_not_independent_evidence':True,'changed_cells':70,'previously_scored_cells_changed':0,
        'features_and_selections_preserved':True,'diagnostic_is_not_total_return':True}
ledger=REPO/'docs/research/2026-09-07-value-observations.jsonl'
if result['protocol_id'] in ledger.read_text(encoding='utf-8'):raise ValueError('already recorded')
with ledger.open('a',encoding='utf-8') as stream:stream.write(json.dumps(record,ensure_ascii=False)+'\n')
feasibility=json.loads((OUT/'H19_PROXIMO_TESTE_VIABILIDADE.json').read_text(encoding='utf-8'))
(REPO/'docs/research/2026-09-07-next-execution-feasibility.json').write_text(json.dumps(feasibility,ensure_ascii=False,indent=2),encoding='utf-8')
handoff=REPO/'HANDOFF.md'
prefix='''## H18/H19: reorganizações executadas, sem promoção (2026-09-07)

Código 54fd8643ef43c3b8182deb0d82a8e186498f1f91: 533 testes em 153,45 s; cobertura 80%,
Ruff CI, Pyright configurado, build e importação externa aprovados. 35 intervalos/70 células
passaram a ter marca diagnóstica; zero retornos já medidos, fatores ou seleções alterados.
Todos os 93 meses e 31 trimestres elegíveis estão medidos nesta definição. Isso NÃO fecha
o cadastro de retorno total, frações ou entrega física. Direitos de subscrição a zero,
dividendos/JCP ordinários omitidos e valores de reorganizações brutos continuam explícitos.

Todas as quatro configurações NO_PRIORITY_UPGRADE. H19 trimestral estável, +0,358834 p.p.
por mês após desconto de 72 pb por trimestre, abaixo de 0,42 p.p. H19 mensal negativa
em estresse. H18 tem IC negativo na primeira metade. Nenhum GO, Proof ou lucro líquido.
Contagem >=24 configurações e >=29 avaliações históricas; manter saídas anteriores.

Checagem seguinte executada sem novos retornos: H19 trimestral tem 40,16% de peso-alvo
em nomes novos por rebalanceamento; isso NÃO mede giro real. Nenhuma das 233 posições
selecionadas tem cobertura integral de caixa já verificada (cadastro só ABEV/ENGI).
Próximo passo, se barato: obter cobertura primária e medir execução das MESMAS seleções,
sem tunar fator/período/régua. Regras de parada e cinco ações em reorganization-results.md;
viabilidade em next-execution-feasibility.json. H11 e ML não foram reabertos.

'''
handoff.write_text(prefix+handoff.read_text(encoding='utf-8'),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
