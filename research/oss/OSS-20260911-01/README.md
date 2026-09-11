# Kit experimental OSS-20260911-01

Cinco capacidades stdlib isoladas; nenhuma operação financeira ou integração de produção.

Leia o [relatório de encerramento](../../../docs/open_source_research/OSS-20260911-01/closure/REPORT.md) e o [deep dive](../../../docs/open_source_research/OSS-20260911-01/closure/SOURCE_REVIEW.md).

Execute `python -I -B -X utf8 tool.py ranking ranking-example.json novo-recibo.json` neste diretório. Saída existente é recusada. As outras operações aceitam argumentos JSON das funções em capabilities.py. Timestamp inteiro é contrato dos fixtures; adaptar e testar datas reais antes de uso empírico.

Benchmark/contract_check usam o checkout canônico C:/STOCKS/stocks-predictor para comparar funções atuais. Para reexecutar, copie o kit para diretório novo, conserve recibos originais e confira hashes. Não usar o runner para sobrescrever evidência congelada.
