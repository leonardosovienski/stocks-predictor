# Ampliação das fontes e correções de ingestão

O complemento foi executado na cópia isolada. O banco operacional, preços brutos,
ledger e hipóteses congeladas foram preservados. Não houve cálculo de desempenho
de H17–H19 nem autorização de operação com dinheiro real.

## O que foi concluído

- Aquisição gratuita de 33 arquivos oficiais CVM: DFP, FRE e FCA, de 2016 a 2026,
  com URL, instante da coleta e SHA-256 de cada arquivo.
- Reconstrução de **4.177 documentos DFP**, **4.824 observações FRE por percentual
  de circulação**, **7.450 registros de capital emitido declarado** e **4.336
  registros de valores mobiliários FCA**. As contagens são registros, não empresas.
- A ingestão FRE passou a rejeitar por documento as quantidades inválidas, sem
  abortar todos os emissores daquele ano. O lote auditado registrou 44 observações
  inválidas e 2.581 sem total derivável. Zero não vira quantidade de ações válida.
- O capital emitido é separado do autorizado, subscrito e integralizado. Em BBAS,
  o documento 137597 declara 5.730.834.040 ações, enquanto a estimativa por percentual
  fica cerca de 34 mil ações abaixo. A aprovação do capital em 2023 não é tratada
  como prova da base física de uma contagem recebida em maio de 2024.
- O vínculo CNPJ/ticker utiliza ID do documento, versão, data de recebimento e
  início/fim da negociação. Um FCA recebido posteriormente não estabelece um vínculo
  disponível no passado. Units preservam sua composição literal, por exemplo uma
  ON e quatro PN da Energisa.
- B3: **9.812 registros brutos de proventos, 100 emissores**, com paginação conferida.
  Dos 113 emissores identificados no FCA para a coleta, 13 retornaram cadastro vazio
  na consulta atual. Cinco tickers do universo original não tinham código explícito
  nos arquivos FCA consultados. As ausências permanecem expostas.
- Cruzamento B3/RI: **184 recebíveis conferidos**, incluindo 88 de BBAS, 69 de
  Energisa (23 por classe ON, PN e UNT) e 27 de Ambev. Na Ambev, três parcelas
  de R$0,075 + R$0,0755 + R$0,1185 recompõem um direito bruto de R$0,269 por ação.
- **95 recebíveis importados** em `cash_events` da cópia, com quatro intervalos de
  cobertura em `cash_event_coverage`: ENGI3/4/11 de 04/01/2016 a 27/08/2026;
  ABEV3 de 04/01/2016 a 22/06/2026. Cada direito dessas listas foi reconciliado,
  por classe, data e montante, com o histórico integral paginado da B3 e o RI.
  A reimportação é idempotente. Isso atesta a concordância das fontes de caixa;
  não certifica eventos sem dinheiro, impostos ou o universo inteiro.

## Lacunas que a coleta demonstrou

O banco reconstruído ainda **não é uma base completa para provar rentabilidade**.
As observações novas ficam em `research_source_documents`, acrescentada pela
migração 0014. APIs de fatores não consultam essa tabela. Apenas os intervalos de
caixa conferidos acima foram promovidos à tabela própria de eventos.

1. Os arquivos correntes da CVM não recuperam todas as versões antigas dos
   demonstrativos. A data da versão disponível é conservadora; não se inventa
   o conteúdo da primeira entrega. Duas DFP de 2021 têm recibos ambíguos e foram
   excluídas com motivo.
2. O FCA de 2016 e 2017 não forneceu códigos aproveitáveis de negociação. Há
   ausências também nos anos seguintes. Um cadastro atual não preenche esse passado.
3. Nenhuma contagem de ações deste complemento recebeu uma data efetiva de base
   ou equivalência de classes sem prova. Portanto, H18/H19 continuam sem a base
   histórica de capitalização certificada.
4. A consulta histórica B3 não informa datas de pagamento. Dos 9.812 registros,
   4.469 puderam ser normalizados no calendário observado de 04/01/2016 a
   27/08/2026. Os demais incluem eventos fora da janela e registros com campos ou
   datas inconsistentes; não são todos defeitos de dados.
5. O relatório do BB traz, literalmente, pagamento em 12/06/2024 para direito de
   junho de 2025. Há também diferenças de valores e correções monetárias separadas.
   O histórico de BBAS não foi declarado completo.
6. Para o direito de ABEV3 em 23/06/2026, o RI indica pagamento em 30/12/2026 e o
   suplemento B3 indica 31/12/2026. Esse evento foi excluído da cobertura certificada.
7. Bonificações, subscrições, mudanças de classe e outros eventos sem dinheiro
   ainda precisam de reconciliação. Os proventos em caixa não resolvem esses efeitos.

## Reprodução e entrega

`tools/rebuild_source_history.py` exige os ZIPs previamente baixados, origem existente
e destino novo. Abre a origem em modo somente leitura, faz backup SQLite, aplica
migrações apenas na cópia, exporta JSONL e verifica SHA-256 e integridade SQLite.
Não calcula sinal, retorno, Sharpe ou veredito científico.

O pacote complementar contém o código, fontes, scripts de coleta/reconciliação,
JSONL, CSV de recebíveis, intervalos, relatórios de rejeição e banco reconstruído.
Os scripts intermediários descrevem os caminhos usados nesta sessão; o comando
principal de reconstrução aceita caminhos como argumentos. Não há dependência
nova de runtime. A leitura das fontes XLSX/PDF usou bibliotecas já disponíveis no
runtime de documentos, fora do pacote Stocks.

O resultado final dos testes e os hashes constam do manifesto de entrega. As
lacunas restantes são de cobertura e certificação histórica; não exigem que o
usuário execute comandos agora. Qualquer nova pesquisa deve continuar com esses
limites explícitos, sem liberar os testes protegidos por mera ingestão de dados.

## Fontes primárias

- [CVM DFP](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/)
- [CVM FRE](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/)
- [CVM FCA](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/)
- [B3 — empresas listadas e eventos corporativos](https://sistemaswebb3-listados.b3.com.br/listedCompaniesPage/)
- [B3 — definição de direito, ex e pagamento](https://www.b3.com.br/data/files/B3/72/8B/6A/D68A7910C2881879AC094EA8/Formulario%20de%20Proventos.pdf)
- [BB — histórico de remuneração](https://ri.bb.com.br/servicos-para-investidores/historico-de-remuneracao-ao-acionista/)
- [Energisa — histórico de dividendos](https://ri.energisa.com.br/governanca-corporativa/dividendos/)
- [Ambev — dividendos e JCP](https://ri.ambev.com.br/informacoes-aos-acionistas/dividendos-e-jcp/)


## Validação final desta entrega

- 448 testes passaram em 140.23 segundos com coverage e Core 3.2.0.
- Commit testado: `ce94aeecd2f7b78308cdb09b4a22ba2a06feea70`. Checkout limpo; nenhum push.
- Ruff aprovado, Pyright aprovado no escopo configurado pelo projeto (módulos RJ).
- Wheel construída e importada fora do checkout, incluindo os novos parsers.
- Todas as tabelas históricas e entradas protegidas preservadas por hash/conteúdo.
- O banco entregue contém 30.835 observações de auditoria, além de 95 recebíveis
  reconciliados e quatro intervalos de caixa. Os 4.177 documentos financeiros
  estão por emissor na área de auditoria; não foram projetados retroativamente
  para tickers sem vínculo histórico certificado.

O usuário não precisa baixar arquivos nem executar comandos para obter esta entrega.
O pacote não libera os testes protegidos nem demonstra lucro futuro.
