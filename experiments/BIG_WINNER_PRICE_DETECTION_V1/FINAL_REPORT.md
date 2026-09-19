# BIG_WINNER_PRICE_DETECTION_V1 — relatório final

> **Algum mecanismo histórico do Stocks Predictor colocava futuras ações de +30% no radar antes da alta?**

Resposta curta: nenhum mecanismo satisfez integralmente os critérios pré-congelados para `PRICE_DETECTION_SIGNAL_PRESENT`. `MOMENTUM_12_1`, `MOMENTUM_6_1` e `REVERSAL_21` produziram sinais fracos, mas não robustos em conjunto a dependência temporal, Holm, limites de identificação parcial e cauda confirmatória. Os outros quatro mecanismos apresentaram `NO_EVIDENCE_OF_PRICE_DETECTION`.

## Resultado por mecanismo

| Detector | Veredito | Precision | Base | Lift | Lift outer bounds | p bruto | p Holm | IC temporal da diferença | Episódios detectados/scorable |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MOMENTUM_12_1 | WEAK_PRICE_DETECTION_SIGNAL | 22,97% | 20,47% | 1,122x | 0,543–2,351 | 0,0028 | 0,0196 | -0,0332–0,0876 | 52/223 (51 early) |
| MOMENTUM_6_1 | WEAK_PRICE_DETECTION_SIGNAL | 22,32% | 20,47% | 1,090x | 0,550–2,174 | 0,0225 | 0,1125 | -0,0195–0,0671 | 75/223 (72 early) |
| REVERSAL_21 | WEAK_PRICE_DETECTION_SIGNAL | 22,83% | 20,47% | 1,115x | 0,590–2,025 | 0,0171 | 0,1026 | 0,0035–0,0428 | 123/223 (122 early) |
| 52W_HIGH | NO_EVIDENCE_OF_PRICE_DETECTION | 17,14% | 20,47% | 0,837x | 0,421–1,951 | 0,9984 | 1,0000 | -0,0723–0,0071 | 43/223 (38 early) |
| LOW_VOL_252 | NO_EVIDENCE_OF_PRICE_DETECTION | 11,71% | 20,47% | 0,572x | 0,319–1,262 | 1,0000 | 1,0000 | -0,1204––0,0525 | 42/223 (42 early) |
| MOMENTUM_LOW_VOL | NO_EVIDENCE_OF_PRICE_DETECTION | 12,66% | 19,10% | 0,662x | 0,289–2,038 | 1,0000 | 1,0000 | -0,1044––0,0206 | 20/102 (19 early) |
| VOLUME_SURGE | NO_EVIDENCE_OF_PRICE_DETECTION | 20,19% | 20,47% | 0,986x | 0,488–2,146 | 0,6131 | 1,0000 | -0,0240–0,0202 | 82/223 (80 early) |

`MOMENTUM_12_1` sobreviveu a Holm no teste aleatório, e sua cauda de 24 meses foi positiva, mas o IC95% temporal completo atravessou zero e os limites parciais admitiram lift abaixo de 1. `MOMENTUM_6_1` não sobreviveu a Holm. `REVERSAL_21` teve IC temporal positivo, mas não sobreviveu a Holm e reverteu para diferença ligeiramente negativa na cauda confirmatória. Por isso nenhum dos três foi promovido além de sinal fraco.

## Cobertura e incerteza

Os seis mecanismos com população nativa completa tiveram 6.180 ticker-asofs scorables e 84,89% de outcomes conhecidos. `MOMENTUM_LOW_VOL`, por seu gate histórico, teve 2.472 observações scorables e 81,31% de cobertura. Unknown não foi contado como false. Os 2.184 saltos corporativos abertos afetaram apenas horizontes correspondentes e produziram os limites conservadores exibidos acima.

Foram construídos 278 episódios de vencedoras; 55 tinham fronteira incerta por unknown e foram excluídos do endpoint confirmatório de episódios. Recall elevado isolado não foi interpretado como evidência: `REVERSAL_21`, por exemplo, detectou 123/223 episódios, mas sua vantagem cross-sectional não sobreviveu ao conjunto de gates.

## Integridade e controles

- 43.260 rankings foram gerados sem outcomes e congelados em 103 asofs mensais, de 2017-01-31 a 2025-07-31.
- O manifest e o CSV congelado foram validados antes da geração de labels.
- Execução é next-open; horizonte é 12 meses corridos; preço terminal aceita no máximo cinco sessões de staleness.
- O índice exclui dividendos/JCP e ajusta somente continuidade de quantidade evidenciada.
- Matched random usa 10.000 simulações na mesma população mensal scorable; bootstrap usa 10.000 amostras em blocos de 12 cross-sections mensais; família confirmatória usa Holm FWER 5%.
- O controle positivo de leakage passou para todos os detectores; o controle negativo preservou o tamanho mensal da seleção.
- A comparação em população scorable comum está em `metrics/cross_sectional/common_scorable_population.json`; não foi definido `BEST_FACTOR`.

## Relação com a V1 anterior

```text
BIG_WINNER_DETECTION_V1
Question: total-return winner detection
Result: INCONCLUSIVE_DATA_QUALITY

BIG_WINNER_PRICE_DETECTION_V1
Question: price-appreciation winner detection
Result: no confirmed mechanism; three weak signals and four no-evidence results
```

Os verdicts não são intercambiáveis. Este experimento não estima dividendos, JCP, custos, impostos, PnL, alpha ou rentabilidade futura.

## Reprodutibilidade

Source/freeze commit: `57bfc5aaa932d2ec2e34ffae7e0c77ed0759ddb8`; branch: `experiment/BIG_WINNER_PRICE_DETECTION_V1`; dataset SHA-256: `a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4`; signal CSV SHA-256: `2ba1821bacfda0370c140f3557a6fc087c4452792b32a98935c1b5b4537c1f15`. O commit final local é registrado pelo Git após a validação final; não houve push, merge ou alteração da instalação principal.

**Conclusão:** no escopo de valorização de preço, os mecanismos históricos avaliados não puderam demonstrar capacidade point-in-time de enriquecer seus rankings com futuras grandes vencedoras acima do que seria esperado por seleção equivalente ao acaso. Este resultado diz respeito exclusivamente à detecção histórica de preço e não demonstra retorno econômico total, lucro futuro ou prontidão para capital real.
