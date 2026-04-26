# ─────────────────────────────────────────────────────────────────────
#  SOVEREIGN DOCS — deploy script
#  • git add + commit
#  • Push to ALL configured remotes (github, codeberg, etc.)
#  • Backup whole project to G:\My Drive\Desktop\<timestamp>\
# ─────────────────────────────────────────────────────────────────────
[CmdletBinding()]
param(
  [string]$Message = "feat: BRIEF preview/types, LIBRARY trace grouping + delete, EXTRACT (OCR), FORGE (ASCII)",
  [switch]$NoCommit,
  [switch]$NoPush,
  [switch]$NoBackup
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp   = Get-Date -Format 'yyyy-MM-dd_HHmm'

Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  SOVEREIGN DOCS - DEPLOY" -ForegroundColor Yellow
Write-Host "  Project: $ProjectRoot" -ForegroundColor DarkGray
Write-Host "  Stamp:   $Timestamp" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

# ─── 1. GIT COMMIT ──────────────────────────────────────────────────
if (-not $NoCommit) {
  Write-Host "> git add ." -ForegroundColor Cyan
  git add . | Out-Null

  $staged = git diff --cached --name-only
  if (-not $staged) {
    Write-Host "  (nothing to commit - working tree clean)" -ForegroundColor DarkGray
  } else {
    Write-Host "> git commit -m `"$Message`"" -ForegroundColor Cyan
    git commit -m $Message | Out-Null
    Write-Host "  [OK] committed:" -ForegroundColor Green
    $staged | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
  }
} else {
  Write-Host "> Skipping git commit (-NoCommit)" -ForegroundColor DarkGray
}
Write-Host ""

# ─── 2. PUSH TO ALL REMOTES ─────────────────────────────────────────
if (-not $NoPush) {
  $branch = (git rev-parse --abbrev-ref HEAD).Trim()
  $remotes = git remote
  if (-not $remotes) {
    Write-Host "> No git remotes configured - skipping push" -ForegroundColor Yellow
  } else {
    foreach ($remote in $remotes) {
      Write-Host "> git push $remote $branch" -ForegroundColor Cyan
      git push $remote $branch
      if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] pushed to $remote" -ForegroundColor Green
      } else {
        Write-Host "  [FAIL] push to $remote failed (exit $LASTEXITCODE)" -ForegroundColor Red
      }
      $global:LASTEXITCODE = 0
    }
  }
} else {
  Write-Host "> Skipping push (-NoPush)" -ForegroundColor DarkGray
}
Write-Host ""

# ─── 3. BACKUP TO G:\My Drive\Desktop ───────────────────────────────
if (-not $NoBackup) {
  $BackupRoot = 'G:\My Drive\Desktop'
  $BackupDir  = Join-Path $BackupRoot "veritas-docs-backup-$Timestamp"

  if (-not (Test-Path $BackupRoot)) {
    Write-Host "> G:\My Drive\Desktop not available - skipping backup" -ForegroundColor Yellow
  } else {
    Write-Host "> Backing up to: $BackupDir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    # Exclude only what is genuinely transient or huge.
    # NEVER exclude `renderer` — that's where the UI lives.
    robocopy $ProjectRoot $BackupDir `
      /E `
      /XD node_modules dist .git __pycache__ .venv output `
      /XF *.log *.pyc `
      /NFL /NDL /NJH /NJS /NP /NS /NC | Out-Null
    if ($LASTEXITCODE -lt 8) {
      $size = (Get-ChildItem -Path $BackupDir -Recurse -File -ErrorAction SilentlyContinue |
               Measure-Object Length -Sum).Sum
      $sizeMB = [math]::Round($size / 1MB, 2)
      Write-Host "  [OK] backed up ($sizeMB MB)" -ForegroundColor Green
    } else {
      Write-Host "  [FAIL] robocopy exit $LASTEXITCODE" -ForegroundColor Red
    }
    $global:LASTEXITCODE = 0
  }
} else {
  Write-Host "> Skipping backup (-NoBackup)" -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  DONE" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
