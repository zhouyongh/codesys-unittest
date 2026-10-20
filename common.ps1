# common.ps1 - codesys-unittest shared helpers (dot-source).
# UTF-8 everywhere. No credentials in this file.

function Get-UtRoot {
    $PSScriptRoot
}

function Get-CodesysConnectHome {
    if ($env:CODESYS_CONNECT_HOME) { return $env:CODESYS_CONNECT_HOME }
    $sibling = Join-Path (Split-Path -Parent (Get-UtRoot)) "codesys-connect"
    if (Test-Path (Join-Path $sibling "cc.ps1")) { return $sibling }
    return $sibling
}

function Invoke-ConnectOp {
    # Thin wrapper over codesys-connect cc.ps1
    param(
        [string]$Command,
        [string[]]$Rest = @(),
        [hashtable]$Params = @{}
    )
    $connectHome = Get-CodesysConnectHome
    $cc = Join-Path $connectHome "cc.ps1"
    if (-not (Test-Path $cc)) {
        throw "codesys-connect not found at $cc (set CODESYS_CONNECT_HOME)"
    }
    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $cc, $Command) + $Rest
    foreach ($k in $Params.Keys) {
        $argList += @("-$k", [string]$Params[$k])
    }
    & powershell @argList
}

function Find-RtsInstall {
    # Locate CODESYSControlService.exe + SoftMotion cfg
    if ($env:CODESYS_UNITTEST_RTS_EXE -and (Test-Path $env:CODESYS_UNITTEST_RTS_EXE)) {
        $exe = $env:CODESYS_UNITTEST_RTS_EXE
        $dir = Split-Path -Parent $exe
        return [pscustomobject]@{
            Exe = $exe
            Dir = $dir
            SoftMotionCfg = Join-Path $dir "CODESYSSoftMotion.cfg"
            ControlCfg = Join-Path $dir "CODESYSControl.cfg"
        }
    }
    $bases = @()
    foreach ($v in @(
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        'C:\Program Files',
        'C:\Program Files (x86)'
    )) {
        if ($v -and (Test-Path $v) -and ($bases -notcontains $v)) { $bases += $v }
    }
    $candidates = @()
    foreach ($base in $bases) {
        Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like "CODESYS 3.5*" } | ForEach-Object {
                $exe = Join-Path $_.FullName "GatewayPLC\CODESYSControlService.exe"
                if (Test-Path $exe) {
                    $dir = Split-Path -Parent $exe
                    $candidates += [pscustomobject]@{
                        Exe = $exe
                        Dir = $dir
                        SoftMotionCfg = Join-Path $dir "CODESYSSoftMotion.cfg"
                        ControlCfg = Join-Path $dir "CODESYSControl.cfg"
                        InstallName = $_.Name
                    }
                }
            }
    }
    if ($candidates.Count -eq 0) { throw "No CODESYSControlService.exe found. Set CODESYS_UNITTEST_RTS_EXE." }
    # prefer one that has SoftMotion cfg
    $sm = $candidates | Where-Object { Test-Path $_.SoftMotionCfg } | Select-Object -First 1
    if ($sm) { return $sm }
    return $candidates[0]
}

function Test-PortOpen {
    param([string]$Address = "127.0.0.1", [int]$Port = 11740)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect($Address, $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(1000, $false)
        if ($ok -and $client.Connected) { $client.Close(); return $true }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

function Get-RtsProcess {
    # The soft-PLC process (not the tray).
    Get-Process -Name "CODESYSControlService" -ErrorAction SilentlyContinue
}

function Ensure-Runtime {
    param(
        [string]$Address = "127.0.0.1",
        [int]$Port = 11740,
        [int]$TimeoutSec = 30,
        [switch]$SoftMotion,
        [int]$MaxAgeHours = 2
    )
    $rts = Find-RtsInstall
    $cfg = if ($SoftMotion -or (Test-Path $rts.SoftMotionCfg)) { $rts.SoftMotionCfg } else { $rts.ControlCfg }
    if (-not (Test-Path $cfg)) { $cfg = $rts.ControlCfg }

    $proc = Get-RtsProcess | Select-Object -First 1
    $restart = $false
    if ($proc -and $proc.StartTime) {
        $age = (New-TimeSpan -Start $proc.StartTime -End (Get-Date)).TotalHours
        if ($MaxAgeHours -gt 0 -and $age -gt $MaxAgeHours) {
            Write-Host "WARN runtime age $([math]::Round($age,2))h exceeds ${MaxAgeHours}h (demo license); restarting"
            $restart = $true
        }
    }
    if ($restart -and $proc) {
        try { Stop-Process -Id $proc.Id -Force } catch {}
        Start-Sleep -Seconds 2
        $proc = $null
    }

    if (-not (Test-PortOpen -Address $Address -Port $Port)) {
        if (-not $proc) {
            $cfgName = Split-Path -Leaf $cfg
            Write-Host "starting runtime: $($rts.Exe) -d $cfgName (cwd $($rts.Dir))"
            # shortcut style: -d <cfg file name>, working dir = GatewayPLC
            Start-Process -FilePath $rts.Exe -ArgumentList @("-d", $cfgName) -WorkingDirectory $rts.Dir -WindowStyle Hidden | Out-Null
        }
        $deadline = (Get-Date).AddSeconds($TimeoutSec)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Seconds 1
            if (Test-PortOpen -Address $Address -Port $Port) { break }
        }
    }

    $proc = Get-RtsProcess | Select-Object -First 1
    $open = Test-PortOpen -Address $Address -Port $Port
    if (-not $open) {
        Write-Host "ERR runtime port ${Address}:${Port} not open (see $cfg)"
        return $false
    }
    $procId = if ($proc) { $proc.Id } else { 0 }
    Write-Host "OK runtime=1 pid=$procId port=$Port"
    return $true
}

function Stop-Runtime {
    $proc = Get-RtsProcess
    if ($proc) {
        foreach ($p in $proc) {
            try { Stop-Process -Id $p.Id -Force } catch {}
        }
        Start-Sleep -Seconds 2
    }
    $left = Get-RtsProcess
    if ($left) {
        Write-Host "ERR runtime still running (pid=$($left.Id -join ','))"
        return $false
    }
    Write-Host "OK runtime=0"
    return $true
}

function Write-Utf8File {
    param([string]$Path, [string]$Text)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Text, $utf8)
}

function Get-DefaultOutDir {
    param([string]$ProjectFile = "")
    if ($ProjectFile) {
        $dir = Join-Path (Split-Path -Parent $ProjectFile) "out"
        return $dir
    }
    Join-Path (Get-UtRoot) "out"
}
