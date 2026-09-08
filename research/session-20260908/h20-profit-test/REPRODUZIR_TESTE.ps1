param([Parameter(Mandatory=$true)][string]$OutputFile)
$ErrorActionPreference = 'Stop'
$researchRoot = 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907'
$env:PYTHONPATH = "$researchRoot\work\stocks-predictor;$researchRoot\work\runtime;$researchRoot\work\checks"
py -3.13 "$PSScriptRoot\compare_h20.py" --root $researchRoot --protocol "$PSScriptRoot\protocol.json" --gate "$PSScriptRoot\h19-gate-replay.json" --output $OutputFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$actualDigest = (Get-FileHash -LiteralPath $OutputFile -Algorithm SHA256).Hash.ToLower()
if ($actualDigest -ne 'aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3') { throw 'Resultado difere da observação preservada.' }
Write-Output 'Reproduzido byte a byte. Lucro líquido permanece desconhecido.'
