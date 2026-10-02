# publish-public.ps1 - Publie le kit et ses sous-modules vers l'org publique.
#
# Methode : SNAPSHOT. Chaque repo public recoit un historique NEUF (orphan
# branch, un seul commit "Public release") : zero fuite d'historique prive.
# Le script est idempotent : republier = pousser un nouveau snapshot.
#
# Usage :  powershell -File tools\publish-public.ps1 [-Org art-qalam-fr] [-DryRun]
param(
    [string]$Org = "art-qalam-fr",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$KitRoot = Split-Path -Parent $PSScriptRoot
$Tmp = Join-Path $env:TEMP ("hephaistos-pub-" + [guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Path $Tmp -Force | Out-Null

$TextExt = @(".md",".json",".mjs",".js",".cjs",".ts",".ps1",".txt",".html",".css",".yaml",".yml",".gitmodules")

function Sanitize-Tree([string]$dir) {
    Get-ChildItem -Path $dir -Recurse -File | Where-Object {
        ($TextExt -contains $_.Extension -or $_.Extension -eq "") -and $_.Length -lt 1MB -and $_.FullName -notmatch "\\.git\\"
    } | ForEach-Object {
        $raw = [IO.File]::ReadAllText($_.FullName)
        $new = $raw.Replace("github.com/art-qalam-fr", "github.com/$Org")
        $new = $new.Replace("art-qalam-fr", $Org).Replace("art-qalam-fr", $Org)
        $new = $new.Replace("art-qalam-fr", $Org)
        if ($new -ne $raw) { [IO.File]::WriteAllText($_.FullName, $new) }
    }
}

function Publish-Snapshot([string]$srcPath, [string]$repoName) {
    Write-Host "=== $repoName" -ForegroundColor Cyan
    $work = Join-Path $Tmp $repoName
    git clone --quiet --no-hardlinks $srcPath $work 2>&1 | Out-Null
    Push-Location $work
    try {
        git checkout --quiet --orphan public-release
        Sanitize-Tree $work
        git add -A
        git -c user.name="art-qalam-fr" -c user.email="147002352+art-qalam-fr@users.noreply.github.com" commit --quiet -m "Public release - composant du Hephaistos-Kit"
        $sha = (git rev-parse HEAD).Trim()
        if ($DryRun) { Write-Host "  [dry-run] sha=$sha"; return $sha }
        $exists = $false
        try { gh repo view "$Org/$repoName" --json name 2>&1 | Out-Null; $exists = ($LASTEXITCODE -eq 0) } catch {}
        if (-not $exists) { gh repo create "$Org/$repoName" --public | Out-Null }
        git push --force --quiet "https://github.com/$Org/$repoName.git" "public-release:main"
        Write-Host "  -> https://github.com/$Org/$repoName ($sha)" -ForegroundColor Green
        return $sha
    } finally { Pop-Location }
}

# 1) Composants : chaque sous-module devient un repo public independant
$map = @{}
$components = Get-ChildItem -Path (Join-Path $KitRoot "mcp\servers") -Directory
$components += Get-Item (Join-Path $KitRoot "cli\opencli-cookies")
foreach ($c in $components) {
    $map[$c.Name] = Publish-Snapshot $c.FullName $c.Name
}

# 2) Le kit : snapshot + gitlinks reparés vers les SHA publics
$kitWork = Join-Path $Tmp "Hephaistos-Kit"
git clone --quiet --no-hardlinks $KitRoot $kitWork 2>&1 | Out-Null
Push-Location $kitWork
try {
    git checkout --quiet --orphan public-release
    Sanitize-Tree $kitWork
    # Exclusions publiques : docs internes qui restent prives
    $excl = Join-Path $KitRoot "tools\publish-public.exclude.txt"
    if (Test-Path $excl) {
        Get-Content $excl | Where-Object { $_ -and -not $_.StartsWith("#") } | ForEach-Object {
            $p = Join-Path $kitWork $_.Trim()
            if (Test-Path $p) { Remove-Item -Recurse -Force $p }
        }
    }
    git add -A
    foreach ($name in $map.Keys) {
        $rel = if ($name -eq "opencli-cookies") { "cli/opencli-cookies" } else { "mcp/servers/$name" }
        git update-index --cacheinfo "160000,$($map[$name]),$rel"
    }
    git -c user.name="art-qalam-fr" -c user.email="147002352+art-qalam-fr@users.noreply.github.com" commit --quiet -m "Public release - Hephaistos-Kit"
    if (-not $DryRun) {
        $exists = $false
        try { gh repo view "$Org/Hephaistos-Kit" --json name 2>&1 | Out-Null; $exists = ($LASTEXITCODE -eq 0) } catch {}
        if (-not $exists) { gh repo create "$Org/Hephaistos-Kit" --public | Out-Null }
        git push --force --quiet "https://github.com/$Org/Hephaistos-Kit.git" "public-release:main"
    }
    Write-Host "=== Hephaistos-Kit -> https://github.com/$Org/Hephaistos-Kit" -ForegroundColor Green
} finally { Pop-Location }

if (-not $DryRun) { Write-Host "`nPublication terminee. Verifier : git clone --recurse-submodules https://github.com/$Org/Hephaistos-Kit" }
