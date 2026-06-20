# =============================================================================
# MediaSense v1.0 Rollback Script (PowerShell)
# =============================================================================
# Usage:
#   Open PowerShell in the project root and run:
#   .\scripts\rollback-v1.0.ps1
#
# What this does:
#   1. Restores ALL project files to the exact v1.0 state
#   2. Creates a new forward commit (safe — no force-push to shared history)
#   3. Pushes to GitHub → triggers Railway (backend) and Vercel (frontend) redeploys
#   4. Prints post-rollback checklist
#
# =============================================================================

$V1_COMMIT = "06f0f042f2b216c26be7eb1762732fa7b7fe17df"
$V1_TAG    = "v1.0"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  MediaSense Rollback → $V1_TAG" -ForegroundColor Cyan
Write-Host "  Commit: $V1_COMMIT" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# --- Safety check: no uncommitted changes ---
$status = git status --porcelain
if ($status) {
    Write-Host "ERROR: Uncommitted changes detected. Stash or commit them first." -ForegroundColor Red
    Write-Host $status
    exit 1
}

# --- Confirm ---
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  • Restore ALL files to v1.0 state (new forward commit)"
Write-Host "  • Push to GitHub (triggers Railway + Vercel auto-redeploy)"
Write-Host ""
$confirm = Read-Host "Type 'yes' to proceed"
if ($confirm -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "[1/4] Fetching tags from origin..." -ForegroundColor Green
git fetch --tags origin
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: git fetch" -ForegroundColor Red; exit 1 }

Write-Host "[2/4] Restoring files to $V1_TAG state..." -ForegroundColor Green
# Check out every file from the v1.0 tag into the working tree.
# This is NOT a force-push — it creates a new commit on top of current HEAD.
git checkout $V1_TAG -- .
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: git checkout $V1_TAG" -ForegroundColor Red; exit 1 }

Write-Host "[3/4] Committing rollback..." -ForegroundColor Green
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git add -A
git commit -m "rollback: revert to v1.0 ($timestamp)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing to commit — working tree already matches v1.0." -ForegroundColor Yellow
}

Write-Host "[4/4] Pushing to GitHub (triggers Railway + Vercel redeploy)..." -ForegroundColor Green
git push origin master
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: git push" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ROLLBACK INITIATED SUCCESSFULLY" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "POST-ROLLBACK CHECKLIST:" -ForegroundColor Yellow
Write-Host "  [ ] Railway: https://railway.app — confirm backend redeployed"
Write-Host "  [ ] Vercel:  https://vercel.com   — confirm frontend redeployed"
Write-Host "  [ ] Test:    Open MediaSense, log in, check pipeline status banner"
Write-Host "  [ ] Test:    Overview dashboard loads (KPIs, trend chart, map)"
Write-Host "  [ ] Test:    Mention Explorer — filter + CSV export work"
Write-Host "  [ ] Test:    Brand management, user management accessible"
Write-Host ""
Write-Host "If Railway did NOT auto-redeploy:" -ForegroundColor Cyan
Write-Host "  Go to Railway project → Deployments → click 'Deploy' on latest"
Write-Host ""
Write-Host "If Vercel did NOT auto-redeploy:" -ForegroundColor Cyan
Write-Host "  Run: vercel --prod   (from frontend/ directory)"
Write-Host "  Or:  Vercel dashboard → Deployments → Redeploy"
Write-Host ""
