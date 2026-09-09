# Reproduzir H21

Leia `docs/research/2026-09-09-h21-results.md` antes de interpretar valores.
Uma rodada, quatro especificações, oito valorizações de capital, mesma história
exploratória. O lucro executável integral e o lucro futuro permanecem desconhecidos.

Os scripts auxiliares usam somente stdlib e podem rodar no Python 3.12.14 fornecido
pelo Codex. Isso não substitui o contrato Python 3.13/Core do pacote nem o CI.
Não criar venv/instalar Core no Windows afetado. Não executar scripts legados
de paper/ingestão. Novos destinos são obrigatórios; nada é sobrescrito.

Nesta máquina, o arquivo `C:\STOCKS\DADOS_STOCKS.zip` já foi reunido e verificado.
As partes originais permanecem intactas. Para outra máquina, reuni-las em ordem
binária e conferir SHA-256
`83d5aac8e23d72e4deb1331077e08313914375a5dbac4276e5f8ad89da586d23`.
O recibo pequeno `DADOS_STOCKS.json` deve ficar ao lado do ZIP. O script de reunião
entregue pressupõe que as partes estejam no diretório do próprio script; no
pacote deste computador isso não ocorre. Não contornar políticas de execução.

Exemplo PowerShell, com diretórios novos:

```powershell
Set-Location 'C:\STOCKS\stocks-predictor'
$researchPython = 'C:\Users\leona\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$reproductionRoot = 'C:\STOCKS\work\h21-reproduction'
& $researchPython -B research/session-20260909/h21/acquire_inputs.py extract C:\STOCKS\DADOS_STOCKS.zip "$reproductionRoot\raw"
& $researchPython -B research/session-20260909/h21/extract_quotes.py "$reproductionRoot\raw" "$reproductionRoot\inputs"
& $researchPython -B research/session-20260909/h21/run_round.py --inputs "$reproductionRoot\inputs\quotes.json" --selic C:\STOCKS\work\h21\public\selic-11.json --protocol docs/research/2026-09-09-h21-protocol.json --expected-protocol-sha256 5721d7405af2f398448be3966eeb832deda06f7aa936e5244059ae7ca86797fb --output "$reproductionRoot\result.json" --journal "$reproductionRoot\reproduction-journal.jsonl"
& $researchPython -B research/session-20260909/h21/verify_result.py "$reproductionRoot\result.json" "$reproductionRoot\inputs\BOVA11.original-lines.txt" "$reproductionRoot\integer-check.json"
& $researchPython -B -m unittest discover -s tests -p test_etf_hold.py -v
& $researchPython -B -m unittest discover -s tests -p test_economics_labels.py -v
```

Use o Selic já capturado, hash
`82d23198927eedeef2193e6fb69f788c68cacf44f163d03ccad6636c34c3dcfd`.
Nova aquisição pode sofrer revisão pelo publicador e deve ser guardada com outra
identidade. URL original:
`https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=02/01/2018&dataFinal=31/03/2026`.
A licença ODbL e unidade estão no [catálogo BCB](https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic).

Artefatos da primeira medição em `C:\STOCKS\work\h21`:

- `raw/receipt.json`: manifesto dos nove objetos, origem e hashes;
- `inputs/quotes.json`: 2.050 linhas interpretadas, fontes e calendário;
- `inputs/BOVA11.original-lines.txt`: linhas originais sem modificação;
- `public/`: aquisição pública com recibos individuais;
- `result-01.json`: oito livros e curvas;
- `independent-accounting-01.json`: conferência separada em centavos.

Hash das linhas originais:
`95a0f8c69954911c7c8e332af846b830989ccbe3d2f7e6ed1bdff014213e6eb3`.
Hash de `quotes.json`:
`445a24c3098deb3da6f3bdd7b3d92ca48e24e6b4f9fdc38fb52b7705c2467d94`.
Hash do resultado completo original:
`39a940514b5fdcbb577c496f996ddd324c8107436852ab67da352401bb8870d2`.

O resultado inclui caminhos absolutos, SHA do checkout e detalhes do Python.
Esses metadados mudarão em outro ambiente; comparar os campos econômicos e hashes
das fontes, não chamar metadados diferentes de novo retorno. O protocolo e código
da medição original estão nos commits `62161fb` e `fbc2a2b`. A conferência separada
não importa o motor: lê diretamente os campos originais em centavos, dimensiona
lotes por outro algoritmo e reconcilia todos os pontos diários e tributos.

Não contar reprodução idêntica como hipótese ou evidência independente. Nunca
alterar o protocolo antigo para aceitar preços/intervalos diferentes. A captura
de fontes adicionais deve preservar as versões e revisar eventos antes de novo
resultado; não trocar ETF/janela por desempenho.

Os dados B3/BlackRock ficam locais. Git contém implementação, protocolo, resumo,
fontes citadas e hashes, sem presumir licença para redistribuir dados brutos.
Os testes da suíte geral, lint, Pyright, build e wheel real são os da execução CI
registrada no recibo da rodada. Os testes stdlib acima são apenas a validação local
do novo livro e dos rótulos econômicos.
