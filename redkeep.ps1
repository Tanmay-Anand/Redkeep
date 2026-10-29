<#
  Redkeep PowerShell wrapper (Windows).

  Nothing here idles in the background: the Kali toolbox runs with `run --rm`
  (ephemeral) and the optional DefectDojo hub only runs when you start it.
  The `free-resources` command stops everything AND shuts the WSL2 backend down
  so Docker stops holding RAM for the rest of your system.

  Usage:
    ./redkeep.ps1 lab-build
    ./redkeep.ps1 lab-up
    ./redkeep.ps1 scan [quick|full|network|web|api]
    ./redkeep.ps1 network | web | api | report | shell
    ./redkeep.ps1 hub-up | hub-down | bootstrap
    ./redkeep.ps1 lab-down | down-all | free-resources
#>
param(
  [Parameter(Position = 0)][string]$Command = "help",
  [Parameter(Position = 1)][string]$Profile = "quick"
)

$ErrorActionPreference = "Stop"
$Lab = @("compose", "-f", "lab/docker-compose.yml")
$Hub = @("compose", "-f", "hub/docker-compose.yml")
$Targets = @("target-db", "target-api", "target-platform", "target-admin", "target-reports", "target-ui")

function Lab { docker @Lab @args }
function Hub { docker @Hub @args }

switch ($Command) {
  "lab-build" { Lab build }
  "lab-up"    { Lab up -d @Targets }
  "lab-down"  { Lab down }
  "lab-reset" { Lab run --rm kali bash lab/target/reset.sh }

  "scan"      { Lab run --rm kali vapt run --profile $Profile }
  "network"   { Lab run --rm kali vapt network }
  "web"       { Lab run --rm kali vapt web }
  "api"       { Lab run --rm kali vapt api }
  "report"    { Lab run --rm kali vapt report }
  "shell"     { Lab run --rm kali bash }

  "hub-up"    { Hub up -d }
  "hub-down"  { Hub down }
  "bootstrap" { Lab run --rm kali python3 hub/config/bootstrap.py --config config.yaml }

  "down-all"  { Lab down; Hub down }

  "free-resources" {
    Write-Host "[redkeep] Stopping all containers..." -ForegroundColor Cyan
    try { Lab down } catch {}
    try { Hub down } catch {}
    Write-Host "[redkeep] Shutting down the WSL2 backend to free RAM..." -ForegroundColor Cyan
    try { wsl --shutdown } catch { Write-Host "wsl --shutdown failed (is WSL installed?)" -ForegroundColor Yellow }
    Write-Host "[redkeep] Done. Also quit Docker Desktop if you want it fully idle." -ForegroundColor Green
  }

  default {
    Write-Host "Redkeep commands:" -ForegroundColor Cyan
    Write-Host "  lab-build  lab-up  lab-down  lab-reset"
    Write-Host "  scan [quick|full|network|web|api]   network  web  api  report  shell"
    Write-Host "  hub-up  hub-down  bootstrap"
    Write-Host "  down-all   free-resources   (free-resources also runs 'wsl --shutdown')"
  }
}
