# ─────────────────────────────────────────────────────────────────────
#  scrub-history.ps1 — wipe sensitive paths from git history (BOTH remotes)
#
#  Removes from EVERY commit on the master branch:
#    • output/                       (all generated documents + receipts)
#    • backend/__pycache__/          (Python bytecode)
#    • backend/engines/__pycache__/  (Python bytecode)
#    • backend/data/drafts/          (auto-saved drafts)
#
#  Then re-adds remotes (filter-repo strips them by design) and force-pushes
#  to GitHub AND Codeberg so both reflect the scrubbed history.
#
#  REQUIRES: git-filter-repo (script will offer to pip install it).
#  DESTRUCTIVE: rewrites public history. Re-clones required for any other
#  machine that has this repo cloned.
# ─────────────────────────────────────────────────────────────────────
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp   = Get-Date -Format 'yyyy-MM-dd_HHmm'
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  SOVEREIGN DOCS - HISTORY SCRUB" -ForegroundColor Yellow
Write-Host "  Project: $ProjectRoot" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

# ─── 0. SANITY CHECKS ──────────────────────────────────────────────
Write-Host "> Checking working tree..." -ForegroundColor Cyan
$status = git status --porcelain
if ($status) {
  Write-Host "[FAIL] Working tree has uncommitted changes:" -ForegroundColor Red
  Write-Host $status
  Write-Host ""
  Write-Host "Commit or stash them first, then re-run this script." -ForegroundColor Yellow
  exit 1
}
Write-Host "  [OK] working tree clean" -ForegroundColor Green
Write-Host ""

# ─── 1. CAPTURE REMOTES ────────────────────────────────────────────
Write-Host "> Capturing remote URLs..." -ForegroundColor Cyan
$remoteList = git remote
$remoteMap = @{}
foreach ($r in $remoteList) {
  $url = git remote get-url $r
  $remoteMap[$r] = $url
  Write-Host "  $r -> $url" -ForegroundColor DarkGray
}
if ($remoteMap.Count -eq 0) {
  Write-Host "[FAIL] No remotes configured. Aborting." -ForegroundColor Red
  exit 1
}
Write-Host ""

# ─── 2. INSTALL git-filter-repo IF MISSING ─────────────────────────
Write-Host "> Checking for git-filter-repo..." -ForegroundColor Cyan
$hasFilterRepo = $false
try {
  $null = git filter-repo --version 2>&1
  if ($LASTEXITCODE -eq 0) { $hasFilterRepo = $true }
} catch {}
if (-not $hasFilterRepo) {
  Write-Host "  git-filter-repo not found. Installing via pip..." -ForegroundColor Yellow
  pip install git-filter-repo
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] pip install failed. Install manually: pip install git-filter-repo" -ForegroundColor Red
    exit 1
  }
  Write-Host "  [OK] installed" -ForegroundColor Green
} else {
  Write-Host "  [OK] git-filter-repo present" -ForegroundColor Green
}
Write-Host ""

# ─── 3. SHOW WHAT'S ABOUT TO HAPPEN ────────────────────────────────
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  THIS WILL PERMANENTLY REWRITE GIT HISTORY" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Will be REMOVED from every commit on master:" -ForegroundColor White
Write-Host "  output/                         (all 9+ generated documents)" -ForegroundColor Gray
Write-Host "  backend/__pycache__/            (Python bytecode)" -ForegroundColor Gray
Write-Host "  backend/engines/__pycache__/    (Python bytecode)" -ForegroundColor Gray
Write-Host "  backend/data/drafts/            (auto-saved drafts)" -ForegroundColor Gray
Write-Host ""
Write-Host "Then will FORCE-PUSH to:" -ForegroundColor White
foreach ($r in $remoteMap.Keys) {
  Write-Host "  $($r.PadRight(10)) -> $($remoteMap[$r])" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Local files on disk are NOT deleted - only stripped from git." -ForegroundColor DarkGray
Write-Host ""
$confirm = Read-Host "Type 'SCRUB' (all caps) to proceed, anything else to abort"
if ($confirm -ne 'SCRUB') {
  Write-Host "Aborted." -ForegroundColor Yellow
  exit 0
}
Write-Host ""

# ─── 4. BACKUP .git BEFORE DESTRUCTION ─────────────────────────────
$BackupDir = Join-Path $ProjectRoot ".git-backup-$Timestamp"
Write-Host "> Backing up .git to: $BackupDir" -ForegroundColor Cyan
Copy-Item -Path (Join-Path $ProjectRoot ".git") -Destination $BackupDir -Recurse -Force
Write-Host "  [OK] backup made (delete it once you've confirmed everything works)" -ForegroundColor Green
Write-Host ""

# ─── 5. RUN filter-repo ────────────────────────────────────────────
Write-Host "> Running git filter-repo..." -ForegroundColor Cyan
git filter-repo `
  --force `
  --invert-paths `
  --path output `
  --path backend/__pycache__ `
  --path backend/engines/__pycache__ `
  --path backend/data/drafts
if ($LASTEXITCODE -ne 0) {
  Write-Host "[FAIL] filter-repo errored. .git-backup-$Timestamp has the original. Restore with:" -ForegroundColor Red
  Write-Host "  Remove-Item .git -Recurse -Force; Move-Item .git-backup-$Timestamp .git" -ForegroundColor Yellow
  exit 1
}
Write-Host "  [OK] history rewritten" -ForegroundColor Green
Write-Host ""

# ─── 6. RESTORE REMOTES ────────────────────────────────────────────
Write-Host "> Restoring remotes..." -ForegroundColor Cyan
foreach ($r in $remoteMap.Keys) {
  git remote add $r $remoteMap[$r]
  Write-Host "  [OK] $r -> $($remoteMap[$r])" -ForegroundColor Green
}
Write-Host ""

# ─── 7. FORCE PUSH TO ALL REMOTES ──────────────────────────────────
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host "> Force-pushing $branch to all remotes..." -ForegroundColor Cyan
foreach ($r in $remoteMap.Keys) {
  Write-Host "  > git push --force-with-lease $r $branch" -ForegroundColor DarkGray
  git push --force $r $branch
  if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] pushed to $r" -ForegroundColor Green
  } else {
    Write-Host "  [FAIL] push to $r failed (exit $LASTEXITCODE)" -ForegroundColor Red
  }
  $global:LASTEXITCODE = 0
}
Write-Host ""

# ─── 8. DONE ───────────────────────────────────────────────────────
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  SCRUB COMPLETE" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Verify on the web:" -ForegroundColor White
foreach ($r in $remoteMap.Keys) {
  Write-Host "  $r : $($remoteMap[$r])" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Once verified, delete the backup:" -ForegroundColor White
Write-Host "  Remove-Item .git-backup-$Timestamp -Recurse -Force" -ForegroundColor Gray
Write-Host ""
