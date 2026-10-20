# ut.ps1 - codesys-unittest CLI (xunit-style CODESYS unit tests)
# Usage:
#   ut.ps1 run [-Project <abs .project>] [-Mock] [-TimeoutSec 60] [-OutDir dir]
#              [-UserFile f | -User u] [-Address ip] [-Port n]
#              [-Device name] [-App name] [-Change Never|Try|Keep|Force]
#   ut.ps1 ensure-runtime [-Address ip] [-Port n] [-SoftMotion]
#   ut.ps1 stop-runtime
#   ut.ps1 report [-Results <results.json>] [-OutDir dir]
#
# Exit 0 = all passed; 1 = failures or ERR.
# All text I/O is UTF-8. Passwords are NEVER written to files by this script:
# pass -UserFile (preferred) or env CODESYS_UNITTEST_USER / CODESYS_UNITTEST_PASSWORD.
# Login never auto-escalates to Force (Force = full download / wipes variables).
param(
    [Parameter(Position = 0)]
    [string]$Command = "run",
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Rest = @(),
    [string]$Project = "",
    [string]$User = "",
    [string]$Password = "",
    [string]$UserFile = "",
    [string]$Device = "",
    [string]$App = "",
    [string]$Address = "127.0.0.1",
    [string]$Port = "11740",
    [string]$Change = "Never",
    [string]$TimeoutSec = "60",
    [string]$OutDir = "",
    [string]$Results = "",
    [string]$CodesysConnect = "",
    [string]$CodesysExe = "",
    [string]$CodesysProfile = "",
    [string]$ProjectInfo = "",
    [switch]$Mock,
    [switch]$SoftMotion
)
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
. (Join-Path $PSScriptRoot "common.ps1")
if ($CodesysConnect) { $env:CODESYS_CONNECT_HOME = $CodesysConnect }

$portNum = 11740
try { $portNum = [int]$Port } catch { $portNum = 11740 }
$timeoutNum = 60
try { $timeoutNum = [int]$TimeoutSec } catch { $timeoutNum = 60 }

if ($UserFile) {
    if (-not (Test-Path $UserFile)) { Write-Host "ERR UserFile not found: $UserFile"; exit 1 }
    $raw = Get-Content $UserFile -Encoding UTF8 | Where-Object { $_.Trim() -ne "" -and -not $_.Trim().StartsWith("#") }
    foreach ($line in $raw) {
        if ($line -match '^\s*user\s*[:=]\s*(.+)$') { $User = $matches[1].Trim() }
        elseif ($line -match '^\s*password\s*[:=]\s*(.+)$') { $Password = $matches[1].Trim() }
        elseif (-not $User) { $User = $line.Trim() }
        elseif (-not $Password) { $Password = $line.Trim() }
    }
    if (-not $User) { Write-Host "ERR UserFile has no user"; exit 1 }
}
# expose credentials to test_ops.py via env only - never via target.txt
if ($User)     { $env:CODESYS_UNITTEST_USER = $User }
if ($Password) { $env:CODESYS_UNITTEST_PASSWORD = $Password }

function Write-MockResults {
    param([string]$Path)
    $obj = @{
        done = $true
        caseCount = 3
        failCount = 1
        skipCount = 1
        durationSec = 0.25
        suiteName = "Sample"
        cases = @(
            @{ sName = "Sample.Test_add"; eStatus = 0; sMessage = ""; sSuite = "Sample" },
            @{ sName = "Sample.Test_sub"; eStatus = 1; sMessage = "lreal mismatch"; sSuite = "Sample" },
            @{ sName = "Sample.Test_slow"; eStatus = 2; sMessage = "not on this target"; sSuite = "Sample" }
        )
    }
    $json = $obj | ConvertTo-Json -Depth 6
    Write-Utf8File -Path $Path -Text $json
}

function Invoke-Report {
    param([string]$ResPath, [string]$Out)
    if (-not (Test-Path $ResPath)) {
        Write-Host "ERR results not found: $ResPath"
        return 1
    }
    if (-not $Out) { $Out = Get-DefaultOutDir -ProjectFile $Project }
    New-Item -ItemType Directory -Force -Path $Out | Out-Null
    $py = $env:MIMO_PYTHON
    if (-not $py) {
        $c = Get-Command python -ErrorAction SilentlyContinue
        if ($c) { $py = $c.Source }
    }
    if (-not $py) {
        Write-Host "ERR python not found (set MIMO_PYTHON or PATH)"
        return 1
    }
    # Out-Host so report text is not captured into the function return value
    & $py (Join-Path $PSScriptRoot "report.py") $ResPath $Out | Out-Host
    return [int]$LASTEXITCODE
}

function Invoke-RealRun {
    if (-not $Project) {
        Write-Host "ERR -Project required (or use -Mock)"
        return 1
    }
    if (-not (Test-Path $Project)) {
        Write-Host "ERR project not found: $Project"
        return 1
    }
    $out = if ($OutDir) { $OutDir } else { Get-DefaultOutDir -ProjectFile $Project }
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    $work = Join-Path $env:USERPROFILE ".codesys-unittest\work"
    New-Item -ItemType Directory -Force -Path $work | Out-Null
    $resJson = Join-Path $work "results.json"
    if (Test-Path $resJson) { Remove-Item $resJson -Force }

    # 1) runtime - only manage a local soft PLC. Real targets: pass -Address <ip>
    #    and the runtime is expected to already be running.
    $isLocal = ($Address -eq "127.0.0.1") -or ($Address -eq "localhost") -or ($Address -eq "::1")
    if ($isLocal) {
        $ok = Ensure-Runtime -Address $Address -Port $portNum -TimeoutSec 30 -SoftMotion:$SoftMotion
        if (-not $ok) { return 1 }
    } else {
        if (-not (Test-PortOpen -Address $Address -Port $portNum)) {
            Write-Host "ERR target ${Address}:${portNum} not reachable (start the PLC or check -Address/-Port)"
            return 1
        }
        Write-Host "OK target=1 address=$Address port=$portNum"
    }

    # 2) bind session via codesys-connect (credentials live there)
    # Prefer -UserFile so the password is not visible on the child command line.
    # Do NOT pass -Change here: that would persist it into the user's connect
    # session. test_ops.py uses its own change= (default Never) and never Force.
    $connParams = @{
        Project = $Project
        Address = $Address
        Port = $Port
    }
    if ($UserFile) { $connParams["UserFile"] = $UserFile }
    elseif ($User) {
        $connParams["User"] = $User
        if ($Password) { $connParams["Password"] = $Password }
    }
    if ($Device) { $connParams["Device"] = $Device }
    if ($App) { $connParams["App"] = $App }
    if ($ProjectInfo) { $connParams["ProjectInfo"] = $ProjectInfo }
    $connOut = Invoke-ConnectOp -Command connect -Params $connParams
    $connOut | ForEach-Object { Write-Host $_ }
    if (@($connOut | Where-Object { $_ -like "ERR*" }).Count -gt 0) { return 1 }

    # 3) run tests via CODESYS --runscript
    $target = Join-Path $work "ut_target.txt"
    $log = Join-Path $work "ut_log.txt"
    if (Test-Path $log) { Remove-Item $log -Force }
    $lines = @(
        "project=$Project",
        "result=$resJson",
        "log=$log",
        "address=$Address",
        "port=$Port",
        "change=$Change",
        "timeout_sec=$timeoutNum"
    )
    if ($Device) { $lines += "device=$Device" }
    if ($App) { $lines += "app=$App" }
    # credentials go via env (CODESYS_UNITTEST_USER/PASSWORD) or codesys-connect
    # session - NEVER as plaintext fields in target.txt
    Write-Utf8File -Path $target -Text (($lines -join "`n") + "`n")
    $env:CODESYS_UNITTEST_TARGET = $target

    $ops = Join-Path $PSScriptRoot "test_ops.py"
    $bat = Join-Path $work "run_ut.bat"
    $utf8Bom = New-Object System.Text.UTF8Encoding $true
    $exe = $CodesysExe
    $prof = $CodesysProfile
    $connectHome = Get-CodesysConnectHome
    $common = Join-Path $connectHome "common.ps1"
    if (-not (Test-Path $common)) {
        Write-Host "ERR cannot resolve CODESYS install (codesys-connect missing at $connectHome)"
        return 1
    }
    # resolve in a child scope so we do not clobber this script's functions
    $inst = & {
        param($common, $ex, $pr, $proj, $info)
        . $common
        Resolve-CodesysInstall -Exe $ex -ProfileName $pr -ProjectFile $proj -ProjectInfo $info
    } $common $CodesysExe $CodesysProfile $Project $ProjectInfo
    $exe = $inst.Exe
    $prof = $inst.Profile
    if (-not $exe) {
        Write-Host "ERR cannot resolve CODESYS install (set -CodesysExe)"
        return 1
    }
    if (-not $prof) {
        Write-Host "ERR cannot resolve CODESYS profile for $exe"
        return 1
    }
    [System.IO.File]::WriteAllLines($bat, @(
        "@echo off",
        "set CODESYS_UNITTEST_TARGET=$target",
        "`"$exe`" --noUI --profile=`"$prof`" --runscript=`"$ops`"",
        "exit /b %ERRORLEVEL%"
    ), $utf8Bom)

    # Host-level watchdog: kill the whole process tree on timeout so CODESYS
    # does not become an orphan (taskkill /T).
    $watchdogSec = [Math]::Max($timeoutNum + 30, 45)
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "`"$bat`"") -PassThru -WindowStyle Hidden
    $finished = $p.WaitForExit($watchdogSec * 1000)
    if (-not $finished) {
        Write-Host "ERR test_ops timed out after ${watchdogSec}s (see $log)"
        & taskkill /PID $p.Id /T /F 2>&1 | Out-Null
        # belt-and-suspenders: any leftover CODESYS.exe from this runscript
        Get-Process -Name "CODESYS" -ErrorAction SilentlyContinue | ForEach-Object {
            try { & taskkill /PID $_.Id /T /F 2>&1 | Out-Null } catch {}
        }
        if (Test-Path $log) { Get-Content $log -Encoding UTF8 | Select-Object -Last 20 }
        return 1
    }

    if (-not (Test-Path $resJson)) {
        Write-Host "ERR no results.json (see $log)"
        if (Test-Path $log) { Get-Content $log -Encoding UTF8 | Select-Object -Last 20 }
        return 1
    }
    Write-Host "results: $resJson"
    return (Invoke-Report -ResPath $resJson -Out $out)
}

# never leave credentials in the process environment longer than one command
function Clear-UtCredentials {
    Remove-Item Env:CODESYS_UNITTEST_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:CODESYS_UNITTEST_USER -ErrorAction SilentlyContinue
}

switch ($Command.ToLower()) {
    "ensure-runtime" {
        try {
            $ok = Ensure-Runtime -Address $Address -Port $portNum -TimeoutSec 30 -SoftMotion:$SoftMotion
            if ($ok) { exit 0 } else { exit 1 }
        } finally { Clear-UtCredentials }
    }
    "stop-runtime" {
        try {
            $ok = Stop-Runtime
            if ($ok) { exit 0 } else { exit 1 }
        } finally { Clear-UtCredentials }
    }
    "status" {
        try {
            $open = Test-PortOpen -Address $Address -Port $portNum
            $proc = Get-RtsProcess | Select-Object -First 1
            $procId = if ($proc) { $proc.Id } else { 0 }
            Write-Host "runtime_pid=$procId port_open=$open address=$Address port=$portNum"
            if ($open) { exit 0 } else { exit 1 }
        } finally { Clear-UtCredentials }
    }
    "run" {
        try {
            if ($Mock) {
                $out = if ($OutDir) { $OutDir } else { Get-DefaultOutDir }
                New-Item -ItemType Directory -Force -Path $out | Out-Null
                $resJson = Join-Path $out "results.json"
                Write-MockResults -Path $resJson
                Write-Host "mock results: $resJson"
                $rc = Invoke-Report -ResPath $resJson -Out $out
                if ($rc -eq 0) { exit 1 }
                exit $rc
            }
            $rc = Invoke-RealRun
            exit $rc
        } finally {
            Clear-UtCredentials
        }
    }
    "report" {
        try {
            $res = $Results
            if (-not $res) {
                $candidates = @(
                    (Join-Path (Get-DefaultOutDir -ProjectFile $Project) "results.json"),
                    (Join-Path $env:USERPROFILE ".codesys-unittest\work\results.json")
                )
                foreach ($c in $candidates) { if (Test-Path $c) { $res = $c; break } }
            }
            if (-not $res) {
                Write-Host "ERR no results.json (run first or pass -Results)"
                exit 1
            }
            $rc = Invoke-Report -ResPath $res -Out $(if ($OutDir) { $OutDir } else { Get-DefaultOutDir -ProjectFile $Project })
            exit $rc
        } finally {
            Clear-UtCredentials
        }
    }
    default {
        Clear-UtCredentials
        Write-Host "ERR unknown command: $Command (run|ensure-runtime|stop-runtime|status|report)"
        exit 1
    }
}
