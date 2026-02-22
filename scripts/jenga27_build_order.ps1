$ErrorActionPreference = "Stop"

$repo = "E:\Projets\MacShared\Projets\Jenga"
$example = Join-Path $repo "Jenga\Exemples\27_nk_window"

if (-not (Test-Path $example)) {
    throw "Workspace not found: $example"
}

# --- Auto env setup for Windows host tooling ---
if (-not $env:ANDROID_SDK_ROOT) {
    if (Test-Path "C:\Android\sdk") { $env:ANDROID_SDK_ROOT = "C:\Android\sdk" }
}
if (-not $env:ANDROID_HOME -and $env:ANDROID_SDK_ROOT) {
    $env:ANDROID_HOME = $env:ANDROID_SDK_ROOT
}
if (-not $env:ANDROID_NDK_ROOT) {
    if (Test-Path "C:\Android\sdk\ndk\27.0.12077973") {
        $env:ANDROID_NDK_ROOT = "C:\Android\sdk\ndk\27.0.12077973"
    } elseif (Test-Path "C:\Android\android-ndk-r27d") {
        $env:ANDROID_NDK_ROOT = "C:\Android\android-ndk-r27d"
    }
}
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
Write-Host "ANDROID_SDK_ROOT=$env:ANDROID_SDK_ROOT"
Write-Host "ANDROID_NDK_ROOT=$env:ANDROID_NDK_ROOT"
Write-Host "MINGW_ROOT=$env:MINGW_ROOT"
Write-Host "EMSDK=$env:EMSDK"

$results = @{}

function Invoke-Build([string]$platform) {
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "BUILD PLATFORM: $platform"
    Write-Host "=================================================="

    $cmd = "$pythonCmd ..\\..\\jenga.py build --no-daemon --jenga-file 27_nk_window.jenga --platform $platform"
    Write-Host "> $cmd"

    cmd.exe /c $cmd
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        $results[$platform] = "OK"
    } else {
        $results[$platform] = "FAIL (exit=$exitCode)"
    }
}

# Order requested: Android -> Windows -> Emscripten(Web)
Invoke-Build "Android-arm64"
Invoke-Build "Windows"
Invoke-Build "Web"

Write-Host ""
Write-Host "==================== SUMMARY ====================="
foreach ($p in @("Android-arm64", "Windows", "Web")) {
    $status = if ($results.ContainsKey($p)) { $results[$p] } else { "NOT_RUN" }
    Write-Host "$p => $status"
}

$failed = $results.Keys | Where-Object { $results[$_] -like "FAIL*" }
if ($failed.Count -gt 0) {
    exit 1
}
exit 0
