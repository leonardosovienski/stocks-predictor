# Stocks: preço, rentabilidade e redução de trocas

**Implementado e executado em pesquisa.** A nova hipótese H20 combina preço baixo com rentabilidade dos acionistas e oferece tolerâncias para evitar trocas e pequenos ajustes. Os resultados abaixo medem seleção e viabilidade de compra; o lucro líquido histórico continua desconhecido.

O código está no checkout independente:
`C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907\work\stocks-predictor`, branch `fix/stocks-cvm-execution-20260907`.

**O que funciona agora**

- `stocks_predictor.value_profitability`: confere documento, versão, data disponível, período anual e fontes; calcula valor e rentabilidade; ordena as ações e explica a seleção.
- `stocks_predictor.buffered_rebalance`: congela quantidades com preços do sinal e a posição completa da carteira; delega as operações simuladas ao `RetailBook`, com quantidades inteiras, fracionário, base fiscal, caixa e liquidação.
- `stocks_predictor.h20_research`: comando para reproduzir a análise de fundamentos, a sequência de nomes planejados e compras iniciais com fontes locais verificadas.
- `stocks_predictor.entry_feasibility`: centraliza a simulação de compras e a revisão de unidades societárias que já existiam. A H19 conserva a mesma lógica e os mesmos resultados.

**Regras registradas antes da primeira medição**

Valor é patrimônio dos acionistas dividido pela aproximação de capitalização já disponível no projeto. Rentabilidade é lucro anual atribuível aos acionistas dividido pelo patrimônio deles no encerramento do exercício. É uma aproximação de ROE com patrimônio final; não usa patrimônio médio nem rentabilidade operacional.

O universo comum exige os dois indicadores disponíveis e patrimônio positivo. Lucro negativo continua na amostra e recebe sua posição no ranking. Valores ausentes não viram zero. A combinação usa média dos ranks, com pesos iguais e desempate por ticker, sem pesos treinados. Há três alternativas:

| Alternativa | Seleção | Tolerância |
|---|---|---|
| Preço baixo — controle | Melhores 20% por valor, no mesmo universo comum | Sem tolerância adicional |
| Preço + rentabilidade | Melhores 20% pela média dos ranks | Sem tolerância adicional |
| Preço + rentabilidade com tolerância | Mesmo score e número de posições | Posições existentes podem permanecer até o corte de 30% do ranking; ajustes de posições mantidas de até 2,5% do capital são dispensados |

Uma posição ausente ou inelegível não recebe proteção da tolerância. Saídas totais, liquidação final e novas posições não são suprimidas. Os limites de 30% e 2,5% são escolhas fixas de implementação, sem calibração por retorno; não representam uma estimativa de que a troca pagará todos os seus custos e impostos.

**Resultados executados**

Foram avaliadas as 32 datas trimestrais de março de 2018 a dezembro de 2025: 1.897 células de origem, das quais 1.234 atenderam aos critérios. Houve cobertura suficiente em 31 datas. Em março de 2018, apenas 17 nomes ficaram elegíveis, abaixo do mínimo registrado de 20; essa data permaneceu explicitamente bloqueada.

| Alternativa | Datas elegíveis | Substituições de nomes nas 30 transições comparáveis |
|---|---:|---:|
| Preço baixo — controle comum | 31 | 90 |
| Preço + rentabilidade | 31 | 96 |
| Preço + rentabilidade com tolerância | 31 | 70 |

A tolerância reduziu as substituições planejadas de 96 para 70, ou **27,1%**. São mudanças de nomes numa sequência de carteiras pretendidas, não operações de uma carteira contínua. Não se pode converter esse percentual diretamente em redução de giro financeiro, impostos ou aumento de lucro. A entrada de rentabilidade, isoladamente, aumentou as substituições de 90 para 96 nesse diagnóstico; isso foi mantido no resultado.

Foram concluídas **372 de 384 compras iniciais simuladas**, com capitais de R$5 mil e R$10 mil e custos por lado de 0,18% e 0,36%. Os 12 casos bloqueados são as três alternativas, dois capitais e dois custos na data com cobertura insuficiente. Cada compra começa com caixa integral; por isso a tolerância e a alternativa sem tolerância têm a mesma seleção de entrada. Retenção exige uma posição anterior real.

A primeira observação concluiu 364 casos. O adendo de fontes vinculou a revisão da bonificação da Cyrela já conferida anteriormente: as unidades ON originais permaneceram iguais, sem conceder bonificação a quem compra na data-ex. A segunda observação concluiu mais oito casos, sem mudar ranking, parâmetros ou datas. Ambas foram preservadas.

Em um teste sintético pareado, a carteira tinha 510 ações A e 490 B, ambas a R$10, além de R$20 em caixa. O alvo sem tolerância exigia vender dez A e comprar dez B: R$200 negociados e R$0,36 de custo modelado. Com tolerância, manteve as posições e evitou essas duas operações. A diferença de exposição permaneceu visível. Isso valida a mecânica, não a conveniência econômica futura de manter essas ações.

**Validação e preservação**

- **639 testes passaram** na suíte completa, em 131,70 segundos, sobre o runtime `9ecf5eb`.
- **92 testes passaram fora do checkout**, usando o código da wheel extraída localmente. Não houve instalação do Core ou novas dependências.
- Ruff passou; Pyright passou nos quatro módulos novos.
- A wheel reproduziu a segunda observação H20 byte a byte: SHA256 `13acee7062dddbf96c81356588f36806e758ea9e5c6c8f395e7891620b1f6a8f`.
- O replay H19 permaneceu byte a byte igual; o diagnóstico H19 anterior permaneceu estruturalmente igual após a centralização do código.
- Foram verificados 11 arquivos brutos contábeis, 31 entradas do manifesto de execução e 365.198 registros de cotação. Isso não certifica cobertura integral de proventos ou execução real.

Na preparação dos testes externos, foram corrigidos os caminhos do próprio ambiente de teste para acomodar imports legados e imports entre testes. Não houve correção de runtime após a suíte completa. A primeira comparação bruta do replay H19 também precisou usar as mesmas quebras de linha Windows do arquivo anterior; o conteúdo JSON já era igual. Os logs preservam essas etapas.

**Como usar**

Para reproduzir o pacote extraído, use o Python 3.13 global e um diretório de saída novo:

```powershell
py -3.13 .\REPRODUZIR_H20.py --research-root 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907' --output 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907\work\h20-reproducao-nova'
```

O pacote contém wheel, código novo, protocolos, observações e testes. A reprodução reutiliza as fontes extensas da raiz preservada, confere seus hashes e grava em uma saída nova. Não baixa dados, abre bancos ou envia ordens. O comando completo do diagnóstico está em `EXECUTAR_H20.ps1` no pacote e na documentação da pesquisa.

Na API de simulação, a sequência é `prepare_snapshot` → `rank_snapshot` → `select_members` → `freeze_rebalance` → `execute_rebalance`. A seleção recebe os ticker/ISIN realmente mantidos no livro. Só se cria o plano quando `selection_available` é verdadeiro. O executor exige uma revisão explícita das unidades no intervalo entre sinal e execução e rejeita alterações na carteira desde o sinal, incluindo base fiscal e reservas. Essa confirmação mecânica não substitui a auditoria das fontes.

**Limite econômico que permanece**

Os fundamentos são aproximações com atraso, não há neutralização setorial e o histórico compartilhado já foi observado. A H20 ainda precisa de inventário de caixa e eventos para seus próprios períodos de retenção; os documentos da H19 não certificam automaticamente esse novo caminho. Não foi calculado retorno, lucro contínuo ou vantagem ajustada a risco.

Há agora pelo menos **35 configurações registradas** e continuam **37 avaliações históricas de retorno**. As três novas alternativas foram avaliadas em sinais e execução inicial, sem nova avaliação de retorno ou holdout intacto. A H19 permanece congelada. O estado financeiro continua **INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO**.
