$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$pythonCmd = "python"
& $pythonCmd -c "import typer, rich, PyInstaller" | Out-Null

& $pythonCmd -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name "Cakirin_Mekani" `
    Cakirin_Mekani.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build başarısız oldu."
}

Write-Host ""
Write-Host "EXE hazır: $projectRoot\dist\Cakirin_Mekani.exe"
