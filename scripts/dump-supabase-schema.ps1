# =============================================================================
# Supabase Schema Dump — v1.0 baseline capture
# =============================================================================
# Run this ONCE to capture a schema snapshot of the v1.0 database state.
# The output file (supabase-schema-v1.0.sql) is NOT auto-committed to git
# (it may contain connection info). Store it securely alongside this project.
#
# Prerequisites:
#   - pg_dump installed (comes with PostgreSQL client tools)
#   - SUPABASE_DB_URL set in environment or .env
#   - Or: run from Supabase Dashboard → SQL Editor → copy schema manually
#
# Usage:
#   .\scripts\dump-supabase-schema.ps1
# =============================================================================

$outputFile = "scripts/supabase-schema-v1.0.sql"

# Try to load SUPABASE_DB_URL from .env if not in environment
if (-not $env:SUPABASE_DB_URL) {
    $envFile = ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "^SUPABASE_DB_URL=(.+)$") {
                $env:SUPABASE_DB_URL = $matches[1].Trim('"').Trim("'")
            }
        }
    }
}

if (-not $env:SUPABASE_DB_URL) {
    Write-Host "ERROR: SUPABASE_DB_URL not set." -ForegroundColor Red
    Write-Host ""
    Write-Host "Set it via:" -ForegroundColor Yellow
    Write-Host '  $env:SUPABASE_DB_URL = "postgresql://postgres:[password]@[host]:5432/postgres"'
    Write-Host ""
    Write-Host "Or run this SQL in Supabase Dashboard SQL Editor to view schema:" -ForegroundColor Cyan
    Write-Host "  SELECT table_name, column_name, data_type FROM information_schema.columns"
    Write-Host "  WHERE table_schema = 'public' ORDER BY table_name, ordinal_position;"
    exit 1
}

Write-Host "Dumping Supabase schema to $outputFile ..." -ForegroundColor Green

pg_dump `
  --schema-only `
  --no-owner `
  --no-acl `
  --schema=public `
  $env:SUPABASE_DB_URL `
  -f $outputFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "Schema saved to: $outputFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Store this file securely. To restore:" -ForegroundColor Yellow
    Write-Host '  psql $env:SUPABASE_DB_URL < scripts/supabase-schema-v1.0.sql'
} else {
    Write-Host "pg_dump failed. Check your SUPABASE_DB_URL and pg_dump installation." -ForegroundColor Red
}
