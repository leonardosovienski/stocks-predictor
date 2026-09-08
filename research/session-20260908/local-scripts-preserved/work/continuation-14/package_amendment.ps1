$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath($PSScriptRoot)
$taskChat=[IO.Path]::GetFullPath((Join-Path $taskRoot '..\..'))
$taskStage=Join-Path $taskRoot 'deliverable'
if (Test-Path -LiteralPath $taskStage) {throw 'Preserve existing deliverable'}
[IO.Directory]::CreateDirectory($taskStage) | Out-Null
[IO.Directory]::CreateDirectory((Join-Path $taskStage 'replacement-inputs')) | Out-Null
[IO.Directory]::CreateDirectory((Join-Path $taskStage 'reviewed-primary')) | Out-Null
foreach ($taskName in @('source-amendment-14.json','cash-closure-14.json','VALIDAR_REVISAO_14.py','prepare_amendment.ps1','inspect_local_sources.py','package_amendment.ps1')) {
    [IO.File]::Copy((Join-Path $taskRoot $taskName),(Join-Path $taskStage $taskName),$false)
}
foreach ($taskName in @('cash-events.json','source-revision.json','SHA256.json')) {
    [IO.File]::Copy((Join-Path $taskRoot ('inputs-14-awaiting-python-validation\'+$taskName)),(Join-Path $taskStage ('replacement-inputs\'+$taskName)),$false)
}
$taskBase=Join-Path $taskRoot 'baseline-13'
$taskCatalog=Get-Content -Raw -LiteralPath (Join-Path $taskBase 'inputs\primary-catalog.json') -Encoding utf8 | ConvertFrom-Json -AsHashtable
$taskIssuer=@($taskCatalog.Keys | Where-Object {$_ -like '*-cvm-notice-0140.pdf'})[0]
$taskLaw=@($taskCatalog.Keys | Where-Object {$_ -like '*-lei-15270-2025.html'})[0]
foreach ($taskName in @($taskIssuer,$taskLaw)) {
    [IO.File]::Copy((Join-Path $taskBase ('inputs\'+$taskName)),(Join-Path $taskStage ('reviewed-primary\'+[IO.Path]::GetFileName($taskName))),$false)
}
$taskIssuerUrl=$taskCatalog[$taskIssuer].url
$taskReport=@"
# Stocks Predictor — complemento 14 preparado

**A revisão 14 foi preparada, mas ainda não foi validada pelo projeto em Python 3.13 nem aplicada ao checkout original. A revisão 13 continua sendo a última validada.**

Foram conciliados dois valores líquidos da Cogna com o aviso original de 18/12/2025: R`$ 0,0661459121, com pagamento previsto em 13/02/2026, e R`$ 0,04858806025, previsto em 20/12/2028. O aviso declara ausência de retenção de IR e identifica os resultados de 2025 e 2024, as datas de corte e o cronograma. A revisão preserva os valores brutos, as datas e todos os 800 pagamentos. [Aviso original da Cogna]($taskIssuerUrl).

A análise documental considera a regra de transição para distribuições aprovadas até 2025, mantendo os termos originais de pagamento. Não calcula a declaração anual pessoal. O pagamento de 2028 é um cronograma futuro e precisa ser revalidado se os termos ou a lei mudarem. [Lei 15.270/2025, artigo 2º](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15270.htm).

## Verificações realizadas agora

- O ZIP da revisão 13 confere com o SHA256 publicado: ef3dc22b280ec89180b995495bc6013f059482695d3ebd63c92ef496bddb4fb4.
- Seus 1.485 arquivos foram verificados após a extração nesta pasta autorizada.
- Uma busca nos documentos locais examinou 5.323 páginas de 477 PDFs, sem erro de extração. Isso não certifica a completude do inventário.
- O PowerShell verificou os 827 hashes das entradas anteriores e os da revisão preparada, a identidade dos dois dividendos e a conservação de todas as linhas, valores brutos, datas e conhecimento. Os demais 798 pagamentos permanecem iguais.
- Nenhum código do motor foi alterado. Nenhum teste do projeto em Python 3.13, novo retorno histórico ou projeção de lucro foi executado nesta etapa. O Python 3.12.14 disponibilizado para documentos foi usado exclusivamente na leitura de PDFs.

O manifesto da revisão preparada é 3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda. O arquivo source-amendment-14.json conserva o estado PREPARED_AWAITING_PYTHON_3_13_VALIDATION. Os 735 testes e os 166 testes na wheel pertencem à revisão 13; não são resultados novos desta revisão.

## O que ainda falta

Após os dois ajustes preparados, ainda ficam 52 líquidos, 24 datas e 28 entradas societárias, além dos 1.248 intervalos sem inventário integral certificado. As contagens se sobrepõem. Permanecem datas máximas sem confirmação de pagamento, conflitos de valores, crédito tributário de JCP, restituições de capital, custo fiscal, frações e entregas de sucessores. Nenhuma dessas lacunas foi transformada em zero ou descartada para melhorar o resultado.

Uma consulta adicional ao RI da Raia voltou a encontrar apenas prazo máximo para o JCP de setembro de 2020. O aviso menciona reunião em 16/09, enquanto a ata publicada registra 17/09; esse conflito precisa ser preservado na conciliação. O download do arquivo original adicional foi bloqueado, então a consulta não foi incorporada às entradas como nova fonte com hash. [Aviso da Raia](https://ri.rd.com.br/Download.aspx?Arquivo=Es0bnDmZWjYZQMWftiHJew%3D%3D&linguagem=pt), [ata publicada no Diário Oficial](https://diariooficial.imprensaoficial.com.br/doflash/prototipo/2020/Setembro/22/empresarial/pdf/pg_0007.pdf).

Lucro líquido histórico e projeção futura continuam desconhecidos. H1–H20, as contagens 53/55 e as observações anteriores permanecem preservados. A falta de um holdout intacto não pode ser corrigida inventando dados futuros. O protocolo de fontes exige evidência suficiente e pré-inscrição separada antes de uma nova avaliação econômica.

## Bloqueio do ambiente

As permissões atuais negaram a leitura do checkout original, impediram o lançamento do Python global 3.13 e negaram o download direto de fontes por acesso ao socket. A escrita está limitada à pasta desta tarefa. As consultas pelo navegador de pesquisa continuam possíveis, mas não substituem a aquisição dos arquivos originais exigida pelo protocolo.

Para concluir a integração, os testes e a aquisição das fontes faltantes, o ambiente precisa permitir acesso ao projeto, execução do Python 3.13 e downloads das fontes públicas. Nenhuma permissão foi contornada. Não houve escrita em bancos, ledgers ou quarentenas, instalação, serviço pago, agente adicional ou ordem de mercado.

## Complemento pronto para validar

COMPLEMENTO_FONTES_14.zip contém os dois ajustes, as fontes originais usadas, o snapshot completo preparado, os arquivos substitutos e VALIDAR_REVISAO_14.py. Ele utiliza a wheel já validada do pacote 13, sem instalar dependências nem acessar a rede.

Depois de extrair os dois pacotes e com Python 3.13 disponível, execute no diretório do complemento:

    py -3.13 -I VALIDAR_REVISAO_14.py --baseline13 CAMINHO_DO_PACOTE_13_EXTRAIDO --workspace NOVA_PASTA_DE_VALIDACAO

O comando verifica os dois manifestos, conserva a base, materializa a revisão em uma pasta nova e executa somente a auditoria de fontes. A saída esperada continua economicamente bloqueada, com 52 líquidos e 24 datas faltantes. Esse resultado ainda não foi produzido neste ambiente; o comando falha de forma explícita em outra versão de Python.
"@
[IO.File]::WriteAllText((Join-Path $taskStage 'LEIA-ME.md'),$taskReport,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $taskChat 'outputs\CONTINUACAO_STOCKS_14.md'),$taskReport,[Text.UTF8Encoding]::new($false))
[IO.File]::Copy((Join-Path $taskRoot 'source-amendment-14.json'),(Join-Path $taskChat 'outputs\REVISAO_14_PENDENTE_VALIDACAO.json'),$false)
$taskManifest=[ordered]@{}
Get-ChildItem -LiteralPath $taskStage -File -Recurse | Sort-Object FullName | ForEach-Object {
    $taskRelative=[IO.Path]::GetRelativePath($taskStage,$_.FullName).Replace('\','/')
    $taskManifest[$taskRelative]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
[IO.File]::WriteAllText((Join-Path $taskStage 'COMPLEMENTO_SHA256.json'),(ConvertTo-Json -InputObject $taskManifest -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
Add-Type -AssemblyName System.IO.Compression.FileSystem
$taskZip=Join-Path $taskChat 'outputs\COMPLEMENTO_FONTES_14.zip'
if (Test-Path -LiteralPath $taskZip) {throw 'Preserve earlier supplement'}
[IO.Compression.ZipFile]::CreateFromDirectory($taskStage,$taskZip,[IO.Compression.CompressionLevel]::Optimal,$false)
$taskArchive=[IO.Compression.ZipFile]::OpenRead($taskZip)
try {
    foreach ($taskEntry in $taskArchive.Entries) {
        if ($taskEntry.FullName -eq 'COMPLEMENTO_SHA256.json') {continue}
        $taskStream=$taskEntry.Open()
        try {$taskHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskStream)).ToLowerInvariant()}
        finally {$taskStream.Dispose()}
        if ($taskHash -ne $taskManifest[$taskEntry.FullName]) {throw ('ZIP hash mismatch: '+$taskEntry.FullName)}
    }
} finally {$taskArchive.Dispose()}
@{File=$taskZip;Bytes=(Get-Item -LiteralPath $taskZip).Length;SHA256=(Get-FileHash -LiteralPath $taskZip -Algorithm SHA256).Hash.ToLowerInvariant();Payloads=$taskManifest.Count;Status='PREPARED_AWAITING_PYTHON_3_13_VALIDATION'} | ConvertTo-Json
