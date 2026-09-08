"""Record tested software, actual evidence failure and limits of the verdict."""
from datetime import datetime,timezone
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];repo=root/'work/stocks-predictor'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
receipt=read(root/'outputs/H19_EXECUCAO_CONTINUA_REPRODUCAO.json')
audit=read(root/'outputs/H19_EXECUCAO_CONTINUA_AUDITORIA.json')
tests=(root/'work/h19-continuous-tests.log').read_text(encoding='utf-8')
assert '572 passed in 177.43s' in tests
assert not audit['full_history_executed'] and audit['profit'] is None
decision={'action':'INTEGRATE_AND_VALIDATE_FROZEN_H19_CONTINUOUS_REPLAY',
 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'software_status':'TESTED_GUARDED_REPLAY_IMPLEMENTED',
 'economic_status':'INCONCLUSIVE_DATA_QUALITY',
 'operation_status':'NO_GO_UNVALIDATED_NET_PROFIT',
 'full_history_executed':False,'net_profit_brl':None,
 'source_commit_tested':receipt['source_commit'],
 'full_suite':{'passed':572,'elapsed_seconds':177.43,'coverage_percent':79},
 'targeted_and_external_bundle_tests':33,
 'ruff_ci_scope':'PASS','pyright_configured_rj_scope':'PASS','wheel_and_external_import':'PASS',
 'independent_reproduction':receipt,
 'observation_budget':{'minimum_configurations':32,'minimum_historical_return_evaluations':37,
                       'new_configurations':0,'new_historical_return_evaluations':0},
 'config_or_selection_changed':False,
 'remaining_evidence':{'unreviewed_payment_dates_excluding_normalized_installments':356,
     'dated_events_without_reviewed_net':33,'complete_cash_intervals_uncertified':1237,
     'corporate_records_not_fully_integrated':36,'successor_cash_uncertified':True,
     'post_2019_jbs_events_not_fully_integrated':11},
 'stop_decision':'Do not operate or reveal a partial profit. The frozen protocol stops when source repair cannot cheaply establish an executable comparison.',
 'not_claimed':['no edge exists','full historical simulation completed','economic validation passed'],
 'reopening_requirements':['Source-complete cash inventory for both frozen portfolios including successors and PN shares',
     'Reviewed cash dates, final net amounts and actual fiscal basis/auction treatment',
     'Integrated whole-share corporate delivery paths with causal revisions and code-level tax treatment when needed',
     'Only after those gates: four registered paired historical evaluations, net benchmark and risk analysis'],
 'database_integrity':{'operational_sha256':'a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4',
     'isolated_sha256':'a8238568980d3303890b04590cfb5c55ab2d24c9271edd86820269336b09679a','unchanged':True},
 'orders_or_paid_resources_used':False}
out=root/'outputs/H19_EXECUCAO_CONTINUA_DECISAO.json'
out.write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')
report=f'''# H19 — validação técnica e resultado econômico

**O programa de execução contínua foi implementado e testado. A simulação histórica real não foi concluída: os dados ainda falham nos requisitos de evidência. Não há lucro líquido validado para operar com R$5 mil ou R$10 mil.**

O resultado econômico é `INCONCLUSIVE_DATA_QUALITY`; a decisão operacional é `NO_GO_UNVALIDATED_NET_PROFIT`. Isso não prova ausência de oportunidade. Significa que os resultados disponíveis não sustentam o uso de capital real. O relatório anterior baseado em preços não deve ser apresentado como lucro líquido executável.

## O que ficou pronto

O programa mantém a mesma carteira e o mesmo caixa entre rebalanceamentos. Negocia apenas as diferenças de quantidade, utiliza preços de abertura do mercado padrão e fracionário, respeita liquidações e conserva direitos a proventos mesmo após vender a ação. A apuração mensal reserva IRRF e DARF, inclusive valores acumulados abaixo de R$10, sem tratar crédito tributário como dinheiro recebido.

Ações ainda não entregues são controladas separadamente. Negociação anterior ao crédito exige autorização documentada e entrega até a liquidação da venda. Valores de direitos conhecidos apenas depois não entram antecipadamente na marcação patrimonial. A última liquidação e as obrigações fiscais são verificadas antes de aceitar um resultado.

O comando único executa a verificação de evidências e, quando ela passar, as duas carteiras nos quatro casos congelados. A integração real já foi chamada e devolveu código **2**, indicando dados incompletos. Ela não devolveu lucro zero nem um resultado parcial.

| Verificação | Resultado |
|---|---|
| Suíte completa do projeto | **572 testes passaram**, 177,43 s |
| Testes do recorte de execução, inclusive fora do repositório | **33 passaram** |
| Cobertura geral | 79%; contabilidade contínua 76%; driver 85% |
| Ruff, Pyright no escopo RJ configurado, wheel e importação externa | Passaram |
| Reprodução do pacote em pasta nova | Duas saídas idênticas, ambas com código 2 |
| Arquivos verificados por SHA256 | {receipt['payload_files_verified']} |
| Cópias de fontes primárias incluídas | {receipt['source_files_copied']}; nenhuma referência selecionada sem cópia |

Os testes utilizam cenários controlados. Seus lucros conhecidos verificam contas e não constituem evidência de rentabilidade da H19. Pyright segue o escopo limitado já adotado pelo projeto; não é uma aprovação estática de todo o novo código.

## Dados conferidos e pendências

Foram conferidos 95 meses do calendário DARF 6015 nas agendas da Receita. As cotações cobrem 76.301 dias de posições do universo anteriormente mapeado, sem lacunas. A conferência posterior identificou RENT4 e CYRE4; foram acrescentadas 125 cotações no mercado padrão e 125 no fracionário, também sem lacunas nos intervalos adicionais. A integração dos eventos que entregam esses ativos continua pendente.

Os 1.345 boletins B3 examinados integralmente forneceram 31.601 linhas de crédito. A fila original tem 778 eventos: 420 pagamentos individuais revisados, mais duas linhas substituídas por parcelas explícitas. As 133 linhas da seleção têm datas cobertas, mas **356 datas da comparação ainda não foram validadas**. Há 389 valores líquidos teóricos com regra documentada para o cenário PF; outros 33 eventos já datados ainda exigem revisão do líquido. Os demais também carecem de datas.

A aplicação da regra histórica de dividendos e JCP se limita às distribuições ordinárias com pagamento confirmado antes de 2026. Não se estendeu automaticamente essa regra a atualizações monetárias, frações, resgates ou pagamentos de 2026. A base legal é a [Lei 9.249/1995, arts. 9 e 10](https://www.planalto.gov.br/ccivil_03/leis/l9249.htm), respeitadas as alterações de vigência.

O inventário integral de caixa dos **1.237 intervalos** ainda não está certificado. Também faltam a integração fiscal e operacional de **36 registros societários**, o caixa ordinário dos sucessores e a incorporação completa dos 11 eventos posteriores de JBS já localizados. As contagens do JSON são requisitos e campos pendentes; não representam milhares de falhas de software independentes.

## Achados que impedem aceitar o teste antigo

- **Light:** o grupamento 100:1 seguido de desdobramento 1:100 arredonda a posição para centenas. O fator de preço líquido igual a 1 não significa posição inalterada. As sobras são alienadas em leilão.
- **Telefônica:** a sequência 40:1 e 1:80 também separa sobras. O aviso distingue resultado de leilão líquido de custos do eventual imposto pessoal sobre o ganho.
- **Localiza e Cyrela:** as bonificações entregam ações preferenciais RENT4/CYRE4. Elas não podem ser avaliadas como quantidades extras de RENT3/CYRE3. Localiza ainda divulgou uma razão operacional posterior diferente da descrição resumida de 1 por 26, exigindo tratamento causal.

As oito revisões documentais parciais estão em `H19_EVENTOS_SOCIETARIOS_CONFERIDOS.json`, com documento, página, hash e trechos verificados. Elas não foram convertidas artificialmente em aprovação fiscal completa.

## Decisão e uso do pacote

O trabalho técnico não elimina as lacunas econômicas. Aplicou-se a regra já registrada de interromper a promoção da hipótese quando a reconstrução não estabelece, a custo razoável, uma comparação executável. H19 continua inconclusiva. Não foram observados novos retornos: a contagem permanece em pelo menos 32 configurações e 37 avaliações anteriores.

Para reabrir a avaliação, é necessário completar as evidências enumeradas no pacote e integrar os tratamentos fiscais dependentes da posição. Só então cabem os quatro testes históricos, a comparação líquida com alternativas e a avaliação de risco. Não há ação de investimento indicada ao usuário nem necessidade de ele executar comandos para confirmar o resultado desta rodada: a reprodução já foi feita.

O pacote `STOCKS_H19_EXECUCAO_CONTINUA_AUDITADA.zip` contém programa, entradas, fontes e testes. O arquivo `LEIA-ME.md` explica o comando e os códigos de saída. O recibo `H19_EXECUCAO_CONTINUA_REPRODUCAO.json` registra a reprodução.

Commit de código validado: `{receipt['source_commit']}`. SHA256 do ZIP: `{receipt['zip_sha256']}`. Os dois bancos usados anteriormente mantêm seus hashes. Nenhuma ordem foi enviada e nenhum recurso pago foi contratado.
'''
path=root/'outputs/H19_EXECUCAO_CONTINUA_RESULTADO.md';path.write_text(report,encoding='utf-8')
docs=repo/'docs/research';(docs/'2026-09-07-h19-continuous-results.md').write_text(report,encoding='utf-8')
(docs/'2026-09-07-h19-continuous-decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf-8')
handoff=repo/'HANDOFF.md';text=handoff.read_text(encoding='utf-8')
text=text.replace('33 testes direcionados passaram; Ruff do escopo CI passou. Suíte completa,\nwheel e reprodução externa ainda serão verificadas nesta mesma rodada.',
 f'Validação concluída do commit {receipt["source_commit"]}: 572 testes passaram\nem 177,43 s; cobertura geral 79%, módulo contínuo 76%, driver 85%. Ruff CI,\nPyright no escopo RJ, wheel e importação externa passaram. Recorte do pacote:\n33 testes passaram fora do repositório. Duas reproduções reais idênticas,\nambas exit 2 por evidência incompleta; {receipt["payload_files_verified"]} payloads e {receipt["source_files_copied"]} fontes verificados.\nZIP SHA256 {receipt["zip_sha256"]}.')
text=text.replace('mais 125 cotações ON/PN\nprincipais e 125 fracionárias','mais 125 cotações PN no mercado\npadrão e 125 fracionárias')
handoff.write_text(text,encoding='utf-8')
print(json.dumps({'report':str(path),'decision':decision['economic_status'],'profit':None,'tests':572}))
