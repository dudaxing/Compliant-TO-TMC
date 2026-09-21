$ErrorActionPreference = 'Stop'
$workspacePath = (Resolve-Path -LiteralPath '.github_handoff/c2_s0_workspace').Path
$targetPrefix = $workspacePath.TrimEnd('\') + '\'
$recordRoot = Join-Path $workspacePath 'handoff/s0'
$candidate = Get-Content -LiteralPath (Join-Path $recordRoot 'migration_candidate.json') -Raw | ConvertFrom-Json -AsHashtable
$archive = Get-Content -LiteralPath (Join-Path $recordRoot 'build_receipt.json') -Raw | ConvertFrom-Json -AsHashtable
$comparison = Get-Content -LiteralPath (Join-Path $recordRoot 'validation/restored_comparison.json') -Raw | ConvertFrom-Json -AsHashtable
$restoration = Get-Content -LiteralPath (Join-Path $recordRoot 'validation/full_restoration_verification.json') -Raw | ConvertFrom-Json -AsHashtable
$receiptPath = Join-Path $recordRoot 'candidate_removal_receipt.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Preserve prior removal record; do not repeat.' }
if ($archive.status -ne 'pass' -or -not $archive.all_copies_member_hashes_verified -or -not $archive.exact_restored_member_set) { throw 'Archive acceptance incomplete.' }
if ($comparison.status -ne 'pass' -or ($comparison.checks.Values -contains $false)) { throw 'Baseline/slim/restored comparison incomplete.' }
if ($restoration.status -ne 'pass' -or -not $restoration.full_evidence_checked -or $restoration.restored_historical_files -ne 1802) { throw 'Full restoration incomplete.' }
foreach ($group in $archive.groups) {
    foreach ($key in @('first_copy','second_copy')) {
        $copy = $group[$key]
        $file = Get-Item -LiteralPath $copy.path
        if ($file.Length -ne $copy.bytes -or (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $copy.sha256) { throw 'Archive backup changed.' }
    }
}
$paths = [System.Collections.Generic.List[string]]::new()
[long]$bytes = 0
foreach ($group in $candidate.groups.Values) {
    foreach ($row in $group.files) {
        $path = [System.IO.Path]::GetFullPath((Join-Path $workspacePath $row.path))
        if (-not $path.StartsWith($targetPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Deletion target escapes isolated delivery tree.' }
        if ($row.path.StartsWith('hf_repo/') -or $row.path.StartsWith('geometry_dataset/')) { throw 'Source or geometry deletion prohibited.' }
        $file = Get-Item -LiteralPath $path
        if ($file.PSIsContainer -or $file.Length -ne $row.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) { throw "Candidate changed: $($row.path)" }
        $paths.Add($path)
        $bytes += $file.Length
    }
}
if ($paths.Count -ne 1099 -or $bytes -ne 1115101240 -or ($paths | Sort-Object -Unique).Count -ne 1099) { throw 'Unexpected removal set.' }
$receipt = [ordered]@{schema='s0-verified-delivery-removal-v1';status='preflight_pass';tree=$workspacePath;files=$paths.Count;bytes=$bytes;two_archives_per_group_reverified=$true;full_restore_and_regression_passed=$true;source_and_geometry_deletions=0;original_full_workspace_and_archives_retained=$true;started_utc=[DateTime]::UtcNow.ToString('o')}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding utf8NoBOM
# Nonrecursive, literal-path removal after every absolute target and both backups were checked.
foreach ($path in $paths) { Remove-Item -LiteralPath $path -Force }
if ($paths.Where({ Test-Path -LiteralPath $_ }).Count -ne 0) { throw 'Some candidate paths remain.' }
$receipt.status = 'pass'
$receipt.completed_utc = [DateTime]::UtcNow.ToString('o')
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receiptPath -Encoding utf8NoBOM
$ignore = Join-Path $workspacePath '.gitignore'
$lines = @('', '# S0: original evidence restored by immutable asset/member hashes; exact historical paths only.')
foreach ($group in $candidate.groups.Values) { foreach ($row in $group.files) { $lines += '/' + $row.path } }
Add-Content -LiteralPath $ignore -Value $lines -Encoding utf8NoBOM
$receipt | ConvertTo-Json -Depth 5
