# H19 — validação técnica e resultado econômico

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
| Arquivos verificados por SHA256 | 418 |
| Cópias de fontes primárias incluídas | 367; nenhuma referência selecionada sem cópia |

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

Commit de código validado: `d6740817e1e0433bbcb9fdcbfe11ab128914ec56`. SHA256 do ZIP: `e6144a954ff55b12ef067b8459dfb59482ebf75f0c426e79642c261f448931b0`. Os dois bancos usados anteriormente mantêm seus hashes. Nenhuma ordem foi enviada e nenhum recurso pago foi contratado.
