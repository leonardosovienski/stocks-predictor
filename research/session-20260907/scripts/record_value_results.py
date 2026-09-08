from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parent.parent
REPO=ROOT/'work/stocks-predictor'
first=json.loads((ROOT/'outputs/h18-h19-first-observation.json').read_text(encoding='utf-8'))
path=ROOT/'outputs/h18-h19-repaired-observation.json'
result=json.loads(path.read_text(encoding='utf-8'))
digest=hashlib.sha256(path.read_bytes()).hexdigest()
record={'observed_at_utc':result['observed_at_utc'],'protocol_id':result['protocol_id'],
        'code_commit':'2a86e0cf4c6dac53c267390e57235d3ad6b87a80','output_sha256':digest,
        'trials':[{'family':t['family'],'holding_months':t['holding_months'],'summary':t['summary']} for t in result['trials']],
        'minimum_cumulative_configurations':20,'minimum_cumulative_return_evaluations':25,'proof_trials':0,
        'measurement_revision_not_independent_evidence':True,'changed_cells':len(result['changed_returns']),
        'previously_scored_cells_changed':sum(x['old_return'] is not None for x in result['changed_returns']),
        'features_and_selections_preserved':result['features']==first['features']}
ledger=REPO/'docs/research/2026-09-07-value-observations.jsonl'
if any(json.loads(line)['protocol_id']==record['protocol_id'] for line in ledger.read_text(encoding='utf-8').splitlines()):
    raise ValueError('Observation already recorded')
with ledger.open('a',encoding='utf-8') as stream:stream.write(json.dumps(record,ensure_ascii=False)+'\n')

gaps={}
for trial in result['trials']:
    for period in trial['periods']:
        for m in period['members']:
            if m['price_return'] is not None:continue
            key=m['ticker'],period['entry'],period['exit']
            row=gaps.setdefault(key,{'ticker':m['ticker'],'isin':m['isin'],'entry':period['entry'],'exit':period['exit'],
                                    'quality_reasons':m['quality_reasons'],'selected_in':[]})
            if m['selected']:row['selected_in'].append(trial['family']+'-'+str(trial['holding_months']))
(ROOT/'outputs/H18_H19_LACUNAS_RESTANTES.json').write_text(json.dumps(list(gaps.values()),ensure_ascii=False,indent=2),encoding='utf-8')

positive=['Probability edge exists','Potential net economic value','Data advantage','Executability','Capacity','Speed to falsify']
negative=['Overfitting risk','Research cost','Data cost','Operational complexity','Time to deployable evidence']
options=[('Completar evidência da H19', [2,2,1,2,4,2], [4,3,1,3,4], 'Prioridade relativa de informação; não passou o gate e não autoriza promoção. IC e spread condicional positivos nas duas metades, porém o cenário adverso falha.'),
         ('Aprofundar H18 sem informação nova',[1,2,1,2,4,2],[4,3,1,3,4],'Baixa prioridade: IC negativo em 2018–2021, estabilidade inferior à H19.'),
         ('Reabrir H11 dividendos legado',[1,2,1,2,4,1],[4,4,2,4,4],'Custo maior para corrigir datas, equivalência ON/PN e histórico de caixa; o número positivo antigo não é confiável.'),
         ('Adicionar ML aos mesmos dados',[1,2,0,1,4,1],[5,4,1,4,5],'Não justificado: nenhuma vantagem informacional nova e risco adaptativo maior.')]
decision={'created_at_utc':datetime.now(timezone.utc).isoformat(),'phase':'DISCOVERY','economic_state':'NO_PRIORITY_UPGRADE_IN_REGISTERED_SCREENS',
          'capital_scenarios_brl':[5000,10000],'capital_authorization':False,'expenses_authorization':False,
          'candidate_closest_to_further_investigation':'H19','hypothesis_promoted_to_proof':None,
          'search_budget':record['minimum_cumulative_return_evaluations'],'count_is_minimum_not_complete_search_denominator':True,
          'priority_scores_are_subjective_not_probabilities':True,'options':[],
          'expected_value_of_research':'A evidência nova tem maior valor se resolve eventos de saída/fusão que dominam a incerteza. Repetir parâmetros sobre os mesmos preços não produz validação independente. Com R$5–10 mil, recorrência de custo operacional precisa ser baixa; lucro anual mínimo e horas de manutenção não foram confirmados.',
          'stopping_rule_applied':'As quatro configurações e uma correção de medição foram encerradas sem aprovação econômica. Sem nova variante, novo modelo, papel real ou Proof gerado para escapar deste resultado.',
          'next_five_concrete_actions_if_research_is_resumed':[
              'Resolver com termos primários todos os 35 intervalos restantes, incluindo ativos fora da seleção; conservar caixa, trocas e direitos, sem substituir ticker automaticamente.',
              'Auditar a cobertura de dividendos/JCP e eventos completos dos emissores necessários antes de estimar retorno total.',
              'Registrar um experimento novo se corrigir também a elegibilidade/fatores históricos; a revisão atual mantém as seleções originais.',
              'Só após fonte suficiente, simular quantidades/caixa em R$5 mil e R$10 mil, custos e uma alternativa de caixa, com execução após o sinal.',
              'Exigir evidência futura separada e custos realizáveis antes de qualquer GO; interromper se o benefício plausível não compensa a manutenção.']}
for name,pos,neg,reason in options:
    decision['options'].append({'line':name,'positive':dict(zip(positive,pos)),'negative':dict(zip(negative,neg)),
                                'heuristic_score':sum(pos)-sum(neg),'rationale':reason})
for dest in (ROOT/'outputs/DECISAO_PESQUISA_STOCKS.json',REPO/'docs/research/2026-09-07-value-decision.json'):
    dest.write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')

lines=['# H18 e H19 executadas — resultado de pesquisa', '',
       'H18 (lucro/preço) e H19 (patrimônio/preço) foram executadas nas versões mensal e trimestral. '
       'As quatro configurações receberam **NO_PRIORITY_UPGRADE**. H19 apresentou a evidência exploratória mais consistente, '
       'mas nenhuma passou o critério econômico e de estabilidade registrado. **Não há lucro líquido demonstrado nem GO para investir.**', '',
       'O orçamento informado de R$5–10 mil foi usado como contexto econômico. Estes diagnósticos não simulam uma conta com esse capital.', '',
       '## O que foi medido', '',
       '96 sinais mensais, de janeiro de 2018 a dezembro de 2025. Há 93 meses elegíveis e 31 trimestres elegíveis. '
       'O universo usa vínculos históricos CVM/FCA, no máximo 60 emissores por data, com uma única classe ON e mediana de liquidez diária de pelo menos R$1 milhão. '
       'A mediana final é 39 empresas com fator por data; seleciona-se o quinto de maior múltiplo invertido.', '',
       'Foram obtidos 745 dos 750 capitais originais necessários; cinco documentos permanecem ausentes/inválidos. '
       'Os balanços oferecem 748 lucros anuais atribuíveis ao controlador e 750 patrimônios líquidos excluindo não controladores. '
       'A capitalização usada é uma aproximação observável: ações declaradas menos tesouraria, traduzidas por eventos de unidade e multiplicadas pelo preço. '
       'Ela mantém a defasagem do balanço e não é a capitalização exata em cada data. Documentos só entram depois da divulgação.', '',
       '## Resultado após as correções', '',
       '“Spread” é a diferença entre a média de retorno por preço das selecionadas e a média do universo elegível. '
       'A coluna de períodos completos exclui períodos com qualquer retorno não medido, portanto sofre seleção por disponibilidade futura. '
       'Os valores trimestrais foram divididos por três para comparação aritmética; não são rentabilidade mensal executável.', '',
       '| Configuração | Períodos completos / elegíveis | Spread em períodos completos, p.p./mês | IC disponível médio | Cenário adverso + custo de 72 bps, p.p./mês |',
       '|---|---:|---:|---:|---:|']
for trial in result['trials']:
    x=trial['summary']['overall'];label=trial['family']+' '+('mensal' if trial['holding_months']==1 else 'trimestral')
    lines.append(f"| {label} | {x['complete_periods']}/{x['eligible_periods']} | {100*x['complete_case_spread_per_month']:+.3f} | {x['available_case_mean_ic']:+.4f} | {100*x['adverse_spread_after_72bp_per_month']:+.3f} |")
lines += ['', 'No cenário adverso, cada retorno ausente vale −100% quando o papel está selecionado e +100% quando está fora da seleção; '
          'o mesmo retorno atribuído entra na estratégia e no benchmark. É um cenário severo, **não um limite matemático**. '
          'São deduzidos 36 ou 72 pontos-base por período de manutenção como obstáculos econômicos, sem alegar custo executável calibrado. '
          'O benchmark recebe custo incremental zero nessa comparação.', '',
          'O gate exigia IC positivo e spread adverso positivo em ambas as metades fixadas, 2018–2021 e 2022–2025, '
          'além de média adversa após 72 bps de pelo menos 0,42% ao mês equivalente. '
          'O patamar é uma referência de pesquisa próxima de R$500/ano sobre R$10 mil; não é projeção de lucro nem preferência já confirmada pelo usuário.', '',
          'H18 tem IC negativo na primeira metade nas duas frequências. H19 tem IC positivo nas duas metades, mas falha nos cenários adversos. '
          'O spread condicional favorável de H19 não permite descartar viés de dados ausentes, risco de empresas em dificuldade ou diferenças setoriais.', '',
          '## Correções que alteraram a medição', '',
          '- O extrato antigo tinha 387.101 cotações e filtrava classificações BDI. O novo contém 391.824, com 4.723 adicionais e zero preços anteriores alterados. '
          'Americanas continuou negociando após 19/01/2023 sob BDI 08. Sua perda entre as aberturas de 02/01 e 01/02/2023, **−79,20%**, agora é medida. '
          'A classificação e os campos constam do [layout oficial COTAHIST da B3](https://www.b3.com.br/data/files/33/67/B9/50/D84057102C784E47AC094EA8/SeriesHistoricas_Layout.pdf).',
          '- Natura em 18/09/2019 e Porto Seguro em 21/10/2021: uma bonificação de 100% registrada pela B3 era aplicada novamente como split legado. '
          'O documento primário passou a contar uma vez; o registro antigo permanece na trilha de auditoria.',
          '- Qualicorp, Hering, Americanas, Petz e Hapvida tiveram movimentos superiores a 30% confirmados nas linhas originais da B3. '
          'Foram mantidos com alerta explícito, incluindo as perdas. Demais saltos sem revisão continuam faltantes.',
          '- As quatro seleções, fatores, datas e critérios foram preservados. Foram recuperadas 28 células antes sem retorno; nenhum retorno anteriormente medido mudou.', '',
          'A primeira rodada está preservada. O diagnóstico corrigido mantém **17 retornos sem medição no mensal e 18 no trimestral**, por família, '
          'correspondendo a 35 intervalos distintos. Fusões, mudanças de instrumento, subscrições e cisões ainda exigem termos próprios. '
          'A elegibilidade original também permanece congelada, inclusive exclusões provocadas pelo filtro de qualidade antigo. '
          'Isto é correção da medição de uma seleção já observada, não validação de uma estratégia completamente reconstruída.', '',
          '## Estado da pesquisa', '',
          'H1–H16 foram revisadas quanto à confiabilidade; H3 não foi executada e há 15 trials legados. Os vereditos NOT_SUPPORTED foram preservados. '
          'As falhas de datas, pesos, benchmark e fontes tornam sua evidência desigual, sem justificar promover automaticamente resultados antigos positivos. '
          'H17 já foi observada e continua inconclusiva; os problemas adicionais encontrados no painel de eventos também limitam a leitura daquele diagnóstico, que não foi rerodado nesta etapa.', '',
          'H18 e H19 deixaram de ser hipóteses nunca vistas. O mínimo acumulado é **20 configurações e 25 avaliações de retorno**, '
          'incluindo as revisões. O total adaptativo histórico é desconhecido. As revisões não são evidência independente; não há holdout histórico intacto e nenhuma Proof foi consumida.', '',
          'A regra de parada desta rodada foi aplicada. H18 perde prioridade. H19 é uma pista para investigação de fontes e retorno total, '
          'sem promoção por ter um gráfico ou spread favorável. O ganho de informação seguinte depende de resolver os eventos restantes para todos os ativos afetados, '
          'e depois incorporar dividendos/JCP, caixa, quantidades, custos, impostos pertinentes e uma alternativa de caixa. '
          'Variar parâmetros ou adicionar ML aos mesmos dados não resolve esses pontos.', '',
          '## Código e reprodução', '',
          'A última versão de código foi validada com **515 testes aprovados em 140,09 segundos**, cobertura de testes de 81%, '
          'Ruff no escopo do CI, Pyright no escopo configurado, construção da wheel e importação fora do checkout. '
          'Os testes incluem documentos reais da CVM e linhas originais da B3. A cobertura não é certificação científica.', '',
          'Código testado: `2a86e0cf4c6dac53c267390e57235d3ad6b87a80`. '
          'Protocolo inicial: `b6a2cc4ba4cbe8fb2d614427ad4d26a3193c7943bbba4e4c9449982ff72a1dde`. '
          'Protocolo de correção: `1f4ad50cd682f4611f16676f64cf56de1c37a5eeab9704b8f7257fc816c1ab0f`.', '',
          'O pacote `STOCKS_H18_H19_TESTADOS.zip` inclui código, dados, documentos de capital, extratos de contas e cotações primárias, '
          'protocolos e ambas as observações. `RODAR_PESQUISA_STOCKS.py` confere os hashes, extrai em `work/` e reproduz as duas versões offline, '
          'sem instalação, venv ou ordens. O resultado da verificação fica em `H18_H19_REPRODUCAO_VERIFICADA.json`.', '',
          'Os bancos operacional e de fontes testadas foram preservados. Não houve operação financeira, gasto com dados ou alteração do Core.', '']
text='\n'.join(lines)
(ROOT/'outputs/H18_H19_RESULTADO_TESTADO.md').write_text(text,encoding='utf-8')
(REPO/'docs/research/2026-09-07-value-results.md').write_text(text,encoding='utf-8')
print('recorded',digest,'remaining unique intervals',len(gaps))
