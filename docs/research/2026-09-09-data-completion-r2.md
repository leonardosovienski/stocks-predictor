# Dados e fontes — recuperação e complemento R2, 09/09/2026

Os bancos e as fontes necessárias à continuidade estão disponíveis em `C:\STOCKS`.
A prontidão econômica integral continua **parcial**: recuperação e integridade
não resolvem automaticamente eventos, despesas e execução. O estado legível por
programa é [data-readiness.json](2026-09-09-data-readiness.json), também disponível
em `C:\STOCKS\data\CATALOG.json`. Não há aprovação para operar capital.

## O que foi resolvido

| Frente | Antes desta rodada | Agora |
|---|---|---|
| Bancos da migração | Preservados apenas no ZIP | 37 caminhos originais mapeados a 12 bancos únicos, recuperados e íntegros |
| Fontes 13 e 14 | Pacotes não disponíveis para leitura local | Fontes materializadas; auditoria 13 reproduzida exatamente e complemento 14 conferido |
| Demonstrações BOVA11 | Grandes lacunas documentais | Tabelas anuais de evolução patrimonial cobrem 2018 a março de 2026, incluindo comparativos |
| Avisos do ETF | Acesso parcial e falhas do FNET | 39 registros identificados: 35 corpos FNET, 3 equivalentes oficiais e 1 corpo indisponível |
| Tarifas históricas B3 | Apenas condições atuais delimitadas | Circular 177/2020 recuperada, com vigência a partir de 02/02/2021 e limites históricos explícitos |
| Retomada | Caminhos de bancos ainda apontavam ao arquivo | Catálogo atual, comandos de recuperação e auditoria, mapas e documentação alinhados |

As 2.159 cotações BOVA11 até 08/09/2026 já verificadas na
[rodada R1](2026-09-09-h21-source-closure.md) continuam com o mesmo hash.
Não foi calculado nenhum retorno novo. H21 original termina em 01/04/2026;
suas quatro especificações e oito valorizações não foram reemitidas.

## Bancos e proveniência

O arquivo `C:\STOCKS\DADOS_STOCKS.zip` foi verificado por SHA-256:
`83d5aac8e23d72e4deb1331077e08313914375a5dbac4276e5f8ad89da586d23`.
A recuperação selecionou 1.392 objetos únicos e cópias independentes dos conjuntos
de evidência. O diretório final, incluindo a composição separada da revisão 14 e
o catálogo, contém 4.317.717.293 bytes. Não foi materializada a árvore inteira de
60.023 caminhos, que inclui muitas cópias dos mesmos dados.

Todos os 12 bancos passaram em `PRAGMA integrity_check`, sem violações de chaves
estrangeiras. Os seis WAL arquivados estavam vazios. A leitura usou
`mode=ro&immutable=1`, `query_only` e hashes antes/depois. O recuperador recusa
atestar leitura imutável quando encontra journal transacional não vazio, inclusive
com diferença de maiúsculas no nome. Não houve ingestão, migração ou ativação de banco.

O banco original `project/data/stocks.db` é identificado por
`a22739794ba4a43a11544338d4a91e14cb6a0b1f7b132ab460f96d3359f63cf4`.
Ele contém 1.149.872 linhas de cotações brutas, 1.784 códigos de instrumentos e
2.647 datas entre 04/01/2016 e 27/08/2026; esses códigos não são necessariamente
1.784 ações. Ajustes, fundamentos e 2.227 linhas de quarentena foram preservados.
Versões reparadas e de pesquisa continuam separadas; três bancos pequenos são
fixtures/smokes, identificados no catálogo. Não foi escolhida uma versão por retorno.
Datas de pagamentos futuros existentes nos bancos não significam caixa recebido.

Fontes 13 e 14:

- Revisão 13: manifesto `7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b`;
  resultado reproduzido semanticamente igual ao `expected-audit.json` original.
- Revisão 14: manifesto `3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda`;
  complemento em outro diretório, sem substituir a referência 13.
- A revisão 14 mantém 52 valores líquidos e 24 datas de pagamento ausentes,
  28 entradas societárias pendentes e 0 de 1.248 intervalos integralmente
  certificados. As contagens se sobrepõem. As duas correções de valores da revisão
  14 já existiam na migração; sua reprodução não é descoberta econômica nova.

H20 continua estacionada para reconstrução ampla. Esses números delimitam a
incompletude; não significam que todos os preços ou proventos estejam ausentes.

## Documentos BOVA11

A identidade conferida é CNPJ 10.406.511/0001-61, fundo B3 990, classe 19674.
O catálogo público FNET, filtrado por esse CNPJ, categoria 6 e tipo 30,
retornou oito demonstrações anuais de 2019 a 2026. Foram recuperados os PDFs
originais de 2019, 2020, 2021, 2022, 2023 e 2025. O original de 2026 e o de
2018 já estavam disponíveis na R1. O PDF isolado de 2024 permaneceu inacessível;
o comparativo de 2025 cobre sua evolução patrimonial, não todos os seus anexos.

As tabelas foram verificadas visualmente nos PDFs de
[2019, página 9](https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=50245&),
[2021, página 11](https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=179946&),
[2023, página 9](https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=471199&),
[2025, página 10](https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=915706&) e
[2026, página 9](https://www.blackrock.com/br/literature/annual-financial-statements/ishares-bova11-brl-demonstrativos-financeiros-2026-ptbr.pdf).
Originais, hashes, páginas e interpretação constam no
[inventário de eventos R2](2026-09-09-bova-event-review-r2.json).

Nas tabelas examinadas não há uma linha separada de amortização em dinheiro.
As políticas incorporam resultados do fundo ao patrimônio da cota; dividendos da
carteira não são automaticamente pagamentos adicionais ao cotista. Subscrições
e resgates no mercado primário não representam desdobramento de todas as cotas.
O demonstrativo de 2025, página 16, permite amortização trimestral em certas
condições, sem redução de cotas. Permissão contratual não comprova sua execução.
Essas evidências reduzem a lacuna documental até 31/03/2026, mas não constituem
um inventário contínuo de direitos, caixa e unidades para todo o intervalo.

Os 39 avisos não periódicos foram consultados por ano e por fundo/classe.
Três reuniões da proposta de incorporação examinada não se instalaram; não há
execução dessa proposta nos documentos examinados. O aviso cancelado 483971
contém CNPJ de outro fundo e foi rejeitado. O aviso 676102 também está cancelado.
O resumo da AGO de 2025, ID 941503, continua sem corpo recuperado. Os três PDFs
equivalentes de BNP/BlackRock não são apresentados como cópias byte a byte do FNET.

No FNET, buscas por CNPJ, entrega entre 01/01/2018 e 09/09/2026 e todos os tipos
retornaram zero registros nas categorias 4 e 14, avisos aos cotistas simples e
estruturados. É ausência nessas consultas específicas, não certificado de ausência
de eventos. A categoria de demonstrações do FNET não corresponde aos tipos do
endpoint B3 `GetStructuredReports`: este retornava vazio até para anos com PDF
confirmado. `exibirDocumento` recuperou diversos originais quando
`downloadDocumento` falhou. Timeout e lista vazia não foram tratados como dado zero.

## Custos e pendências que permanecem

A [Circular B3 177/2020](https://www.b3.com.br/data/files/68/50/2D/3E/99E4671059300467AC094EA8/OC%20177-2020%20PRE%20_Modelo_Intermediario_%28PT%29.pdf),
páginas 3–4, inclui ETFs de ações e documenta, para operações regulares de varejo,
0,0300% por lado no contínuo e 0,0320% no leilão, a partir de 02/02/2021.
A cópia consultada informa revogação remanescente em 05/10/2023. Ela não resolve
a tarifa da entrada H21 em 2018 nem todo o histórico de custódia.
As condições B3 de setembro de 2026 e as condições públicas XP/Rico da R1
continuam registradas, com seus respectivos períodos e bases de cobrança.

As [entradas operacionais R2](2026-09-09-operational-inputs-r2.json) conservam
`ready_for_full_net_backtest=false`. Restam:

- Reconciliação contínua de eventos/direitos BOVA11 após 31/03/2026 e evidência
  proporcional para afirmar ausência de caixa ou alterações de unidades.
- Tarifas aplicáveis à entrada histórica de 2018, condições efetivas de corretagem,
  bases, arredondamentos e eventuais despesas da conta.
- Canal e vínculo com assessor da XP; capital, horizonte e perda aceitável do usuário.
  XP permanece preferida. Rico é alternativa condicional, sem conta ou ordem aberta.
- Spread, deslizamento e preenchimentos efetivos: cotações diárias não demonstram
  execução de ordens. Nenhuma execução real foi autorizada ou realizada.
- As lacunas amplas de ações quantificadas na revisão 14; a atualização BOVA11
  até setembro não atualiza automaticamente o universo de ações após 27/08.

Dados pessoais não impedem recuperar documentos ou preparar cenários, mas não
autorizam preencher custos desconhecidos com zero. A próxima decisão depende de
fontes que conciliem os eventos restantes e das condições aplicáveis da conta.
Não há motivo novo nesta rodada para promover H20 ou alterar o veredito H21.

## Aquisição, validação e reprodução

O [protocolo R2](2026-09-09-data-completion-r2-protocol.json) foi registrado antes
das aquisições adicionais, após as seis consultas iniciais nele declaradas.
Foram concluídos 121 trabalhos de aquisição: 83 respostas retidas como downloads,
38 falhas, 16.252.830 bytes baixados e 221.421 bytes de tentativas parciais.
O [inventário completo R2](2026-09-09-source-inventory-r2.json) preserva resultados,
URLs e hashes. Downloads incluem metadados/HTML, não apenas documentos substantivos. Todos os
50 PDFs desta rodada foram analisados estruturalmente; documentos escaneados
exigiram leitura visual. Respostas e falhas permanecem no diário append-only.

A contagem de descoberta reconstruída registra 40 consultas/aberturas/buscas web
e 26–27 intervenções no navegador, com incerteza de uma chamada; permanece abaixo
do limite de 80. Não é medição de todas as requisições HTTP internas.
Foi usada uma normalização de eventos/custos e uma composição separada da fonte 14,
sem variantes econômicas. As rotas públicas pertinentes foram tentadas, incluindo
B3, FNET, BNP e BlackRock; a rodada de coleta está encerrada.

Nove regressões do recuperador passaram no Python auxiliar 3.12.14: integridade,
deduplicação, cópias independentes, fechamento de handles, journals, corrupção,
travessia de caminhos, destino existente e limite de bytes. A auditoria de fontes
real foi reproduzida nesse ambiente sem Core e sem calcular retorno. Isso não é
certificado do runtime de produção. A CI canônica Linux/Python 3.13/Core 3.2
deve passar no SHA revisado e no commit integrado; seus resultados exatos ficam
no recibo final, sem atribuir a testes locais uma execução de produção.

[Comandos de recuperação e auditoria](../../research/session-20260909/data_completion/README.md).
Evidências e normalizador: `C:\STOCKS\work\data-completion-r2-20260909`.
Recibo de integração, CI, hashes e contenção local:
`C:\STOCKS\outputs\ENTREGA_DADOS_FONTES_R2_20260909.json`.
ZIPs originais, bancos, H1–H21, resultados, ledgers e quarentenas foram preservados.
