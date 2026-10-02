#Requires -Version 5.1
<#
.SYNOPSIS
  Hephaistos-Kit - installateur de la stack MCP canonique.
.DESCRIPTION
  1. Initialise les sous-modules (mcp/servers/*) si presents dans le kit
  2. Build chaque serveur (npm / uv) sous ~/.hephaistos/servers
  3. Genere la config MCP de l'IDE cible depuis manifest.json
     avec les env resolus depuis ~/.hephaistos/env.local
.PARAMETER Ide
  devin | cursor | kilocode | antigravity | trae
.PARAMETER EnvFile
  Fichier KEY=VALUE (defaut: ~/.hephaistos/env.local) - JAMAIS commite.
.PARAMETER Tier
  standard | personal | all  (defaut: all)
.EXAMPLE
  .\install.ps1 -Ide devin
  .\install.ps1 -Ide cursor -Tier standard -SkipBuild
#>
[CmdletBinding()]
param(
  [ValidateSet('devin','cursor','kilocode','antigravity','trae')]
  [string]$Ide = 'devin',
  [string]$EnvFile = "$env:USERPROFILE\.hephaistos\env.local",
  [ValidateSet('standard','personal','all')]
  [string]$Tier = 'all',
  [string]$InstallRoot = "$env:USERPROFILE\.hephaistos\servers",
  [switch]$SkipBuild,
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$KitRoot   = Split-Path -Parent $PSScriptRoot
$Manifest  = Get-Content (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json

# --- 1. Env local (KEY=VALUE par ligne, # commentaires) ---
$envVars = @{}
if (Test-Path $EnvFile) {
  Get-Content $EnvFile | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
    $k,$v = $_ -split '=',2; $envVars[$k.Trim()] = $v.Trim()
  }
} else {
  Write-Warning "env.local absent ($EnvFile) - les secrets seront laisses en placeholder"
}

# --- 2. Submodules du kit ---
$serversDir = Join-Path $KitRoot 'mcp\servers'
if ((Test-Path (Join-Path $KitRoot '.gitmodules')) -and -not $SkipBuild) {
  Push-Location $KitRoot
  git submodule update --init --recursive
  Pop-Location
}

# --- 3. Build des serveurs 'submodule' ---
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
foreach ($s in $Manifest.servers) {
  if ($s.kind -ne 'submodule') { continue }
  if ($Tier -ne 'all' -and $s.tier -ne $Tier) { continue }
  $src = Join-Path $serversDir ($s.repo -split '/')[1]
  if (-not (Test-Path $src)) { $src = Join-Path $InstallRoot ($s.repo -split '/')[1] }
  if (-not (Test-Path $src)) {
    Write-Host "-> clone $($s.repo)" -ForegroundColor Cyan
    if (-not $DryRun) { git clone "https://github.com/$($s.repo).git" $src }
  }
  if ($SkipBuild) { continue }
  Write-Host "-> build $($s.name)  [$($s.build)]" -ForegroundColor Cyan
  if (-not $DryRun -and $s.build) {
    Push-Location $src
    try { Invoke-Expression $s.build } finally { Pop-Location }
  }
}

# --- 3b. Launchers (datacloud) vers ~/.devin/launchers ---
$launchersSrc = Join-Path $PSScriptRoot 'launchers'
if (Test-Path $launchersSrc) {
  $launchersDst = "$env:USERPROFILE\.devin\launchers"
  if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $launchersDst | Out-Null
    Copy-Item "$launchersSrc\*" $launchersDst -Force
  }
  Write-Host "-> launchers deployes -> $launchersDst (requiert l'extension datacloud de l'IDE)" -ForegroundColor Cyan
}

# --- 4. Resolution des placeholders ---
function Resolve-Value([string]$v) {
  $agentRepo = '<AGENTMEMORY_REPO>'
  if ($envVars['AGENTMEMORY_REPO']) { $agentRepo = $envVars['AGENTMEMORY_REPO'] }
  $r = $v -replace '\{INSTALL_ROOT\}', $InstallRoot `
          -replace '\{WORKSPACE\}', (Get-Location).Path `
          -replace '\{DEVIN_LAUNCHERS\}', "$env:USERPROFILE\.devin\launchers" `
          -replace '\{AGENTMEMORY_REPO\}', $agentRepo
  return $r
}

$config = [ordered]@{ mcpServers = [ordered]@{} }
foreach ($s in $Manifest.servers) {
  if ($Tier -ne 'all' -and $s.tier -ne $Tier) { continue }
  $entry = [ordered]@{}
  if ($s.kind -eq 'url') { $entry.url = $s.url }
  else {
    $entry.command = Resolve-Value $s.command
    if ($s.args) { $entry.args = @($s.args | ForEach-Object { Resolve-Value $_ }) }
  }
  $envBlock = [ordered]@{}
  foreach ($e in @($s.env_required) + @($s.env_optional)) {
    if (-not $e) { continue }
    if ($envVars[$e]) { $envBlock[$e] = $envVars[$e] } else { $envBlock[$e] = "`${$e}" }
  }
  if ($envBlock.Count) { $entry.env = $envBlock }
  $missing = @($s.env_required | Where-Object { -not $envVars[$_] })
  if ($missing) { Write-Warning "$($s.name): env manquantes -> $($missing -join ', ') (remplir $EnvFile)" }
  $config.mcpServers[$s.name] = $entry
}

# --- 5. Ecriture de la config IDE ---
$targets = @{
  devin        = "$env:USERPROFILE\.devin\mcp.json"
  cursor       = "$env:USERPROFILE\.cursor\mcp.json"
  kilocode     = "$env:USERPROFILE\.kilocode\mcp_config.json"
  antigravity  = "$env:USERPROFILE\.antigravity\mcp_config.json"
  trae         = "$env:USERPROFILE\.trae\mcp_config.json"
}
$out = $targets[$Ide]
$json = ($config | ConvertTo-Json -Depth 6)
if ($DryRun) { Write-Host "`n=== DRY RUN - config generee pour $Ide ===`n$json" ; return }
if (Test-Path $out) { Copy-Item $out "$out.bak-$(Get-Date -Format yyyyMMdd-HHmmss)" }
New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
$json | Set-Content $out -Encoding UTF8
Write-Host "`n[OK] Config $Ide ecrite -> $out (backup .bak si existante)" -ForegroundColor Green
