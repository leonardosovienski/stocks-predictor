param(
  [Parameter(Mandatory=$true)][long]$RunId,
  [Parameter(Mandatory=$true)][string]$ExpectedSha,
  [Parameter(Mandatory=$true)][ValidateSet('pr','main')][string]$Label
)
$ErrorActionPreference = 'Stop'
$r2Api = 'https://api.github.com/repos/leonardosovienski/stocks-predictor/actions/runs/' + $RunId
$r2Run = Invoke-RestMethod -Uri $r2Api -TimeoutSec 30
if ($r2Run.head_sha -ne $ExpectedSha) { throw 'CI SHA differs from expected commit' }
if ($r2Run.status -ne 'completed' -or $r2Run.conclusion -ne 'success') {
  [pscustomobject]@{run_id=$RunId; status=$r2Run.status; conclusion=$r2Run.conclusion} | ConvertTo-Json
  exit 2
}
$r2Jobs = Invoke-RestMethod -Uri ($r2Api + '/jobs?per_page=100') -TimeoutSec 30
if ($r2Jobs.total_count -ne 2 -or @($r2Jobs.jobs | Where-Object {$_.conclusion -ne 'success'}).Count -ne 0) {
  throw 'Not all expected jobs passed'
}
$r2Result = [ordered]@{observed_at_utc=[DateTime]::UtcNow.ToString('o'); run=$r2Run; jobs=$r2Jobs}
$r2Target = 'C:\STOCKS\work\data-completion-r2-20260909\ci-' + $Label + '-final.json'
if (Test-Path -LiteralPath $r2Target) { throw 'Final CI observation already exists' }
$r2Json = ($r2Result | ConvertTo-Json -Depth 30) + [Environment]::NewLine
[System.IO.File]::WriteAllText($r2Target, $r2Json, [System.Text.UTF8Encoding]::new($false))
[pscustomobject]@{path=$r2Target; run_id=$RunId; sha=$r2Run.head_sha; conclusion=$r2Run.conclusion;
  quality_job=($r2Jobs.jobs | Where-Object {$_.name -eq 'Quality / Python 3.13'}).id} | ConvertTo-Json
