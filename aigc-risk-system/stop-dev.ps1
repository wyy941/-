[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ports = @(5000, 5173)
$stopped = New-Object System.Collections.Generic.List[string]

function Get-ProcessMap {
    $items = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    $map = @{}
    foreach ($item in $items) {
        $map[$item.ProcessId] = $item
    }
    return $map
}

function Add-ProcessTree {
    param(
        [int]$ProcessId,
        [hashtable]$ProcessMap,
        [System.Collections.Generic.HashSet[int]]$Collector
    )

    if (-not $ProcessId) {
        return
    }

    if (-not $ProcessMap.ContainsKey($ProcessId)) {
        return
    }

    if (-not $Collector.Add($ProcessId)) {
        return
    }

    foreach ($child in $ProcessMap.Values) {
        if ($child.ParentProcessId -eq $ProcessId) {
            Add-ProcessTree -ProcessId $child.ProcessId -ProcessMap $ProcessMap -Collector $Collector
        }
    }
}

function Stop-ProcessSafe {
    param(
        [int]$ProcessId,
        [string]$Reason
    )

    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        return
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    $stopped.Add("$Reason (PID: $ProcessId)")
}

$processMap = Get-ProcessMap
$targets = New-Object 'System.Collections.Generic.HashSet[int]'

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        Add-ProcessTree -ProcessId $connection.OwningProcess -ProcessMap $processMap -Collector $targets
    }
}

foreach ($process in $processMap.Values) {
    $commandLine = $process.CommandLine
    if ([string]::IsNullOrWhiteSpace($commandLine)) {
        continue
    }

    if ($commandLine -like "*$repoRoot*" -and (
        $commandLine -like "*app.py*" -or
        $commandLine -like "*npm.cmd*run*dev*" -or
        $commandLine -like "*vite*"
    )) {
        Add-ProcessTree -ProcessId $process.ProcessId -ProcessMap $processMap -Collector $targets
    }
}

$orderedTargets = $targets.ToArray() | Sort-Object -Descending
foreach ($processId in $orderedTargets) {
    Stop-ProcessSafe -ProcessId $processId -Reason "Stopped service process"
}

Start-Sleep -Milliseconds 800

$remaining = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in $ports }

if ($stopped.Count -eq 0 -and -not $remaining) {
    Write-Host "No frontend or backend service process was found." -ForegroundColor Yellow
    exit 0
}

if ($stopped.Count -gt 0) {
    Write-Host "Stopped services:" -ForegroundColor Cyan
    foreach ($item in $stopped) {
        Write-Host "- $item"
    }
}

if ($remaining) {
    Write-Host "Some listeners are still active:" -ForegroundColor Yellow
    $remaining | Select-Object LocalPort, OwningProcess | Format-Table -HideTableHeaders
    exit 1
}
