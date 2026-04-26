# SOVEREIGN DOCS - DEPLOY
param(
    [string]$Message = "feat: BRIEF tab daily/weekly/custom engine, LIBRARY trace grouping, delete API, Vault offline graceful"
)

$ProjectRoot = "C:\Veritas_Lab\veritas-docs"
$Stamp = Get-Date -Format "yyyy-MM-dd_HHmm"

Set-Location $ProjectRoot

Write-Host "==========================================================="
Write-Host "SOVEREIGN DOCS - DEPLOY"
Write-Host "Project: $ProjectRoot"
Write-Host "Stamp:   $Stamp"
Write-Host "==========================================================="

# Stage all changes
git add .
git commit -m $Message

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Nothing to commit or commit failed"
} else {
    Write-Host ""
    Write-Host "Pushing to GitHub..."
    git push origin master
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] GitHub push complete"
    } else {
        Write-Host "[!] GitHub push failed"
    }
}

# Backup to G Drive
$BackupDest = "G:\My Drive\Desktop\veritas-docs-backup-$Stamp"
Write-Host ""
Write-Host "Backing up to: $BackupDest"

if (Test-Path "G:\My Drive\Desktop") {
    robocopy . $BackupDest /MIR /XD node_modules .git dist output renderer node_modules /XF "*.pyc" "__pycache__" "*.log" "deploy.ps1" /NP /NFL /NDL /NC /NS /NJH /NJS
    if ($LASTEXITCODE -le 7) {
        Write-Host "[OK] backed up"
    } else {
        Write-Host "[!] backup failed (exit $LASTEXITCODE)"
    }
} else {
    Write-Host "[!] G:\My Drive\Desktop not found - skipping backup"
}

Write-Host ""
Write-Host "==========================================================="
Write-Host "DONE"
Write-Host "==========================================================="
