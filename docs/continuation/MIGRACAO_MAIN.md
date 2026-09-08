# Migração com código na main e dados separados

O operador pediu commit local na `main`, explicitamente **sem push**. A main
reúne a branch `fix/stocks-cvm-execution-20260907`, os três commits que estavam
somente em `origin/main` (até a6300a4) e os helpers ainda fora do Git.
As duas contribuições ao HANDOFF foram preservadas. Os seis arquivos locais
de dados não rastreados permanecem no checkout e também no arquivo de dados.

Revisão posterior das branches: somente **main** existe como branch local.
As duas alternativas locais e as 23 referências de acompanhamento já estavam
integralmente no histórico da main e foram removidas. O fetch acompanha somente
main. A pasta antiga de pesquisa continua intacta, em HEAD destacado no 68ce89d.
As branches no servidor GitHub não foram alteradas, respeitando o pedido de não
enviar mudanças. A prova está em BRANCH_REVIEW_20260908.json.

Validação concluída: **777 testes**, Ruff e Pyright aprovados. O ZIP tem
5.355.806.582 bytes (5,36 GB), com 18.583 objetos e 60.023 caminhos de dados.
Todos os hashes e CRCs foram conferidos; 25 bancos restaurados passaram no
quick_check e a auditoria 14 reproduziu o hash original usando o código da main.
Recibo completo em MIGRACAO_VERIFICADA.json. A restauração integral dos caminhos
ocupa 28,58 GB, além do pacote e do código; recomenda-se pelo menos 36 GB livres.

A entrega atual fica em `E:\STOCKS_MIGRACAO_MAIN_20260908`. Copiar a pasta
inteira para o outro PC, usando unidade que aceite arquivo maior que 4 GB.

- `CODIGO_MAIN.bundle`: repositório Git offline, incluindo a main e seu histórico.
- `DADOS_STOCKS.zip` + `DADOS_STOCKS.json`: dados, documentos, bancos e hashes.
- `DEPENDENCIAS/`: cópia das bibliotecas existentes, fora do ZIP. Nada foi instalado.
- `FONTES_WEB_ORIGINAIS/`: JavaScript e mapas capturados do site da B3, fora do ZIP.
- `MANIFESTO_DEPENDENCIAS.json` e `RESULTADO.json`: inventário e verificações.

O ZIP usa um objeto por SHA-256 e um manifesto com todos os caminhos, evitando
duplicar dados idênticos. **Usar o restaurador do Git**, pois extrair pelo Explorer
mostra objetos, não a árvore original. Bancos e fontes primárias mantêm os bytes.
ZIPs científicos que contêm somente dados mantêm seus bytes também. Os antigos
pacotes mistos foram abertos recursivamente: seus dados vão para
`unpacked-archives/`, e o código fica fora do ZIP. Esses contêineres antigos,
inclusive suas assinaturas de pacote, continuam no backup integral original
`E:\EXPORTACAO_STOCKS_20260908`, que foi preservado e contém código.

No outro PC, instalar Git e Python 3.13 global, sem venv. Exemplo em PowerShell
(ajustar a letra do disco do pacote e escolher destinos novos):

```powershell
$pacote = 'E:\STOCKS_MIGRACAO_MAIN_20260908'
git clone --branch main "$pacote\CODIGO_MAIN.bundle" 'C:\Stocks\codigo'
py -3.13 -B 'C:\Stocks\codigo\tools\data_transfer.py' verify "$pacote\DADOS_STOCKS.zip" --destination 'C:\Stocks\dados'
$env:PYTHONPATH = "$pacote\DEPENDENCIAS\research-runtime;$pacote\DEPENDENCIAS\checks;$pacote\DEPENDENCIAS\lint;$pacote\DEPENDENCIAS\python313-packages"
py -3.13 -B -c "import predictor_core; print(predictor_core.__version__, predictor_core.__file__)"
```

A saída do último comando deve mostrar **3.2.0** de `research-runtime`.
A ordem evita usar o Core 3.1.0 que existia nas bibliotecas globais do PC antigo.
O Python copiado inclui bibliotecas Windows x64/Python 3.13; outro sistema requer
dependências compatíveis. O executável Python e o Git não fazem parte da cópia.
O clone deixa `origin` apontando para o bundle offline. Não executar push;
o repositório remoto continua sem estes commits locais.

O restaurador verifica SHA-256, CRC e nomes antes de criar um destino novo;
confere novamente os arquivos gravados. A restauração integral exige o espaço
indicado por `restored_bytes` em DADOS_STOCKS.json, mais 1 GiB de margem.
`--prefix project/data` permite restaurar somente um recorte. Sem
`--destination`, o comando verifica tudo sem extrair os dados.

Mapeamento para os scripts/manifestos antigos, sem reescrever fontes:

| Caminho original | Nova localização do exemplo |
|---|---|
| `C:\Users\Superleo13\stocks-predictor-work` | `C:\Stocks\dados\project` (dados); código vigente em `C:\Stocks\codigo` |
| `.local-research\stocks-session-20260907` dentro da raiz original | `C:\Stocks\dados\project\.local-research\stocks-session-20260907` |
| chat `...\Documents\Codex\2026-09-07\lei-2` | `C:\Stocks\dados\session` |

Os códigos históricos arquivados mantêm os caminhos e comportamento antigos.
Não executá-los automaticamente: alguns ingerem dados ou consomem evidência.
ORIGENS.json em `research/session-20260908/local-scripts-preserved` e
`historical-code-preserved` localiza os scripts no Git por conteúdo e histórico.

## Estado para continuar

A auditoria das fontes 14 foi validada com Python 3.13 isolado durante a
exportação, inclusive na cópia restaurada. Manifesto de entrada:
`3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda`.
Auditoria: `f27461eeef0c86d5df0727dae73b3d1c4b9ed817b2c8423f2d2649c88d6a67a8`.
Dados em `session/work/migration-20260908/validation-14/inputs`.
Os dois líquidos Cogna foram preenchidos com fonte; continuam 24 datas,
52 líquidos, 28 entradas societárias e 1.248 inventários sem certificação.
A revisão 14 é complemento validado, ainda separado da entrada canônica 13.

Lucro futuro continua desconhecido (`null`), com `BLOCKED_MISSING_EVIDENCE`.
H1–H20 e contagens 53/55 permanecem preservadas; nenhuma nova avaliação de
retorno, escrita em banco original, ledger ou quarentena ocorreu na migração.
