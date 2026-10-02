# Builds the Windows installer: PyInstaller output -> Inno Setup.
# Run from anywhere:  pwsh packaging\windows\build_installer.ps1
# Requires Inno Setup 6.3+ (winget install JRSoftware.InnoSetup).

param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

if (-not $Python) {
    $venv = Join-Path $root ".venv\Scripts\python.exe"
    $Python = if (Test-Path $venv) { $venv } else { "python" }
}

$candidates = @(
    @(
        (Get-Command iscc -ErrorAction SilentlyContinue).Source,
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }
)
if (-not $candidates) {
    throw "Inno Setup not found. Install it with: winget install JRSoftware.InnoSetup"
}
$iscc = $candidates[0]

$version = & $Python -c "import sys; sys.path.insert(0, 'src'); import keyenroll; print(keyenroll.__version__)"
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "x64" }

Remove-Item Env:KEYENROLL_NO_UAC -ErrorAction SilentlyContinue
& $Python -m PyInstaller packaging\keyenroll.spec --noconfirm --log-level WARN
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

& $iscc "/DAppVersion=$version" "/DArch=$arch" packaging\windows\installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }

Get-ChildItem dist\installer\*.exe | Select-Object Name, @{n = "MB"; e = { [math]::Round($_.Length / 1MB, 1) } }
