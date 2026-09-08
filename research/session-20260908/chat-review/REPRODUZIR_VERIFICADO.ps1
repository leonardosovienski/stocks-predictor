param([Parameter(Mandatory=$true)][string]$OutputFile)
$ErrorActionPreference = 'Stop'
$reviewRoot = 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907'
$env:PYTHONPATH = "$reviewRoot\work\stocks-predictor;$reviewRoot\work\runtime;$reviewRoot\work\checks"
py -3.13 "$PSScriptRoot\reproduce_h20_checked.py" --root $reviewRoot --gate "$reviewRoot\work\h20-profit-test-20260908\h19-gate-replay.json" --output $OutputFile
exit $LASTEXITCODE
