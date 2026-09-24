# Protocolo de avaliação v2 (`stocks_predictor/v2`) — 2026-09-24

O pacote é aditivo. Não altera os motores legados (`backtest.legacy_walk_forward`, `simulation.walk_forward`),
o circuito de pesquisa qualificado (`research_*`) nem os vereditos congelados. Serve a toda avaliação nova a
partir do Prompt 3a. Implementa só com a biblioteca padrão; única dependência externa: o contrato de trials do
`predictor-core` 3.2.1, já dependência do projeto.

## Contratos

| Módulo | Contrato |
|---|---|
| `dataset` | `PITDataset` no schema `stocks-pit-dataset/2`: calendário de pregões explícito; papéis com listagem e deslistagem (datas, instante em que ficaram conhecidas e valor de saída); identidade (ticker/emissor) por vigência; barras com preço **negociado, sem ajuste** e instante de disponibilidade (revisões permitidas); eventos societários (multiplicador de ações) e proventos com data ex e instante de anúncio; fundamentos por **data de divulgação**, com versão (reapresentação). Hash sha256 do JSON canônico. Validação fechada: calendário sem fim de semana nem pregão vazio, barra só em pregão, barra disponível só após o fechamento, nada depois do `data_cutoff`, fundamento nunca antes do fim do período, conflitos rejeitados. |
| `dataset.PITView` | O que se sabia antes da abertura do pregão de decisão (12:00 UTC = 09:00 BRT): barras de pregões anteriores, eventos e fundamentos com `available_at` até esse instante. O histórico ajustado usa só eventos já conhecidos com data ex anterior à decisão. Universo = listados conhecidos (deslistados entram enquanto negociaram). ADV conta pregão sem negócio como zero. |
| `execution` | `ExecutionConvention(lag_sessions >= 1, price in {open, close, worst})`. O sinal usa barras até o fechamento de D; a execução é em D+lag. `lag_sessions=0` (fechamento de D) levanta `ExecutionError`: não é representável. |
| `costs` | `CostModel` sem padrões escondidos: corretagem (bps + fixo por ordem), emolumentos, meio spread, slippage, impacto `bps × (N/ADV)^expoente`, aluguel anual dos vendidos. `LiquidityRule`: ADV mínimo na decisão, janela, estatística e participação máxima por ordem. |
| `engine` | Carteira por quantidades e caixa. Eventos na data ex: ações × multiplicador, proventos (vendido paga). A deslistagem sai pelo valor de saída ou pelo último fechamento, com custo. Vendas antes de compras, participação limitada ao ADV da decisão, compras limitadas ao caixa, sem alavancagem. Sem barra no pregão, a ordem não é executada e fica registrada. Métricas **líquidas**; `evaluate` roda a mesma estratégia com custo zero só para decompor. Sharpe com rf = 0 (o excesso sobre CDI/Selic entra no Prompt 3b). Resultado com digest sha256. |
| `baselines` | EW do universo PIT na mesma frequência e com os mesmos custos. Buy-and-hold do fundo de índice. Momentum 12-1 (quintil superior, EW). Carteiras aleatórias com semente e o mesmo número de posições. Previsores de passeio aleatório e ingênuo contra o retorno realizado desde o preço de execução. |
| `walkforward` | `train_end + horizonte + embargo < test_start`, testes contíguos sem sobreposição. O ajuste recebe só a visão do fim do treino. O teste roda num backtest contínuo em que cada decisão usa o modelo da divisão do pregão de execução. |
| `manifest` | `RunManifest`: run_id, commit Git + sujeira, versão do pacote, config + hash, dataset (hash, versão, corte), universo e corte, intervalo, semente, modelo, custos, execução, validação, versão do motor e da política (e, desde o 3b, `decision_policy` com versão, status e sha256 do arquivo de política). `TrialLedger`: JSONL só de acréscimo (`O_APPEND` + `fsync`), cadeia de hashes verificada ao abrir. Ciclo `STARTED` → `COMPLETED`/`FAILED`. `STARTED` sem desfecho, de processo morto, vira `ABANDONED`. Registros `DECISION` só sobre execuções concluídas. Todo `STARTED` é um trial. Cada desfecho leva a linha `trial-registry/2.0.0` validada por `predictor_core.contracts.trial_v2.require_trial_v2`. |

### Validação estatística (Prompt 3b)

| Módulo | Contrato |
|---|---|
| `riskfree` | `RiskFreeSeries` (`stocks-riskfree/1`): série versionada com hash, unidades da SGS do BCB (`percent_per_day` para SGS 11/12, `percent_per_year_252` para SGS 1178/4389). Pregão sem taxa levanta `RiskFreeError`; nunca vira zero. Retorno em excesso = `r_s − rf_s`. |
| `metrics` | Sobre o retorno líquido em excesso: Sharpe anualizado, PSR (fórmula e série do core), sensibilidade do DSR na grade de N (E[max SR] do core, pior caso), t, beta/alpha MQO contra o índice, drawdown, turnover e custos do motor. Referências no docstring. |
| `factor_metrics` | IC (Pearson), Rank IC (Spearman com postos médios), ICIR, t, decaimento por horizonte, retornos por quantil (long-short e long-only) por período de rebalanceamento. Rótulo desde o preço de execução; cada horizonte só usa sinais cujo rótulo termina dentro da janela. Bruto de custos (diagnóstico do sinal). |
| `cpcv` | CPCV de López de Prado com purge pelo intervalo **real** do rótulo de cada amostra (`t0` = decisão, `t1 = t0 + lag + h`), embargo após cada bloco de teste e verificação de vazamento em toda divisão. φ = C(N − 1, k − 1) caminhos. `derive_purge_embargo`: purge = lag + h; embargo = (primeira defasagem com \|ρ\| < z/√n − 1) × passo de rebalanceamento. |
| `pbo` | PBO por CSCV (Bailey, Borwein, López de Prado & Zhu, 2017), implementação local. λ ≤ 0 conta como overfitting. |
| `policy` | Política de decisão versionada em [policy/stocks-evaluation-policy-v1.json](../../../policy/stocks-evaluation-policy-v1.json); limiares só no arquivo. `NO_DECISION` sem baseline, sem rf admitida, com dataset sintético, amostra curta ou DSR/PBO não estimáveis. `REJECT` se algum gate falhar; `PASS` se todos passarem. Toda decisão carrega versão, status e sha256. Status atual: `PROPOSED_PENDING_OWNER_APPROVAL`. |
| `validation` | Orquestra, sob o ledger: baselines exigidos pela política; família pré-declarada, com o candidato dentro; relatórios em excesso de rf; cross-section; CPCV do procedimento "melhor configuração no treino, aplicada no teste"; DSR; PBO; decisão registrada. |

O skfolio (BSD-3, 1.3.1) não foi adotado: o `CombinatorialPurgedCV` dele purga um número fixo de observações,
não o intervalo real de cada rótulo, e traria numpy, scipy, pandas, cvxpy, scikit-learn e plotly. O pypbo
(AGPL) e o mlfinlab (proprietário) também não são usados.

## Uso

```bash
python -m stocks_predictor.v2 --config docs/engineering/2026-09-24-protocol-v2/synthetic-demo-config.json \
  --dataset synthetic --ledger /caminho/novo/ledger.jsonl --output /caminho/novo/resumo.json
```

`--dataset` aceita um arquivo `stocks-pit-dataset/2`. `synthetic` usa `v2/synthetic.py`, que é demonstração e
teste e **nunca evidência empírica**. A configuração precisa ter todos os campos. `--output` nunca sobrescreve.

```bash
python -m stocks_predictor.v2.validation \
  --config docs/engineering/2026-09-24-protocol-v2/synthetic-demo-config.json \
  --validation docs/engineering/2026-09-24-protocol-v2/synthetic-validation-spec.json \
  --dataset synthetic --riskfree synthetic --policy policy/stocks-evaluation-policy-v1.json \
  --ledger /caminho/novo/ledger.jsonl --output /caminho/novo/validacao.json
```

`--riskfree` aceita um arquivo `stocks-riskfree/1`. `synthetic` usa a série sintética `SYNTHETIC-RF`, que a
política recusa. A [especificação sintética](synthetic-validation-spec.json) declara o candidato e a família
antes de qualquer resultado.

A [config sintética](synthetic-demo-config.json) usa o custo congelado da H1: emolumentos de 3 bps e 15 bps de
spread + slippage por lado. A divisão 7,5/7,5 é nominal; o que vale é o total.

## Testes

`tests/test_v2_dataset.py`, `tests/test_v2_engine.py`, `tests/test_v2_manifest.py`. Os cinco obrigatórios:

- PIT: fundamento divulgado em D nunca aparece antes de D; varredura em todos os pregões.
- Execução: nenhum negócio usa o fechamento que gerou o sinal; varredura em três convenções.
- Sobrevivência: deslistados no universo enquanto negociaram.
- Custos: resultado líquido monotonicamente não crescente com custos ×{0; 0,5; 1; 2; 4; 8}, nas quatro carteiras de baseline.
- Reprodutibilidade: mesma config, mesmo hash e mesma semente dão o mesmo resultado; o dataset é reconstruído do zero.

## Dívida técnica registrada

1. O core 3.2.1 não tem RunManifest nem ledger com ciclo de vida. Este pacote tem a versão mínima local, com
   ponte validada para `trial-registry/2.0.0`. Candidata a subir para o core.
2. Não existe construtor de dataset PIT real. O banco atual não guarda quando cada evento ficou conhecido:
   `adjustments` não tem instante de anúncio e `prices_raw` é por ticker.
   - O `stocks-pit-panel/1` do circuito qualificado (`research_pit.Panel`) segue as mesmas regras de instante: decisão às
     12:00 UTC, barra só depois das 20:00 UTC, listagem e deslistagem só quando conhecidas, revisões. Também tem
     identidade por CNPJ. Mas não tem preço de abertura, eventos societários nem fundamentos. Convertê-lo exigiria
     inventar esses dados, então não há adaptador.
   - O dataset real precisa ser montado no PC 1 com: abertura e fechamento do COTAHIST; eventos societários
     versionados, com data de anúncio; fundamentos do `cvm_pit`, com `DT_RECEB` e versões.
   - Nada foi baixado.
3. A carteira aleatória iguala número de posições e frequência, não o turnover (DESIGN §8 pede os dois).
4. Lote padrão e fracionário, tributação e margem de vendidos não são modelados. A participação é medida contra
   o ADV da decisão, não contra o volume do próprio pregão.
5. Sem `delisting_value`, a saída é pelo último fechamento: otimista em falências. O dataset deve informar o
   valor de saída quando ele for conhecido.
6. O core 3.2.1 não tem arquivo de política de decisão. A política é local, versionada e com hash, e os limiares
   da v1 estão **propostos, pendentes de aprovação do dono**.
7. Não há série de taxa livre de risco real versionada no PC 2. A Selic SGS 11 usada na H21 só tem o manifesto de
   fonte no Git (sha256 `82d23198…`). A avaliação real (3c e 4) precisa dessa série; sem cópia local, parar e
   perguntar antes de baixar.
8. O t de Harvey, Liu & Zhu e o t do IC supõem independência entre períodos. Com h maior que o passo de
   rebalanceamento, são otimistas; a autocorrelação entra só no embargo do CPCV.
