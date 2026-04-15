[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$pythonExe = Join-Path $backendDir "venv\\Scripts\\python.exe"
$nodeDir = "C:\\Users\\25362\\Desktop\\tools\\node-v24.14.1-win-x64"
$npmCmd = Join-Path $nodeDir "npm.cmd"

function Assert-PathExists {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "$Label not found: $Path"
    }
}

function Get-ListeningProcessId {
    param([int]$Port)

    $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $connection) {
        return $null
    }
    return $connection.OwningProcess
}

function Start-BackendWindow {
    $existingProcess = Get-ListeningProcessId -Port 5000
    if ($existingProcess) {
        Write-Host "Backend already running: http://127.0.0.1:5000 (PID: $existingProcess)" -ForegroundColor Yellow
        return
    }

    $command = @"
Set-Location -LiteralPath '$backendDir'
`$host.UI.RawUI.WindowTitle = 'AIGC Risk Backend'
`$env:PYTHONPATH = '$backendDir'
& '$pythonExe' 'app.py'
"@

    $process = Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) `
        -PassThru

    Write-Host "Backend window opened (PID: $($process.Id))" -ForegroundColor Green
}

function Start-FrontendWindow {
    $existingProcess = Get-ListeningProcessId -Port 5173
    if ($existingProcess) {
        Write-Host "Frontend already running: http://127.0.0.1:5173 (PID: $existingProcess)" -ForegroundColor Yellow
        return
    }

    $command = @"
Set-Location -LiteralPath '$frontendDir'
`$host.UI.RawUI.WindowTitle = 'AIGC Risk Frontend'
`$env:PATH = '$nodeDir;' + `$env:PATH
& '$npmCmd' 'run' 'dev' '--' '--host' '127.0.0.1' '--port' '5173'
"@

    $process = Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $command) `
        -PassThru

    Write-Host "Frontend window opened (PID: $($process.Id))" -ForegroundColor Green
}

Assert-PathExists -Path $pythonExe -Label "Backend Python"
Assert-PathExists -Path $npmCmd -Label "Frontend npm"
Assert-PathExists -Path $backendDir -Label "Backend directory"
Assert-PathExists -Path $frontendDir -Label "Frontend directory"

Write-Host "Starting AIGC risk system..." -ForegroundColor Cyan

Start-BackendWindow
Start-Sleep -Seconds 2
Start-FrontendWindow

Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend: http://127.0.0.1:5000"
Write-Host ""
Write-Host "Close the two PowerShell windows to stop the services." -ForegroundColor DarkGray
