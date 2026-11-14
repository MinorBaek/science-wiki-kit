# Install science-wiki-kit on Windows: link the skills into your agent's skills folder and,
# optionally, scaffold a wiki.
#
#   .\install.ps1                  # link skills only
#   .\install.ps1 C:\Wikis\mine    # also scaffold a wiki (config, schema, templates, folders)
#
# Environment: CLAUDE_SKILLS_DIR overrides the skills folder (default: ~\.claude\skills).
# Uses directory junctions (no administrator rights needed). Never overwrites a real directory
# or an existing config; existing items are skipped with a notice.
param([string]$Target = "")

$ErrorActionPreference = "Stop"
$Kit = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { throw "Python 3.10 or newer is required" }
& $py.Source -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.10 or newer is required" }

Write-Host "1/3 Python package (optional: skills also work through junctions into this checkout)"
# Windows PowerShell 5.1 turns any stderr line of a native command into a terminating error under
# "Stop"; relax it just for pip, whose failure is not fatal here.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $py.Source -m pip install --quiet --user -e $Kit *> $null
$pipOk = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEap
if ($pipOk) { Write-Host "    installed wikikit in editable mode" }
else { Write-Host "    pip install skipped; the skills still find wikikit through the junctions" }

Write-Host "2/3 Skills -> $SkillsDir"
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
foreach ($d in Get-ChildItem -Directory (Join-Path $Kit "skills")) {
    $dest = Join-Path $SkillsDir $d.Name
    $item = Get-Item $dest -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType) {
        # Remove-Item on a junction throws in Windows PowerShell 5.1; this deletes the link only, never the target.
        [System.IO.Directory]::Delete($dest, $false)
        New-Item -ItemType Junction -Path $dest -Target $d.FullName | Out-Null
        Write-Host "    relinked $($d.Name)"
    } elseif ($item) {
        Write-Host "    SKIPPED $($d.Name): $dest exists and is not a link (move it aside to install)"
    } else {
        New-Item -ItemType Junction -Path $dest -Target $d.FullName | Out-Null
        Write-Host "    linked   $($d.Name)"
    }
}

Write-Host "3/3 Wiki scaffold"
if (-not $Target) {
    Write-Host "    skipped (pass a folder to scaffold a wiki: .\install.ps1 C:\Wikis\mine)"
} else {
    foreach ($f in "papers", "concepts", "methods", "books", "fields", "debates") {
        New-Item -ItemType Directory -Force -Path (Join-Path $Target "wiki\$f") | Out-Null
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $Target "templates") | Out-Null
    function Copy-IfMissing($src, $dst) { if (-not (Test-Path $dst)) { Copy-Item $src $dst } }
    $cfgPath = Join-Path $Target "wiki.config.json"
    if (-not (Test-Path $cfgPath)) {
        Copy-Item (Join-Path $Kit "examples\minimal\wiki.config.json") $cfgPath
        & $py.Source (Join-Path $Kit "tools\set_kit_dir.py") $cfgPath $Kit | Out-Null
    }
    Copy-IfMissing (Join-Path $Kit "docs\WIKI_SCHEMA.md") (Join-Path $Target "wiki\WIKI_SCHEMA.md")
    foreach ($t in Get-ChildItem (Join-Path $Kit "templates") -Filter *.md) {
        Copy-IfMissing $t.FullName (Join-Path $Target "templates\$($t.Name)")
    }
    foreach ($pair in @(@("index.md", "# Index"), @("log.md", "# Log"))) {
        $p = Join-Path $Target "wiki\$($pair[0])"
        if (-not (Test-Path $p)) { Set-Content -Path $p -Value $pair[1] -Encoding utf8 }
    }
    $hub = Join-Path $Target "wiki\fields\MOC_Wiki.md"
    if (-not (Test-Path $hub)) {
        $day = Get-Date -Format "yyyy-MM-dd"
        $hubText = "---`ntags: [MOC, hub]`ndate: $day`nstatus: active`ntype: MOC`n---`n`n# Hub`n`nThe top of the map. Link every field MOC here when you create it.`n`n## Fields`n"
        Set-Content -Path $hub -Value $hubText -Encoding utf8
    }
    Write-Host "    scaffolded $Target (edit wiki.config.json and the Taxonomy section of wiki\WIKI_SCHEMA.md)"
}

Write-Host "Done. Next: cd to your wiki folder and run: python $Kit\skills\wiki-lint\scripts\lint.py"
