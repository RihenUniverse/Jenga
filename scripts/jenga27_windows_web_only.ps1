param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$repo = "E:\Projets\MacShared\Projets\Jenga"
$example = Join-Path $repo "Jenga\Exemples\27_nk_window"

if (-not (Test-Path $example)) {
    throw "Workspace not found: $example"
}

# --- Auto env setup for Windows host tooling ---
if (-not $env:MINGW_ROOT -and (Test-Path "C:\msys64\ucrt64")) {
    $env:MINGW_ROOT = "C:\msys64\ucrt64"
}
if (-not $env:EMSDK) {
    if (Test-Path "C:\emsdk") {
        $env:EMSDK = "C:\emsdk"
    } elseif (Test-Path "E:\emsdk") {
        $env:EMSDK = "E:\emsdk"
    }
}

$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    $pyCandidates = Get-ChildItem "C:\\Users\\*\\AppData\\Local\\Programs\\Python" -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending
    if ($pyCandidates -and $pyCandidates.Count -gt 0) {
        $pythonCmd = ('"' + $pyCandidates[0].FullName + '"')
    } else {
        throw "Python not found on Windows PATH"
    }
}

Set-Location $example

Write-Host "Repo: $repo"
Write-Host "Example: $example"
Write-Host "Python: $pythonCmd"
Write-Host "MINGW_ROOT=$env:MINGW_ROOT"
Write-Host "EMSDK=$env:EMSDK"
Write-Host "Clean mode: $Clean"

if (-not (Get-Command emcc -ErrorAction SilentlyContinue)) {
    Write-Warning "emcc not found in PATH. If Web build fails, run emsdk_env.bat first."
}

$results = @{}

function Invoke-Step([string]$platform) {
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "PLATFORM: $platform"
    Write-Host "=================================================="

    if ($Clean) {
        $cleanCmd = "$pythonCmd ..\\..\\jenga.py clean --jenga-file 27_nk_window.jenga --platform $platform"
        Write-Host "> $cleanCmd"
        cmd.exe /c $cleanCmd
        if ($LASTEXITCODE -ne 0) {
            $results[$platform] = "FAIL CLEAN (exit=$LASTEXITCODE)"
            return
        }
    }

    $buildCmd = "$pythonCmd ..\\..\\jenga.py build --no-daemon --jenga-file 27_nk_window.jenga --platform $platform"
    Write-Host "> $buildCmd"
    cmd.exe /c $buildCmd
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        $results[$platform] = "OK"
    } else {
        $results[$platform] = "FAIL BUILD (exit=$exitCode)"
    }
}

# Order requested after Android: Windows -> Web (Emscripten)
Invoke-Step "Windows"
Invoke-Step "Web"

$launcherGenerator = Join-Path $repo "scripts\generate_launchers.py"
if (Test-Path $launcherGenerator) {
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "GENERATE LAUNCHERS"
    Write-Host "=================================================="
    $launcherCmd = "$pythonCmd `"$launcherGenerator`" --example-dir `"$example`""
    Write-Host "> $launcherCmd"
    cmd.exe /c $launcherCmd
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Launcher generation failed (exit=$LASTEXITCODE)"
    }
} else {
    Write-Warning "Launcher generator not found: $launcherGenerator"
}

Write-Host ""
Write-Host "==================== SUMMARY ====================="
foreach ($p in @("Windows", "Web")) {
    $status = if ($results.ContainsKey($p)) { $results[$p] } else { "NOT_RUN" }
    Write-Host "$p => $status"
}

$failed = $results.Keys | Where-Object { $results[$_] -like "FAIL*" }
if ($failed.Count -gt 0) {
    exit 1
}
exit 0
