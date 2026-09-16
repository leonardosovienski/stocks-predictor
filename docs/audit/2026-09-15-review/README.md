# Auditoria documental e correções — 15/09/2026

O código consumidor CAIN recebeu correções de leitura e seleção de evidências.
Esta revisão Stocks registra o alcance e as pendências científicas, sem mudar
dados, protocolos, ledgers ou conclusões congeladas. Publicação autorizada pelo
usuário; nenhuma exclusão local, operação financeira ou instalação principal.
Adequação pessoal foi explicitamente excluída desta etapa.

## Identidade e evidência

Produtor examinado: `leonardosovienski/stocks-predictor`, commit
`3066321e599ee15dd0ace4167d2791545ce6eb95`. Consumidor de partida:
`leonardosovienski/cain`, `24f784c5dde1fa66c262ad5899f4fd8d02526adf`.
Essas leituras não formam um snapshot atômico dos ambientes.

A [entrega A–F inicial](AUDITORIA_INICIAL.md) e seu
[ledger derivado histórico](initial-derived-ledger.json) preservam o inventário
de hipóteses, observações, 75 entradas R7, 22 claims e 24 frentes. As permissões,
contagens de testes e limitações daquela primeira etapa são datadas; esta
continuação não reescreve seus valores nativos.

O [manifesto](source-manifest.json) contém 794 identidades verificadas na extração:
662 PDFs (30.352 páginas), 74 HTML, 55 JSON, dois ZIPs e um XLSX. Corrige a
afirmação anterior de 794 extrações textuais: os três contêineres foram decodificados
indevidamente pelo primeiro script auxiliar. A inspeção de seus índices e CRC
não é leitura dos documentos referenciados. A tentativa anterior foi preservada.

Foram lidos os textos completos dos 23 PDFs diretamente ligados às pendências
de caixa, com conferência visual focal em MOVI, SLCE e CXSE. Foram revistos os
textos visíveis de três páginas RI (BBSE, COPASA, TIM), o esquema e os campos de
eventos de seis JSON B3 e o catálogo de um ZIP CVM. São 33 referências diretas
examinadas em graus diferentes; não há atestado de leitura semântica integral
dos 794 arquivos, nem verificação visual integral dos PDFs.

Corpos primários, bancos e recibos extensos continuam locais em
`C:/STOCKS/work/remaining-evidence-20260915` e nas pastas de origem.
O manifesto publica identidades e limites, sem reenviar os corpos dos documentos.

## Resultado científico preservado

- H17 tem duas revisões observadas e permanece `INCONCLUSIVE_DATA_QUALITY`.
  São pelo menos 16 candidatos nominais e 17 avaliações históricas, sem denominador
  adaptativo completo. Isso não equivale a 17 famílias independentes.
- H18/H19 receberam validação Discovery, sem promoção; H19 contínua permanece
  bloqueada por evidências faltantes. Código de saída depende do comando, não é
  veredito econômico universal.
- H20 não demonstra vantagem incremental líquida; 1.248 intervalos não certificados.
- H21 histórica é condicional; a janela prospectiva não pode ser antecipada.
  H22 conserva sua rejeição e os denominadores originais.
- Testes de software, citações e hashes não comprovam lucro ou operação real.

## Caixa e eventos: decisão após leitura

Permanecem 50 valores líquidos sem certificação, incluindo 22 datas de pagamento
desconhecidas, além dos 28 registros societários pendentes da revisão R7.
Os campos originais não foram preenchidos com zero, prazo-limite ou alíquota presumida.

| Fonte ou caso | Constatação e consequência |
|---|---|
| MOVI, aviso de 30/07/2026 | Subscrição com crédito de JCP exige opção; crédito das novas ações depende de homologação. Página 10 chama 12/09/2026 de dia útil, embora seja sábado. Divergência confirmada visualmente e mantida como conflito. |
| SLCE 2019 | Valor do emissor usa unidade após desdobramento; B3 conserva outro nominal. Não substituir sem reconciliar quantidade e arredondamento. |
| CXSE 2024/2026 e BBSE 2026 | Nominal e atualização Selic são distintos. Total atualizado não comprova líquido. |
| VIVT e BBSE: redução de capital | Pagamento e nominal documentados não resolvem a base histórica de cada posição. |
| VBBR março/2026 | Duas versões dão setembro/2026 e setembro/2027. Preservar a cadeia já registrada; não transformar versão antiga em crédito realizado. |
| ABEV | Avisos distinguem parcelas JCP 2025 e novas declarações 2026. Há valores líquidos declarados/arredondados, mas a coerência de precisão/base da primeira parcela permanece sem reconciliação; terceira parcela ainda futura no corte. |
| SMFT | Uso de crédito JCP em subscrição é opcional; sobras exigem moeda e homologação condiciona direitos. Não implementar reinvestimento automático. |
| PSSA e RADL, boletins B3 | Crédito e valor estão documentados; coluna de aprovação não basta para reconciliar todas as identidades. Não prova líquido pessoal. |
| COPASA RI | Valores históricos anteriores ao desdobramento foram divididos por três na tabela. Não importar a tabela como unidades originais. |
| TIM RI | Tabela contém cabeçalho ambíguo por ação/lote e uma data histórica de pagamento anterior à aprovação. A linha de 2025 confirma data já registrada; não valida toda a série histórica. |
| JSON B3 | Campos de aprovação, posição anterior ao ex e valor não incluem pagamento nem líquido. Ausência desses campos impede usar o endpoint como prova de crédito. |
| ZIP CVM | Catálogo contém links e metadados de entrega, não o conteúdo dos documentos ou prova de pagamento. |

Consultas adicionais aos avisos oficiais RADL2020 e RECV2023 localizaram prazos
máximos, não comprovação de dia exato de crédito. A auditoria não converte esses
prazos em datas efetivas. Nenhuma comunicação a emissor/corretora foi enviada.

## Correções de engenharia e aceite

No CAIN, o preparador preserva JSONL por objeto e JSON de documento inteiro;
listas simples também conservam seus valores literais e repetições.
Identidade e revisão acompanham métricas. A seleção preserva contexto histórico
ou omite a afirmação quando o contexto não cabe. Uma pergunta específica não
recebe trechos adicionais com apenas uma palavra genérica em comum quando
há correspondências mais específicas. Não foram codificados vereditos Stocks.
Consultas com caminho explícito podem limitar a seleção ao documento e suas
revisões; a consulta genérica de H19 ainda apresentou limitação de recuperação.
Consultas que nomeiam vários campos técnicos recebem valores literais e abstenção
expressa de interpretação. Isso evita a conclusão livre incorreta observada sobre
reprodução, mas não equivale a certificar o raciocínio geral do modelo.

O histórico de tentativas, testes finais e respostas reais está registrado no
repositório CAIN, em `docs/STOCKS_REMEDIATION_20260915.md`. A validação semântica
é limitada aos casos exercitados; o manifesto de fontes não a substitui.

## Próxima evidência necessária

As lacunas remanescentes exigem documentos de pagamento/retificação, reconciliação
das unidades e cadeias societárias, ou observação do período prospectivo.
Isso constitui trabalho científico/documental ainda aberto, não um bug de software
que possa ser encerrado declarando aprovação. Nenhum gate foi enfraquecido.
