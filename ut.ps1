# ut.ps1 - codesys-unittest CLI (xunit-style CODESYS unit tests)
# Usage:
#   ut.ps1 run -Project <abs .project> [-UserFile f | -User u] [-Address ip] -Port n]
#              [-TimeoutSec 60] [-OutDir dir] [-Change Never|Keep]
#              [-Device name] [-App name] [-StartIfStopped] [-MaxAgeHours 2]
#   ut.ps1 run -Mock [-OutDir dir]          # green synthetic run (wiring check)
#   ut.ps1 run -MockFail [-OutDir dir]      # red synthetic run (report check)
#   ut.ps1 ensure-runtime [-Address ip] [-Port n] [-SoftMotion] [-MaxAgeHours 2]
#   ut.ps1 stop-runtime
#   ut.ps1 status [-Address ip] [-Port n]
#   ut.ps1 report [-Results <results.json>] [-OutDir dir]
#
# Exit 0 = all passed; 1 = failures, zero cases, or ERR.
# All text I/O is UTF-8. Passwords are NEVER written to files by this script:
# pass -UserFile (preferred) or env CODESYS_UNITTEST_USER / CODESYS_UNITTEST_PASSWORD.
# Login options are only Never|Keep. Force/Try are rejected: Force downloads and
# wipes variables; Try may online-change. run NEVER downloads - call
# codesys-connect `download` when logic changed, then run.
param(
    [Parameter(Position = 0)]
    [string]$Command = "run",
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
    [string]$MaxAgeHours = "2",
    [string]$OutDir = "",
    [string]$Results = "",
    [string]$CodesysConnect = "",
    [string]$CodesysExe = "",
    [string]$CodesysProfile = "",
    [string]$ProjectInfo = "",
    [switch]$Mock,
    [switch]$MockFail,
    [switch]$SoftMotion,
    [switch]$StartIfStopped
)
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
. (Join-Path $PSScriptRoot "common.ps1")
if ($CodesysConnect) { $env:CODESYS_CONNECT_HOME = $CodesysConnect }

# Login gate: this runner never downloads. Force = full download / wipes
# variables; Try may online-change. Both are codesys-connect's job.
$changeNorm = $Change.Trim()
if ($changeNorm -notin @("Never", "Keep")) {
    Write-Host "ERR -Change $changeNorm rejected. Use Never or Keep."
    Write-Host "     Force/Try download or online-change; call codesys-connect 'download' first."
    exit 1
}

$portNum = 11740
try { $portNum = [int]$Port } catch { $portNum = 11740 }
$timeoutNum = 60
try { $timeoutNum = [int]$TimeoutSec } catch { $timeoutNum = 60 }
$maxAgeNum = 2
try { $maxAgeNum = [int]$MaxAgeHours } catch { $maxAgeNum = 2 }

# per-run work dir so concurrent runs do not share results.json / target.txt
$runId = $PID
$work = Join-Path $env:USERPROFILE ".codesys-unittest\work-$runId"

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
    param([string]$Path, [switch]$Fail)
    $cases = @(
        @{ sName = "Sample.Test_add"; eStatus = 0; sMessage = ""; sSuite = "Sample" },
        @{ sName = "Sample.Test_sub"; eStatus = 0; sMessage = ""; sSuite = "Sample" },
        @{ sName = "Sample.Test_slow"; eStatus = 2; sMessage = "not on this target"; sSuite = "Sample" }
    )
    if ($Fail) {
        $cases[1].eStatus = 1
        $cases[1].sMessage = "lreal mismatch"
    }
    $obj = @{
        done = $true
        caseCount = $cases.Count
        failCount = @($cases | Where-Object { $_.eStatus -eq 1 }).Count
        skipCount = @($cases | Where-Object { $_.eStatus -eq 2 }).Count
        durationSec = 0.25
        suiteName = "Sample"
        cases = $cases
    }
    $json = $obj | ConvertTo-Json -Depth 6
    Write-Utf8File -Path $Path -Text $json
}

function Get-PythonExe {
    $py = $env:CODESYS_UNITTEST_PYTHON
    if (-not $py) { $py = $env:MIMO_PYTHON }   # legacy name, kept for compatibility
    if (-not $py) {
        $c = Get-Command python -ErrorAction SilentlyContinue
        if ($c) { $py = $c.Source }
    }
    return $py
}

function Invoke-Report {
    param([string]$ResPath, [string]$Out)
    if (-not (Test-Path $ResPath)) {
        Write-Host "ERR results not found: $ResPath"
        return 1
    }
    if (-not $Out) { $Out = Get-DefaultOutDir -ProjectFile $Project }
    New-Item -ItemType Directory -Force -Path $Out | Out-Null
    $py = Get-PythonExe
    if (-not $py) {
        Write-Host "ERR python 3.8+ not found (set CODESYS_UNITTEST_PYTHON or put python on PATH)"
        return 1
    }
    # Python writes UTF-8 bytes; tell it explicitly so a zh-CN console cannot
    # re-encode case names/messages.
    $env:PYTHONIOENCODING = "utf-8"
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
    New-Item -ItemType Directory -Force -Path $work | Out-Null
    $resJson = Join-Path $work "results.json"
    if (Test-Path $resJson) { Remove-Item $resJson -Force }

    # 1) runtime - only manage a local soft PLC. Real targets: pass -Address <ip>
    #    and the runtime is expected to already be running.
    $isLocal = ($Address -eq "127.0.0.1") -or ($Address -eq "localhost") -or ($Address -eq "::1")
    if ($isLocal) {
        $ok = Ensure-Runtime -Address $Address -Port $portNum -TimeoutSec 30 -SoftMotion:$SoftMotion -MaxAgeHours $maxAgeNum
        if (-not $ok) { return 1 }
    } else {
        if (-not (Test-PortOpen -Address $Address -Port $portNum)) {
            Write-Host "ERR target ${Address}:${portNum} not reachable (start the PLC or check -Address/-Port)"
            return 1
        }
        Write-Host "OK target=1 address=$Address port=$portNum"
    }

    # 2) run tests via CODESYS --runscript.
    #    No codesys-connect call here: that would login with its default
    #    change=Try (possible online change) and persist a session file. This
    #    runner only logs in with change=Never and never downloads.
    $target = Join-Path $work "ut_target.txt"
    $log = Join-Path $work "ut_log.txt"
    if (Test-Path $log) { Remove-Item $log -Force }
    $allowStart = $isLocal -or $StartIfStopped
    $lines = @(
        "project=$Project",
        "result=$resJson",
        "log=$log",
        "address=$Address",
        "port=$Port",
        "change=$changeNorm",
        "timeout_sec=$timeoutNum",
        "start_if_stopped=$(if ($allowStart) { 1 } else { 0 })"
    )
    if ($Device) { $lines += "device=$Device" }
    if ($App) { $lines += "app=$App" }
    # credentials go via env (CODESYS_UNITTEST_USER/PASSWORD) or the
    # codesys-connect session - NEVER as plaintext fields in target.txt
    Write-Utf8File -Path $target -Text (($lines -join "`n") + "`n")
    $env:CODESYS_UNITTEST_TARGET = $target

    $ops = Join-Path $PSScriptRoot "test_ops.py"
    $bat = Join-Path $work "run_ut.bat"
    $utf8Bom = New-Object System.Text.UTF8Encoding $true
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
        "set `"CODESYS_UNITTEST_TARGET=$target`"",
        "`"$exe`" --noUI --profile=`"$prof`" --runscript=`"$ops`"",
        "exit /b %ERRORLEVEL%"
    ), $utf8Bom)

    # Host-level watchdog: kill the whole process tree on timeout so CODESYS
    # does not become an orphan (taskkill /T). Never touch other CODESYS
    # processes - the user may have the IDE open.
    $watchdogSec = [Math]::Max($timeoutNum + 45, 60)
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "`"$bat`"") -PassThru -WindowStyle Hidden
    $finished = $p.WaitForExit($watchdogSec * 1000)
    if (-not $finished) {
        Write-Host "ERR test_ops timed out after ${watchdogSec}s (see $log)"
        & taskkill /PID $p.Id /T /F 2>&1 | Out-Null
        if (Test-Path $log) { Get-Content $log -Encoding UTF8 | Select-Object -Last 20 }
        return 1
    }

    if (-not (Test-Path $resJson)) {
        Write-Host "ERR no results.json (see $log)"
        if (Test-Path $log) { Get-Content $log -Encoding UTF8 | Select-Object -Last 20 }
        return 1
    }
    $outResults = Join-Path $out "results.json"
    Copy-Item -Path $resJson -Destination $outResults -Force
    Write-Host "results: $outResults"
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
            try { $ok = Ensure-Runtime -Address $Address -Port $portNum -TimeoutSec 30 -SoftMotion:$SoftMotion -MaxAgeHours $maxAgeNum }
            catch { Write-Host "ERR runtime: $($_.Exception.Message)"; $ok = $false }
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
            $proc = @(Get-Process -Name "CODESYSControlService" -ErrorAction SilentlyContinue) | Select-Object -First 1
            $procId = if ($proc) { $proc.Id } else { 0 }
            Write-Host "runtime_pid=$procId port_open=$open address=$Address port=$portNum"
            if ($open) { exit 0 } else { exit 1 }
        } finally { Clear-UtCredentials }
    }
    "run" {
        try {
            if ($Mock -or $MockFail) {
                $out = if ($OutDir) { $OutDir } else { Get-DefaultOutDir }
                New-Item -ItemType Directory -Force -Path $out | Out-Null
                $resJson = Join-Path $out "results.json"
                Write-MockResults -Path $resJson -Fail:$MockFail
                Write-Host "mock results: $resJson"
                $rc = Invoke-Report -ResPath $resJson -Out $out
                exit $rc
            }
            try {
                $rc = Invoke-RealRun
            } catch {
                Write-Host "ERR $($_.Exception.Message)"
                $rc = 1
            }
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
                    (Join-Path (Get-DefaultOutDir -ProjectFile $Project) "results.json")
                )
                foreach ($c in $candidates) { if (Test-Path $c) { $res = $c; break } }
                if (-not $res) {
                    # newest per-run work dir
                    $workRoot = Join-Path $env:USERPROFILE ".codesys-unittest"
                    $latest = Get-ChildItem $workRoot -Directory -Filter "work-*" -ErrorAction SilentlyContinue |
                        Sort-Object LastWriteTime -Descending | Select-Object -First 1
                    if ($latest) {
                        $c = Join-Path $latest.FullName "results.json"
                        if (Test-Path $c) { $res = $c }
                    }
                }
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
