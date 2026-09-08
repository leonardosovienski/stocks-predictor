$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    py -3.13 -m stocks_predictor.continuous_research --inputs ./inputs --output ./RESULTADO_H19.json
    $h19ExitCode = $LASTEXITCODE
    if ($h19ExitCode -eq 2) { Write-Host 'Dados incompletos: auditoria concluida, lucro nao calculado. Consulte RESULTADO_H19.json.' }
    exit $h19ExitCode
} finally { Pop-Location }
