# Matriz e ranking mestre de capacidades

Unidade do backlog = capacidade. A ordem operacional usa dependências e valor da informação; não soma popularidade. Eficácia financeira externa é NOT_DIRECTLY_COMPARABLE até casar universo, datas, dados, risco e custos. NO_VERIFIED_ADVANTAGE: nenhuma superioridade econômica nossa ou externa foi comprovada. As garantias locais que merecem KEEP são versões explícitas, histórico preservado, separação legacy/atual e gates de evidência.

| ID | Capacidade | Estado interno/C | Referências | Ação/estado | Dependência decisiva |
|---|---|---|---|---|---|
| K01 | [Identidade histórica CNPJ/ISIN/classe](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/universe.py#L28) | PARCIAL / C1 | R53, R52, R22 | IMPROVE / CANDIDATE | Mapa documental por data e transições societárias |
| K02 | [Versões e disponibilidade de fundamentos](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/document_panel.py#L21) | PARCIAL / C2 | R51, R60, R22, R23 | IMPROVE / CANDIDATE | Competência, recebimento, publicação, ingestão e versão |
| K03 | [Eventos e recebíveis reconciliados](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/simulation.py#L89) | PARCIAL / C3 | R54, R05, R02 | AUGMENT / BLOCKED_DATA | Valores líquidos, datas e termos societários faltantes |
| K04 | [Contrato de calendário e observação](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/universe.py#L43) | PARCIAL / C1 | R18, R19, R54 | VALIDATE / CANDIDATE | Calendário oficial por período e versão |
| K05 | [Validação de treino e labels por data](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/simulation.py#L326) | PARCIAL / C2 | R11, R01, R57, R58 | ADD / CANDIDATE | Painel sintético e intervalos de label; antes de ML econômico |
| K06 | [Inferência temporal e multiplicidade](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/economic_gate.py#L32) | PARCIAL / C1 | R09, R57, R58 | AUGMENT / CANDIDATE | Séries por data, família e denominador auditável |
| K07 | [Diagnóstico de ranking e atrito](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/portfolio.py#L76) | PARCIAL / C1 | R16, R01, R56 | AUGMENT / CANDIDATE | Labels completos e universos registrados; teste sintético primeiro |
| K08 | [Teste diferencial de contabilidade](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/simulation.py#L89) | IMPLEMENTADO / C3 | R02, R03, R05 | VALIDATE / CANDIDATE | Contrato comum e engine externo em Linux permitido |
| K09 | [Covariância e risco de cauda](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/portfolio.py#L12) | DESCONHECIDO / C0 | R07, R08, R17 | RESEARCH / CANDIDATE | Retornos admissíveis e convenções de cauda; solver não instalado |
| K10 | [Fatores brasileiros como controle](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/factor.py#L33) | DESCONHECIDO / C0 | R56, R10, R59 | RESEARCH / CANDIDATE | Fatores datados e retorno líquido comparável |
| K11 | [Ranking relativo versus forecast](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/docs/DESIGN.md#L1) | APENAS_DOCUMENTADO / C0 | R12, R13, R14, R11, R01 | RESEARCH / BLOCKED_DATA | K01 K02 K03 K05 K07; protocolo materialmente novo |
| K12 | [Value/quality/ranking com baixo giro](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/factor.py#L428) | EXPERIMENTAL / C1 | R16, R56, R59 | RESEARCH / BLOCKED_PERMISSION | Linhagem H7–H19; seis campos e revisão humana para reabertura |
| K13 | [Regimes causais para sizing](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/factor.py#L58) | DESCONHECIDO / C0 | R32, R33, R10 | RESEARCH / DEFER | K05, parâmetros causais; sem estados suavizados como sinal |
| K14 | [Macro com vintages](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/STOCKS_CURRENT_STATE.md#L1) | PARCIAL / C0 | R55, R20, R21 | AUGMENT / BLOCKED_DATA | Vintages e relógios por série; wrapper não preenche lacuna |
| K15 | [Incerteza preditiva e calibração](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/temporal_evidence.py#L29) | DESCONHECIDO / C0 | R35, R29, R27 | RESEARCH / DEFER | Modelo baseline e hipótese de dependência explícita |
| K16 | [RF/ExtraTrees/boosting baselines](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/pyproject.toml#L10) | DESCONHECIDO / C0 | R11, R12, R13, R14 | RESEARCH / DEFER | K05, painel elegível e orçamento igual de tuning |
| K17 | [ARIMA/VAR/Kalman e baselines temporais](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/pyproject.toml#L10) | DESCONHECIDO / C0 | R10, R27, R29, R30 | RESEARCH / DEFER | Target de retorno/risco, não erro de preço como prova econômica |
| K18 | [Redes temporais e Transformers](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/pyproject.toml#L10) | DESCONHECIDO / C0 | R28, R29, R31 | RESEARCH / DEFER | Custo computacional e ganho incremental não medidos |
| K19 | [RL e notícias/LLMs](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/analyst.py#L1) | DESCONHECIDO / C0 | R44, R45, R46 | RESEARCH / DEFER | Pesos, notícias, timestamps, licenças e custos; não executar bots |
| K20 | [Registro e contratos de dados](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/operational_store.py#L26) | IMPLEMENTADO / C1 | R40, R41, R42, R39, R38 | KEEP / CANDIDATE | Evitar novo serviço de tracking que duplique ledgers |
| K21 | [Viabilidade por capital e custos](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/research_profile.py#L7) | PARCIAL / C1 | R02, R54, R55 | IMPROVE / BLOCKED_DATA | Custos, tributação aplicável, prazo, perdas e esforço pessoal |
| K22 | [Relações, neutralização e features](https://github.com/leonardosovienski/stocks-predictor/blob/80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5/stocks_predictor/factor.py#L1) | DESCONHECIDO / C0 | R10, R11, R16, R34 | RESEARCH / DEFER | Ajuste somente no treino e histórico setorial; múltiplas hipóteses |

## Scores: intervalo, não falsa precisão

Notas de valor: 0 sem benefício demonstrável, 3 benefício material plausível, 5 alto benefício sustentado no escopo. Custos/riscos: 0 baixo demonstrado, 5 alto. Intervalos são julgamento pré-experimento e não benefício medido. Justificativas, pesos e notas individuais estão em registry.json. As avaliações semelhantes dos habilitadores refletem evidência insuficiente para separá-los numericamente.

VALUE_ENABLER = .30 ciência + .20 validação + .15 evidência externa + .10 encaixe + .10 incremento + .10 domínio + .05 referências independentes. COST_RISK = .25 complexidade + .20 risco metodológico + .15 dependências + .15 manutenção + .15 dados + .10 operação. Ambos multiplicados por 20; PRIORITY = .70 VALUE + .30 (100−COST_RISK). Não houve N/A nem renormalização nos scores calculados.

| ID | VALUE_SCORE | COST_RISK_SCORE | PRIORITY_SCORE | Confiança |
|---|---:|---:|---:|---|
| K01 | 55.0–91.0 | 22.0–76.0 | 45.7–87.1 | LOW |
| K02 | 55.0–91.0 | 22.0–76.0 | 45.7–87.1 | LOW |
| K03 | 55.0–91.0 | 22.0–76.0 | 45.7–87.1 | LOW |
| K04 | 55.0–91.0 | 20.0–60.0 | 50.5–87.7 | LOW |
| K05 | 55.0–91.0 | 20.0–60.0 | 50.5–87.7 | LOW |
| K06 | 55.0–91.0 | 20.0–60.0 | 50.5–87.7 | LOW |
| K07 | 55.0–91.0 | 20.0–60.0 | 50.5–87.7 | LOW |
| K08 | 53.0–89.0 | 23.0–63.0 | 48.2–85.4 | LOW |
| K09 | 55.0–91.0 | 23.0–63.0 | 49.6–86.8 | LOW |
| K21 | 52.0–88.0 | 22.0–76.0 | 43.6–85.0 | LOW |

Sensibilidade calculada com peso do valor .60/.70/.80 e extremos das notas. Intervalos amplamente sobrepostos: **não há vencedor numérico robusto**. K01–K03 têm alto valor potencial e custo de dados desconhecido [0,5]; K04/K05/K08 permitem testes sintéticos menores. A fila econômica K11–K13/K16/K18/K19/K22 permanece SEM NÚMERO: economic_value, external_evidence pertinente e custo ainda UNKNOWN. Fórmula econômica do mandato preservada em registry.json. Popularidade e novidade não preenchem essas lacunas.

COMPETITOR_PREVALENCE, COMPETITIVE_GAP e DIFFERENTIATION_POTENTIAL = UNKNOWN: não há denominador de concorrentes comparáveis. Rubrica para rodada futura: 0 nenhuma presença/lacuna/diferenciação demonstrada; 3 presença material/lacuna pertinente/capacidade distinta; 5 generalização na amostra definida/lacuna crítica/diferenciação validada no escopo. Não chamar nossos controles de LEAPFROG. REDUNDANCY_PENALTY K20=4 para novo serviço que duplicaria ledgers; demais=0 após agrupar alternativas por problema, sem bônus no score.

## Vistas por categoria

| Vista | Ordem provisória de IDs | Razão |
|---|---|---|
| Melhorias imediatas | K05 → K04 → K08 | Testes mecânicos sem ampliar hipótese econômica |
| Fontes/datasets | K01 → K02 → K03 → K14 | Identidade, versão e eventos habilitam comparação |
| Novas análises | K07 → K10 → K22 | Diagnóstico antes de sinal complexo |
| Filtros/ranking | K01 → K07 → K11 | Admissibilidade separada de hipótese de alpha |
| Ferramentas | K08 → K06 → K20 | Verificação independente parcial sem duplicar infraestrutura |
| Features/estratégias | K11 → K12 → K13 → K16 → K18 | Condicional a dados e protocolo; não autorização de treino |
| Validação | K05 → K06 → K15 | Cronologia, multiplicidade e incerteza |
| Risco/execução | K03 → K21 → K09 | Eventos, fricções e risco em base de capital coerente |
| Referências | R51/R53, R11/R01, R02/R05, R09, R16 | Problemas específicos; não ranking de qualidade global |
| Composições | C01 → C02 → C03 | Dependências descritas abaixo |

Filtros de dados: invalidez/identidade/quarentena (K01–K04). Filtros de sinal: quantis/thresholds (K07/K11/K12), hipóteses econômicas. Filtros de risco: concentração, giro, liquidez e capacidade (K09/K21). Filtros científicos: cronologia, exposição ao teste, inferência (K05/K06). Não otimizar filtro de invalidez por retorno histórico.

## Composições e ablações

- C01 = K01+K02+K03+K07+K11: identidade/PIT/eventos + ranking. Ganho esperado: distinguir sinal de erro de dado. Ablar cada correção em diagnóstico permitido, preservando universo de interseção e efeito de cobertura. Alto custo de fonte; sem desempenho medido.
- C02 = K04+K05+K06+K08: calendário + labels + incerteza + replay. Ganho esperado: rejeitar conclusões temporal ou contabilmente inválidas. Controle sem cada proteção deve falhar nos casos plantados. Prioridade habilitadora.
- C03 = K07+K09+K10+K21: ranking + risco + fatores + custos. Ganho esperado: separar seleção, alocação e prêmio de risco. Comparar pesos iguais e remover neutralização/covariância/custo isoladamente. Não somar evidências das peças como prova da combinação.

Black-Litterman, HRP/risk parity, minimum variance, volatility targeting e VaR/ES/CVaR entram em K09. ROE/ROIC, margem, dívida/caixa, P/L/P/VPA/EV/EBITDA, investment, crescimento, accruals e dividendos entram no contrato K02/K12; disponibilidade de uma conta não certifica todos os múltiplos. Notícias/dados alternativos têm K19 e permanecem sem fonte PIT verificada.
