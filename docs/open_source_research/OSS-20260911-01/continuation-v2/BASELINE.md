# Baseline — complemento verificável v2

Mesma iniciativa e SHA `80e69daa7d83b3b0f0e3384c53207ee0a9afd5b5`. A [fotografia inicial](../BASELINE.md) permanece preservada. Este complemento corrige incertezas anteriores por evidência nova, sem alterar a história.

## CI e Core

O [CI234](https://github.com/leonardosovienski/stocks-predictor/actions/runs/34534223498) mostra Success no SHA atual, dois jobs de qualidade e secrets. Logs inspecionados: 897 testes ativos, 17 arquivados e63 subtests por Python3.13/3.14; wheel Core3.2.0 oficial e módulo carregado em `/tmp/stocks-wheel/.../site-packages`. É execução prévia do CI consultada agora, não suíte rodada por nós neste Windows. Recibos/linhas em [ci-evidence.json](ci-evidence.json). Avisos de Node/cache existem e não falharam os jobs. Código verde não certifica lucro.

## Bancos e alcance de leitura

12/12 objetos do catálogo foram abertos apenas para sqlite_master, em URI mode=ro&immutable=1 com query_only. SHA completo antes/depois igual ao catálogo em todos; nenhum sidecar não vazio; nenhum SELECT de preços, decisões, resultados ou holdout. [Recibo reproduzível](bank-receipt.json). A limitação anterior NOT_ACCESSED foi resolvida apenas para identidade física/esquema. Contagens e datas continuam atribuídas ao catálogo datado, não recontadas nem convertidas em completude econômica.

Esquemas mostram coexistência de preços isolados e bancos de pesquisa: fundamentals legacy com known_at opcional versus fundamentals_pit com versão/received/available/hash; dividends legacy identifica ex_date como proxy de pagamento, enquanto cash_events separa ex/payment. Essa diferença de contrato confirma que bancos não são intercambiáveis. O CHECK available_at>received_at prova uma convenção de armazenamento, não horário público observado.

## Cobertura atual

| Objeto | Estado verificado | Limite |
|---|---|---|
| Parser, universo, painel, ingestão versionada, simulador | Código e testes selecionados | Não auditoria de cada linha do repositório |
| Painel PIT | 12/12 controles novos; C3/E5 ENGINEERING | Não cobre universo real inteiro |
| Capital CVM |3/3 documentos originais e hashes | Capital não autoriza valuation por classe |
| Simulador |8/8 controles da primeira parte | Sem confronto engine externo |
| Inferência iid |1000 séries sintéticas comparadas a oráculo analítico | Calibração nominal não aprovada; ver experimentos |
| Pacote instalado/Core |CI atual consultado | Ambiente local auxiliar é3.12.14; runtime real3.13/3.14 |
|12 bancos |Hash/esquema read-only |Resultados e dados de mercado não abertos |
|H1–H22, ledgers e H21 prospectivo |Protocolos/estados documentais preservados |Nenhum avaliador congelado ou janela futura consultado |

WSL não instalado; Docker não encontrado; nenhum host Linux de benchmark identificado. Workflow do projeto depende de push/PR e não tem workflow_dispatch. O mandato proíbe commit/push nesta rodada e AGENTS proíbe venv/instalação neste Windows. É bloqueio preciso dos benchmarks externos, não falta de um pacote a instalar silenciosamente.

Fontes15 ainda apontam50 valores líquidos, 22 datas de pagamento e 28 eventos societários pendentes, com sobreposição. Fonte14 antiga tinha52/24/28: são revisões diferentes. H22 continua rejeitada, H21 histórica condicional e prospectiva ainda sem maturação. Capital R$5.000 confirmado, custos e situação tributária não inferidos. Fluxo: fonte bruta/hash → versão/identidade disponível → filtros do universo → feature/ranking → pesos/sinal → execução posterior/caixa/eventos → avaliação/trials. Os gates de dado e tempo vêm antes da avaliação econômica.

## Complemento documental DOC03

Após os controles iniciais, baixamos o FCA2023 oficial (434.044 bytes), com hash no [manifesto](DOC03-manifest.json), ODbL declarada no catálogo. Antes da verificação foram fixados12 documentos: os primeiros quatro por competência/versão/ID dos três primeiros CNPJs com quatro documentos, em ordem lexicográfica; nenhuma escolha por preço/retorno. [12/12 verificações passaram](DOC03-receipt.json) para identidade/metadados e nenhum vínculo antes do corte convencional. Onze documentos não geraram ticker admissível; o último gerou VSPT3/VSPT4. Essa amostra é principalmente um controle de rejeição e NÃO demonstra cobertura de doze empresas negociáveis. O parser registrou504 issues no arquivo completo; não os apagamos nem os classificamos todos como defeitos da fonte. O ZIP fica em C:/STOCKS/work/oss-20260911-01/continuation-v2/fca2023.zip, fora do Git.

DOC03 avança X01 no contrato FCA, mas não completa o painel financeiro/identidade/eventos de X01. Três documentos de capital já reconciliados são outra amostra. Disponibilidade no dia seguinte é convenção conservadora; nenhum horário intradiário observado foi inventado. O [runner documental](documentary.py) separa aquisição/manifesto de --verify. O [runner Linux](linux_bootstrap_protocol.py) é código de protocolo para arch, não executado; requer ambiente permitido, versões e recibo imutável de dependências antes do G1 de execução. Foi verificada apenas sua sintaxe localmente.
