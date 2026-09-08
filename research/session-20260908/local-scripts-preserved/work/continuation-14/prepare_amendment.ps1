$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$taskBase = Join-Path $taskRoot 'baseline-13'
$taskInputs = Join-Path $taskBase 'inputs'
$taskDest = Join-Path $taskRoot 'inputs-14-awaiting-python-validation'
if (Test-Path -LiteralPath $taskDest) { throw 'Amendments are append-only' }

function Read-TaskJson([string]$Path) {
    return Get-Content -Raw -LiteralPath $Path -Encoding utf8 | ConvertFrom-Json -AsHashtable -Depth 100
}
function Write-TaskJson([string]$Path, $Value) {
    [IO.File]::WriteAllText($Path, (ConvertTo-Json -InputObject $Value -Depth 100) + "`n", [Text.UTF8Encoding]::new($false))
}
function Task-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Require-Task($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }

$taskManifest = Read-TaskJson (Join-Path $taskInputs 'SHA256.json')
Require-Task ((Task-Hash (Join-Path $taskInputs 'SHA256.json')) -eq '7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b') 'Wrong parent revision'
foreach ($taskName in $taskManifest.Keys) {
    $taskPath = [IO.Path]::GetFullPath((Join-Path $taskInputs $taskName))
    Require-Task ($taskPath.StartsWith($taskInputs + '\',[StringComparison]::OrdinalIgnoreCase)) 'Unsafe input member'
    Require-Task ((Task-Hash $taskPath) -eq $taskManifest[$taskName]) ('Changed input: ' + $taskName)
}
$taskCatalog = Read-TaskJson (Join-Path $taskInputs 'primary-catalog.json')
$taskIssuer = @($taskCatalog.Keys | Where-Object {$_ -like '*4606f00a86e4a533e242a4865b6615b45dfc2b6647802e38f8c14506d513fbb0-cvm-notice-0140.pdf'})
$taskLaw = @($taskCatalog.Keys | Where-Object {$_ -like '*519d9ad9eb39ed5e64eb5327467e3f65c60fa165e930222bc97b75fbbf179dd9-lei-15270-2025.html'})
Require-Task ($taskIssuer.Count -eq 1 -and $taskLaw.Count -eq 1) 'Original issuer and law files required'
$taskIssuer = $taskIssuer[0]; $taskLaw = $taskLaw[0]
$taskPages = Read-TaskJson (Join-Path $taskRoot 'document-text\4606f00a86e4a533e242a4865b6615b45dfc2b6647802e38f8c14506d513fbb0-cvm-notice-0140.json')
$taskText = (($taskPages | Where-Object {$_.page -in @(1,3)} | ForEach-Object {$_.text}) -join ' ') -replace '\s+',' '
$taskText = $taskText.ToLowerInvariant()
foreach ($taskLiteral in @('0,06614591210','0,04858806025','18 de dezembro de 2025',
    '23 de dezembro de 2025','26 de dezembro de 2025','13 de fevereiro de 2026',
    '20 de dezembro de 2028','sem retenção de imposto de renda na fonte')) {
    Require-Task ($taskText.Contains($taskLiteral)) ('Missing original text: ' + $taskLiteral)
}
$taskCash = Read-TaskJson (Join-Path $taskInputs 'cash-events.json')
$taskBefore = Read-TaskJson (Join-Path $taskInputs 'cash-events.json')
$taskProofs = @()
foreach ($taskTerms in @(
    @{Id='BRCOGNACNOR2:2025-12-26:DIVIDENDO:1';Gross='0.0661459121';Pay='2026-02-13';ResultYear=2025},
    @{Id='BRCOGNACNOR2:2025-12-26:DIVIDENDO:2';Gross='0.04858806025';Pay='2028-12-20';ResultYear=2024}
)) {
    $taskRows = @($taskCash | Where-Object {$_.event_id -eq $taskTerms.Id})
    Require-Task ($taskRows.Count -eq 1) 'One exact event required'
    $taskRow = $taskRows[0]
    Require-Task ($taskRow.ticker -eq 'COGN3' -and $taskRow.isin -eq 'BRCOGNACNOR2' -and
        $taskRow.action -eq 'DIVIDENDO' -and $taskRow.ex_date -eq '2025-12-26' -and
        $taskRow.gross_per_share -eq $taskTerms.Gross -and $taskRow.payment_date -eq $taskTerms.Pay -and
        $null -eq $taskRow.net_per_share) 'Identity, nominal or original schedule differs'
    $taskIssuerRef = @{
        file=$taskCatalog[$taskIssuer].original_file;sha256=$taskCatalog[$taskIssuer].sha256;
        url=$taskCatalog[$taskIssuer].url;verified_primary_file=$taskIssuer;pages=@(1,3)
    }
    $taskLawRef = @{
        file=$taskCatalog[$taskLaw].original_file;sha256=$taskCatalog[$taskLaw].sha256;
        url=$taskCatalog[$taskLaw].url;verified_primary_file=$taskLaw;
        locator='Lei15270/2025 art2: Lei9250 art6-A paragraph3, and art16-A paragraph1 XII. Approval before2026 and original payment terms.'
    }
    $taskProof = @{
        event_id=$taskTerms.Id;gross_per_share=$taskTerms.Gross;net_per_share=$taskTerms.Gross;
        approval_date='2025-12-18';last_cum='2025-12-23';ex_date='2025-12-26';
        payment_date=$taskTerms.Pay;result_year=$taskTerms.ResultYear;withholding_rate='0';
        scope='Resident individual: issuer-declared no withholding, original2025 approval and unchanged original payment schedule.';
        sources=@($taskIssuerRef);tax_source=@($taskLawRef);
        future_schedule_not_realized_cash=($taskTerms.Pay -gt '2026-09-08');
        requires_revalidation_if_schedule_or_law_changes=$true;
        personal_annual_tax_return_not_calculated=$true
    }
    $taskRow.net_per_share=$taskTerms.Gross
    $taskRow.tax_source=@($taskLawRef)
    $taskRow.sources=@($taskRow.sources)+@($taskIssuerRef)
    $taskRow.source_review=$true
    $taskRow.net_rule='RESIDENT_PF_2025_APPROVAL_TRANSITION_ISSUER_NO_IRRF'
    $taskRow.net_evidence_review=$taskProof
    $taskRow.actual_broker_cent_rounding_not_verified=$true
    $taskProofs+=@($taskProof)
}
Require-Task ($taskCash.Count -eq $taskBefore.Count -and $taskCash.Count -eq 800) 'Cash rows changed'
$taskChangedIds=@($taskProofs | ForEach-Object {$_.event_id})
for ($taskI=0;$taskI -lt $taskCash.Count;$taskI++) {
    if ($taskCash[$taskI].event_id -notin $taskChangedIds) {
        Require-Task ((ConvertTo-Json -InputObject $taskCash[$taskI] -Depth 100 -Compress) -eq
            (ConvertTo-Json -InputObject $taskBefore[$taskI] -Depth 100 -Compress)) 'Unrelated event changed'
    }
    foreach ($taskField in @('event_id','ticker','isin','action','ex_date','payment_date','gross_per_share','known_on','available_on')) {
        Require-Task ($taskCash[$taskI][$taskField] -eq $taskBefore[$taskI][$taskField]) ('Frozen cash field changed: ' + $taskField)
    }
}
$taskReview = @{
    schema='SOURCE_AMENDMENT_14';parent_manifest_sha256='7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b';
    status='PREPARED_AWAITING_PYTHON_3_13_VALIDATION';amendments=$taskProofs;
    fields_reconciled=2;remaining_net_values=52;remaining_payment_dates=24;
    corporate_inputs_pending=28;inventory_intervals_without_certification=1248;
    checked_in_powershell=@('All827parent-input hashes','Exact two issuer distribution identities','Original payment schedules unchanged',
        'All800rows preserved','All unrelated events unchanged','Gross/ex/payment/knowledge/availability unchanged');
    python_project_tests_run=$false;original_checkout_updated=$false;
    profit=$null;future_profit_projection=$null;new_historical_return_evaluations=0;
    environment_blocks=@('Original checkout access denied','Global Python3.13 launcher unavailable',
        'Direct original-source download denied by socket permissions');
    document_runtime='Bundled Python3.12.14 used only for PDF inspection, not project execution';
    original_source_downloads_performed=0
}
Write-TaskJson (Join-Path $taskRoot 'source-amendment-14.json') $taskReview
$taskSnapshot = Read-TaskJson (Join-Path $taskBase 'revision-trail\cash-closure-13.json')
$taskSnapshot.schema='SOURCE_CLOSURE_CASH_14'
$taskSnapshot.parent_sha256=Task-Hash (Join-Path $taskBase 'revision-trail\cash-closure-13.json')
$taskSnapshot.cash_events=$taskCash
$taskSnapshot.net_facts=@($taskSnapshot.net_facts)+$taskProofs
$taskSnapshot.counts.missing_net_after=52
$taskSnapshot.validation_status='PREPARED_AWAITING_PYTHON_3_13_VALIDATION'
Write-TaskJson (Join-Path $taskRoot 'cash-closure-14.json') $taskSnapshot
[IO.Directory]::CreateDirectory($taskDest) | Out-Null
foreach ($taskName in @($taskManifest.Keys)+@('SHA256.json')) {
    $taskTarget=[IO.Path]::GetFullPath((Join-Path $taskDest $taskName))
    Require-Task ($taskTarget.StartsWith($taskDest + '\',[StringComparison]::OrdinalIgnoreCase)) 'Unsafe revision target'
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($taskTarget)) | Out-Null
    [IO.File]::Copy((Join-Path $taskInputs $taskName),$taskTarget,$false)
}
Write-TaskJson (Join-Path $taskDest 'cash-events.json') $taskCash
$taskRevision=Read-TaskJson (Join-Path $taskDest 'source-revision.json')
$taskRevision.snapshot_sha256=Task-Hash (Join-Path $taskRoot 'cash-closure-14.json')
$taskRevision.counts=$taskSnapshot.counts
$taskRevision.parent_source_manifest_sha256=$taskReview.parent_manifest_sha256
$taskRevision.validation_status=$taskReview.status
$taskRevision.amendment_sha256=Task-Hash (Join-Path $taskRoot 'source-amendment-14.json')
Write-TaskJson (Join-Path $taskDest 'source-revision.json') $taskRevision
$taskManifest['cash-events.json']=Task-Hash (Join-Path $taskDest 'cash-events.json')
$taskManifest['source-revision.json']=Task-Hash (Join-Path $taskDest 'source-revision.json')
Write-TaskJson (Join-Path $taskDest 'SHA256.json') $taskManifest
foreach ($taskName in $taskManifest.Keys) {
    Require-Task ((Task-Hash (Join-Path $taskDest $taskName)) -eq $taskManifest[$taskName]) ('Revised hash mismatch: ' + $taskName)
}
Require-Task (@($taskCash | Where-Object {$null -eq $_.net_per_share}).Count -eq 52) 'Unexpected missing-net count'
Require-Task (@($taskCash | Where-Object {-not $_.payment_date}).Count -eq 24) 'Unexpected missing-date count'
@{Status=$taskReview.status;NetFieldsReconciled=2;RemainingNet=52;RemainingDates=24;
  ManifestSHA256=(Task-Hash (Join-Path $taskDest 'SHA256.json'));ProjectTestsRun=$false} | ConvertTo-Json
