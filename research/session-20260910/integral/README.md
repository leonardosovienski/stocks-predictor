# Reproduzir e conferir a auditoria integral

Leia primeiro o [relatório](../../../docs/audit/2026-09-10-integral/README.md) e o [registro](../../../docs/audit/2026-09-10-integral/registry.json). Todos os exemplos desta máquina usam a raiz autorizada `C:\STOCKS`. Nunca sobrescrever livros, protocolos ou destinos de reprodução existentes. Scripts históricos têm restrições próprias; não executar ingestão, paper ou broker para reproduzir H21.

## Ambiente

Produção: Linux CI, Python3.13, Core3.2.0 oficial e dependências do `uv.lock`. CI197 validou `c1f99b67025c0c013527c3a71c458f1d32d59fe0`; o PR74 informa o último commit testado e o merge. Python local3.12.14 é apenas ferramenta auxiliar; não criar venv, instalar dependências ou alterar EDR/Core/Python no Windows.

```powershell
Set-Location 'C:\STOCKS\stocks-predictor'
$researchPython = 'C:\Users\leona\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
git status --short --branch
git rev-parse HEAD
& $researchPython -B research/session-20260910/integral/verify_audit.py
```

O último comando precisa somente dos recibos versionados. Confere SHA-256, IDs e referências, 24 frentes e sete usos; não certifica documentos externos por hash. O diretório canônico é `docs/audit/2026-09-10-integral`.

## H21 — fontes, decisão, livro e conferência separada

Pré-requisitos existentes: nove COTAHIST originais em `C:\STOCKS\work\h21\raw`, Selic capturada em `C:\STOCKS\work\h21\public\selic-11.json`, protocolo V1 no Git. O [guia H21 original](../../session-20260909/h21/README.md) explica como extrair do arquivo de migração quando os nove objetos ainda não estiverem materializados. Fonte nova não deve substituir o arquivo lacrado antigo.

```powershell
$replayRoot = 'C:\STOCKS\work\h21-replay-audit-independent'
if (Test-Path -LiteralPath $replayRoot) { throw 'Escolha um destino novo; não sobrescreva a reprodução anterior.' }
& $researchPython -B research/session-20260909/h21/extract_quotes.py 'C:\STOCKS\work\h21\raw' "$replayRoot\inputs"
if ($LASTEXITCODE -ne 0) { throw 'Extração falhou' }
& $researchPython -B research/session-20260909/h21/run_round.py --inputs "$replayRoot\inputs\quotes.json" --selic 'C:\STOCKS\work\h21\public\selic-11.json' --protocol docs/research/2026-09-09-h21-protocol.json --expected-protocol-sha256 5721d7405af2f398448be3966eeb832deda06f7aa936e5244059ae7ca86797fb --output "$replayRoot\result.json" --journal "$replayRoot\replay-journal.jsonl"
if ($LASTEXITCODE -ne 0) { throw 'Livro H21 falhou' }
& $researchPython -B research/session-20260909/h21/verify_result.py "$replayRoot\result.json" "$replayRoot\inputs\BOVA11.original-lines.txt" "$replayRoot\integer-check.json"
if ($LASTEXITCODE -ne 0) { throw 'Conferência em centavos falhou' }
```

O journal do runner registra especificações, mas esta execução é **replay de uma história exposta**, zero nova hipótese e zero evidência independente. Compare os oito campos `outcomes`, referência Selic e hashes de entradas. Caminhos absolutos, Python, SHA e hash do JSON completo naturalmente podem mudar. E18 documenta a igualdade dos campos econômicos na auditoria; E11 confere 16.400 pontos por outro algoritmo em centavos, do mesmo auditor.

Para rehash dos nove ZIPs e comparação completa com o original já guardado:

```powershell
& $researchPython -B research/session-20260909/h21/reproduce_check.py 'C:\STOCKS\work\h21' 'C:\STOCKS\work\h21-check-new.json'
```

## H20 — reconciliação delimitada

Pré-requisito: `C:\STOCKS\DADOS_STOCKS.zip` com SHA `83d5aac8e23d72e4deb1331077e08313914375a5dbac4276e5f8ad89da586d23`. O programa usa somente os objetos consumidos, extraídos com SHA individual, e lê bancos em modo somente leitura. Importa algoritmos atuais identificados e um auxiliar bootstrap congelado cujo hash também é verificado; esse auxiliar não é o Core de produção.

```powershell
& $researchPython -B research/session-20260910/integral/reconcile_h20.py --root 'C:\STOCKS' --output 'C:\STOCKS\work\h20-consumed-new'
if ($LASTEXITCODE -ne 0) { throw 'Reconciliação H20 falhou; preservar log e saída parcial' }
```

Saída: `verification.json`, hashes das entradas/código, contagens, tolerância e diferenças; `underlying-recomputed.json` conserva o cálculo detalhado local. Resultados esperados: 9.732 células, 12 cenários subjacentes, 18 cenários de estratégia, 465 médias, 30 trajetórias, 54 pares e 54 comparações de intervalos. Floats finitos têm tolerância relativa/absoluta2e-12; estrutura/IDs exatos. A única diferença observada na auditoria foi2,22e-16 em uma anualização.

**Isto não executa nem desativa o verificador integral original de1.448 arquivos.** Cinco objetos faltam; [E12](../../../docs/audit/2026-09-10-integral/evidence/h20-omissions.json) traz caminhos e SHA. Recuperados os cinco bytes exatos, o wrapper histórico poderá ser retomado com seus requisitos originais. Não criar arquivos substitutos sob os hashes esperados.

## Auditoria de fontes e regressões locais

```powershell
& $researchPython -B -I research/session-20260909/data_completion/audit_recovered.py 'C:\STOCKS\data\recovery-r2' 'C:\STOCKS\work\source-check-new.json'
& $researchPython -B -m unittest tests.test_audit_integrity tests.test_etf_hold tests.test_economics_labels tests.test_data_bank -v
```

Esperado para o contrato desta revisão:49 testes stdlib passam; as fontes13/14 continuam bloqueadas por lacunas, com0/1.248 intervalos completos. O sucesso do comando de auditoria indica execução correta do diagnóstico de bloqueio, não prontidão das fontes.

A suíte completa com Core é a da [CI](../../../.github/workflows/ci.yml), não executar instalação no Windows. Os logs de falha CI195/196 e de sucesso CI197 foram preservados junto aos recibos. Os 24 testes adicionais em relação à base correspondem a18 regressões de integridade/gate, três guardas paper e três contratos RJ; também foram ampliadas asserções de testes existentes. Repetir teste só quando mudanças, falhas ou uma dúvida concreta justificarem.

## Identidade e continuidade

O `registry.json` relaciona claims → achados → evidências/execuções/decisões/usos. O relatório é a visão humana, não outra fila. Evidências locais completas, fontes primárias e logs auxiliares permanecem em `C:\STOCKS\work\audit-integral-20260910`; banco/catálogos em `C:\STOCKS\data`. Os recibos copiados para Git não incluem dados brutos B3, PDFs ou banco.

O pacote de saída local contém o relatório, registro, recibos e `ENTREGA.json` com SHA final de integração. Não ativar agendamento, paper, login, compra ou ordem a partir destes comandos. H21 permanece condicional; H20 amplo permanece estacionado.
