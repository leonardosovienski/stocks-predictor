param(
    [string]$ResearchRoot = 'C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907',
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
$repoPath = Join-Path $ResearchRoot 'work\stocks-predictor'
$arguments = @(
    '-3.13', '-m', 'stocks_predictor.h20_research',
    '--features', (Join-Path $ResearchRoot 'work\value-prepared-features.json'),
    '--accounting', (Join-Path $ResearchRoot 'work\value-capital-source\accounting-v2.json'),
    '--source-dir', (Join-Path $ResearchRoot 'work\source-acquisition'),
    '--execution-inputs', (Join-Path $ResearchRoot 'work\stocks-final-review-bundle\inputs'),
    '--protocol', (Join-Path $repoPath 'docs\research\2026-09-08-h20-implementation-protocol.json'),
    '--entry-unit-review', (Join-Path $ResearchRoot 'work\continuation-20260908\entry-unit-review\review.json'),
    '--output', $Output
)
Push-Location -LiteralPath $repoPath
try { & py @arguments; $runExit = $LASTEXITCODE }
finally { Pop-Location }
exit $runExit
