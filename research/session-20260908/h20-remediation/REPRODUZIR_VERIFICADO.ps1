param([Parameter(Mandatory=$true)][string]$OutputFile)
$ErrorActionPreference = 'Stop'
$repairRoot = 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPATH = "$repairRoot\work\stocks-predictor;$repairRoot\work\runtime;$repairRoot\work\checks"
py -3.13 -m stocks_predictor.h20_checked --root $repairRoot --gate "$repairRoot\work\h20-profit-test-20260908\h19-gate-replay.json" --output $OutputFile
exit $LASTEXITCODE
