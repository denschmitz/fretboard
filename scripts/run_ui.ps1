param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$streamlitExe = Join-Path $repoRoot ".venv\Scripts\streamlit.exe"
$appPath = Join-Path $repoRoot "src\fretboard\ui\streamlit_app.py"

if (-not (Test-Path $streamlitExe)) {
    throw "Expected Streamlit at $streamlitExe. Run scripts/setup_env.ps1 first."
}

& $streamlitExe run $appPath @Args
exit $LASTEXITCODE
