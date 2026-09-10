$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath('C:\STOCKS')
$chatRoot = [System.IO.Path]::GetFullPath('C:\Users\leona\Documents\Codex\2026-09-09\crie-uma-imagem-de-2')
$journalPath = Join-Path $projectRoot 'work\centralizacao-20260909\movimentacoes.json'
$deliveryNames = @('CI_MAIN_STOCKS_H21.txt','CONFERENCIA_STOCKS_H21.json','ENTREGA_STOCKS_H21.json','RELATORIO_STOCKS_H21.md','REPRODUCAO_STOCKS_H21.json','RESULTADO_STOCKS_H21.json')
$entries = @()
foreach ($name in $deliveryNames) {
    $entries += [pscustomobject]@{source=(Join-Path $chatRoot "outputs\$name");destination=(Join-Path $projectRoot "outputs\$name");sha256=$null;bytes=$null;status='planned'}
}
$entries += [pscustomobject]@{
    source='C:\Users\leona\Downloads\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md'
    destination=(Join-Path $projectRoot 'instructions\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md')
    sha256=$null;bytes=$null;status='planned'
}
function Write-Journal {
    $record = [ordered]@{
        schema_version=1
        updated_at_utc=[DateTime]::UtcNow.ToString('o')
        authorized_root=$projectRoot
        method='Copy exact bytes, verify SHA-256 at both locations, remove only the individually verified original file.'
        moves=$entries
    }
    [System.IO.File]::WriteAllText($journalPath, ($record | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
}
if (Test-Path -LiteralPath $journalPath) { throw 'O recibo desta movimentação já existe; conferir antes de repetir.' }
# Verify every explicit source/destination before making changes.
foreach ($entry in $entries) {
    $source = [System.IO.Path]::GetFullPath($entry.source)
    $destination = [System.IO.Path]::GetFullPath($entry.destination)
    if (-not $destination.StartsWith($projectRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fora de C:\STOCKS.' }
    $allowedSource = $source.StartsWith($chatRoot + '\outputs\', [System.StringComparison]::OrdinalIgnoreCase) -or $source -eq 'C:\Users\leona\Downloads\STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md'
    if (-not $allowedSource) { throw 'Origem fora do inventário autorizado.' }
    $item = Get-Item -LiteralPath $source
    if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Origem não é arquivo regular.' }
    if (Test-Path -LiteralPath $destination) { throw "Destino já existe: $destination" }
    $entry.sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    $entry.bytes = $item.Length
}
if ($entries[-1].sha256 -ne 'd63db21471620a6a4a83671e1acebda1d7ff0be04a96652d5f0d658997cc73cc') { throw 'Prompt foi modificado desde a execução.' }
foreach ($directory in @('outputs','instructions','work\centralizacao-20260909')) {
    $newDirectory = Join-Path $projectRoot $directory
    if (Test-Path -LiteralPath $newDirectory) {
        if ((Get-Item -LiteralPath $newDirectory).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Destino contém link.' }
    } else { New-Item -Path $newDirectory -ItemType Directory | Out-Null }
}
Write-Journal
foreach ($entry in $entries) {
    Copy-Item -LiteralPath $entry.source -Destination $entry.destination
    if ((Get-FileHash -LiteralPath $entry.destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Cópia não confere; origem preservada.' }
    $entry.status = 'copied_and_hash_verified'
    Write-Journal
}
foreach ($entry in $entries) {
    if ((Get-FileHash -LiteralPath $entry.source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Origem mudou; preservada.' }
    if ((Get-FileHash -LiteralPath $entry.destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'Destino mudou; origem preservada.' }
    Remove-Item -LiteralPath $entry.source
    if (Test-Path -LiteralPath $entry.source) { throw 'Origem permanece.' }
    $entry.status = 'moved_and_verified'
    Write-Journal
}
# Remove only empty child directories, never the current task root.
foreach ($child in @('outputs','work')) {
    $emptyCandidate = [System.IO.Path]::GetFullPath((Join-Path $chatRoot $child))
    if (-not $emptyCandidate.StartsWith($chatRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Diretório fora da tarefa.' }
    if ((Test-Path -LiteralPath $emptyCandidate) -and @(Get-ChildItem -LiteralPath $emptyCandidate -Force).Count -eq 0) {
        Remove-Item -LiteralPath $emptyCandidate
    }
}
[pscustomobject]@{MovedFiles=$entries.Count;VerifiedBytes=($entries | Measure-Object -Property bytes -Sum).Sum;Journal=$journalPath;AllSourcesAbsent=(@($entries | Where-Object { Test-Path -LiteralPath $_.source }).Count -eq 0)} | ConvertTo-Json

