from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'; OUT=ROOT/'outputs'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
v=read(OUT/'VALIDACAO_LUCRO_STOCKS.json')
cash=read(OUT/'VALIDACAO_PROVENTOS_AMPLIADA_STOCKS_V2.json')
rate=read(OUT/'VALIDACAO_CUSTO_OPORTUNIDADE_STOCKS.json')
lines=['**Stocks: validação técnica e econômica — 7 de setembro de 2026**','',
       '**Ainda não há lucro líquido validado para operar.** Há valorização histórica nas simulações, mas a incerteza sobre vantagem futura, os proventos incompletos e a execução impedem chamar isso de estratégia lucrativa comprovada. H19 trimestral continua apenas como hipótese em Discovery.','',
       'Os 539 testes passaram em 153,65 segundos. Cobertura: 79%; Ruff no escopo CI, Pyright configurado, construção do wheel e importação fora do repositório passaram. O segundo cálculo confirmou 9.732 células, com diferença máxima de 2,22×10⁻¹⁶ por arredondamento numérico. Fatores, papéis selecionados e períodos ficaram fixos.','',
       'A tabela mostra **vantagem média sobre o universo comparável**, em pontos percentuais por mês, após um desconto fixo de 72 pontos-base por período de manutenção. Esse desconto é cenário de custo, não giro efetivamente medido. O cenário adverso compra pelo maior e marca a saída pelo menor entre abertura e fechamento; aplica a mesma regra ao benchmark. Ele não é um limite inferior matemático do excesso de retorno.','',
       '| Hipótese | Abertura | Fechamento | Preço adverso | Intervalo descritivo de 95%, abertura |',
       '|---|---:|---:|---:|---:|']
for t in v['trials']:
    s=t['modes']['open']['summary']; ci=s['descriptive_stationary_bootstrap_95pct_after_72bp']
    values=[t['modes'][m]['summary']['spread_after_72bp_per_month']*100 for m in ('open','close','worst')]
    lines.append(f"| {t['family']} {'mensal' if t['holding_months']==1 else 'trimestral'} | {values[0]:+.3f} | {values[1]:+.3f} | {values[2]:+.3f} | {ci[0]*100:+.3f} a {ci[1]*100:+.3f} |")
lines += ['',
    '**Os 12 intervalos de incerteza incluem zero.** O bootstrap preserva blocos de tempo de tamanho médio de um ano e usa 10 mil reamostragens pareadas. São intervalos descritivos após observar a pesquisa, sem correção pela busca adaptativa: não são evidência confirmatória. A medição continua omitindo dividendos/JCP ordinários, impostos e disponibilidade efetiva dos direitos.','',
    '**Ganho no passado e risco.** Abaixo está o crescimento geométrico hipotético das marcas na abertura, subtraindo 72 pb a cada período e supondo reinvestimento de todos os valores marcados. Valores ainda não recebidos podem estar incluídos nessas marcas; portanto isto não é saldo executável de uma conta. As quedas são medidas entre finais de período e podem subestimar as perdas dentro de cada mês ou trimestre.','',
    '| Hipótese | Janela de compra/saída | Crescimento hipotético anual | Maior queda entre marcas |',
    '|---|---|---:|---:|']
for t in v['trials']:
    s=t['modes']['open']['summary']; p=s['synthetic_strategy_after_flat_72bp']
    lines.append(f"| {t['family']} {'mensal' if t['holding_months']==1 else 'trimestral'} | {s['start']} a {s['end']} | {p['annualized_geometric_return']*100:.2f}% | {p['period_mark_max_drawdown']*100:.2f}% |")
lines += ['',
    'Na H19 trimestral, o cenário adverso reduz o crescimento hipotético e mantém perdas elevadas. Não foi escolhido o fechamento só porque ele apresentou resultado melhor. A régua exploratória original de 0,42 p.p./mês continua sendo uma premissa de pesquisa; você informou capital de R$5–10 mil, sem definir um lucro mínimo anual.','',
    f"**Custo de oportunidade.** Na mesma janela trimestral, a Selic diária oficial acumulou o equivalente a {rate['comparisons'][1]['selic_gross_annualized']*100:.2f}% ao ano, antes de impostos e custos de produto. A proximidade dos números pede cuidado com o valor econômico da pesquisa. A comparação ainda não determina um vencedor líquido: a carteira de ações omite dividendos e a referência Selic é bruta. [Fonte e unidade da série 11, Banco Central](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic).",'',
    '**Proventos: avancei na fonte, sem inventar retorno.** Os históricos foram localizados para os 126 instrumentos da coorte, incluindo nomes antigos de empresas que deixaram de negociar. Foram examinadas 872 linhas nas janelas necessárias; os preços anteriores informados coincidem com o COTAHIST. Só 92 linhas encontraram ao menos uma data de pagamento no suplemento B3 consultado, o que não certifica a completude ou unicidade desses pagamentos. Algumas mudanças de emissor ainda exigem reconciliação.','',
    'Há 10 grupos com valor, data e aprovação repetidos. Repetição não equivale a erro: na WEGE3, três registros iguais correspondem no suplemento a pagamentos em 2026, 2027 e 2028. Somar tudo como dinheiro imediatamente disponível ou apagar parcelas duplicadas distorceria a carteira. A primeira auditoria de correspondência por texto foi corrigida para comparar decimais sem zeros insignificantes; ambas versões ficaram preservadas e nenhuma gerou retorno de estratégia.','',
    '**Capital de R$5–10 mil.** Na H19 trimestral, 182/233 tickets com R$5 mil e 115/233 com R$10 mil ficariam abaixo de 100 ações, usando alocação equiponderada inicial e custo por lado de 36 pb. Localizei 4.225 cotações fracionárias em 4.226 endpoints procurados e todos os endpoints dos ativos selecionados. A única ausência é JBSS32 em 01/07/2025, BDR cujo suplemento informa lote de uma unidade; não se deve exigir um mercado fracionário separado para esse caso. [Regra B3 de lote unitário de BDR](https://www.b3.com.br/pt_br/noticias/alteracao-no-lote-padrao-de-bdrs-e-etfs.htm).','',
    'Isso fecha a busca de preços necessários, mas não mede ainda uma carteira contínua de R$5 mil ou R$10 mil: faltam giro efetivo, lotes/frações gerados por eventos, recebimentos, custos sobre as ordens reais e impostos. Cotações diárias também não garantem execução ao preço mostrado.','',
    '**H1–H19 e decisão.** A revisão anterior de H1–H16 permanece preservada, com 15 estudos negativos e H3 não executada. Eles não foram rodados novamente nesta etapa. H17 continua inconclusiva e sem ganho demonstrado; as quatro configurações H18/H19 receberam esta validação. Não há promoção a Proof, operação real ou evidência de que o lucro futuro esteja garantido. H18 perde prioridade por instabilidade; H19 trimestral merece no máximo pesquisa limitada à reconciliação de caixa e execução das mesmas seleções.','',
    'Contagem conservadora atual: pelo menos 32 configurações e 37 avaliações históricas, com histórico adaptativo antigo desconhecido. As oito novas sensibilidades de preço foram contabilizadas. Reproduções idênticas, auditorias de fonte e a comparação de oportunidade não são novas hipóteses independentes. Nenhum parâmetro, janela ou limiar foi ajustado para produzir lucro.','',
    '**Reprodução.** O pacote `STOCKS_VALIDACAO_LUCRO_TESTADA.zip` e o lançador `RODAR_VALIDACAO_LUCRO_STOCKS.py` reproduzem offline a observação anterior, o segundo cálculo e os 12 cenários com bootstrap. Incluem fontes, hashes, código e logs. O lançador exige Python 3.13 e não instala dependências, não envia ordens e não faz downloads. A confirmação da execução do pacote fica em `VALIDACAO_LUCRO_REPRODUCAO.json`.','',
    'O próximo teste econômico depende da conclusão do caixa: recebimentos nas datas efetivas, reinvestimento somente do disponível, giro entre carteiras, quantidades inteiras e benchmark sob a mesma execução. Se essa reconciliação exigir pesquisa extensa diante da vantagem e da incerteza atuais, encerrar o aprofundamento será uma decisão econômica válida. Não faz sentido multiplicar variantes até aparecer um positivo.'
]
text='\n'.join(lines)+'\n'
with (OUT/'VALIDACAO_LUCRO_STOCKS_RESULTADO.md').open('x',encoding='utf-8') as f:f.write(text)
(REPO/'docs/research/2026-09-07-profit-validation-results.md').write_text(text,encoding='utf-8')
sha=hashlib.sha256((OUT/'VALIDACAO_LUCRO_STOCKS.json').read_bytes()).hexdigest()
record={'protocol_id':v['protocol']['protocol_id'],'observed_at_utc':v['observed_at_utc'],
        'code_commit':'28cf87e1819d25eb031067d6c707fa8519171953','output_sha256':sha,
        'mode':'DISCOVERY_VALIDATION_NOT_EXECUTABLE_PROFIT','new_price_scenarios':8,
        'budget':v['budget'],'status':'NO_CONFIRMED_NET_PROFIT','all_12_descriptive_CIs_include_zero':True,
        'ordinary_cash_returns_not_observed':True,'tests':'539 passed in 153.65s; 79% coverage'}
ledger=REPO/'docs/research/2026-09-07-value-observations.jsonl'
if any(json.loads(line).get('protocol_id')==record['protocol_id'] for line in ledger.read_text(encoding='utf-8').splitlines()):raise ValueError('Already recorded')
with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
paths=[Path(r'C:\Users\Superleo13\stocks-predictor-work\data\stocks.db'),ROOT/'work/stocks-tested-real-v2-20260907.db']
integrity=[]
for p in paths:
    with p.open('rb') as f:hashval=hashlib.file_digest(f,'sha256').hexdigest()
    integrity.append({'path':str(p),'sha256':hashval})
assert integrity[0]['sha256']=='a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4'
assert integrity[1]['sha256']=='a8238568980d3303890b04590cfb5c55ab2d24c9271edd86820269336b09679a'
with (OUT/'VALIDACAO_LUCRO_AUDITORIA.json').open('x',encoding='utf-8') as f:json.dump({**record,'original_databases_unchanged':integrity},f,ensure_ascii=False,indent=2)
print('Report, append-only ledger and original DB hashes recorded.')
