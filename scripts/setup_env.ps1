param(
    [switch]$SkipUI,
    [switch]$SkipDev
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Expected virtual environment python at $pythonExe. Create the .venv first."
}

$extras = @()
if (-not $SkipUI) {
    $extras += "ui"
}
if (-not $SkipDev) {
    $extras += "dev"
}

$target = if ($extras.Count -gt 0) { ".[{0}]" -f ($extras -join ",") } else { "." }

& $pythonExe -m pip install -e $target
exit $LASTEXITCODE
