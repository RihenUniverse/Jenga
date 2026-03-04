$ErrorActionPreference = "Stop"

$repo = "E:\Projets\MacShared\Projets\Jenga"
$example27 = Join-Path $repo "Jenga\Exemples\27_nk_window"
$example25 = Join-Path $repo "Jenga\Exemples\25_opengl_triangle"

if (-not (Test-Path $example27)) { throw "Missing: $example27" }
if (-not (Test-Path $example25)) { throw "Missing: $example25" }

if (-not $env:ANDROID_SDK_ROOT -and (Test-Path "C:\Android\sdk")) {
    $env:ANDROID_SDK_ROOT = "C:\Android\sdk"
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

$pythonExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
    $pythonPrefix = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
    $pythonPrefix = @()
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonExe = "python3"
    $pythonPrefix = @()
} else {
    $cand = Get-ChildItem "C:\Users\*\AppData\Local\Programs\Python" -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $cand) { throw "Python not found" }
    $pythonExe = $cand.FullName
    $pythonPrefix = @()
}

Write-Host "Python: $pythonExe"
Write-Host "ANDROID_SDK_ROOT=$env:ANDROID_SDK_ROOT"
Write-Host "ANDROID_NDK_ROOT=$env:ANDROID_NDK_ROOT"

function Run-Build([string]$path, [string]$jengaFile, [string]$label) {
    Write-Host ""
    Write-Host "===== BUILD $label ====="
    Set-Location $path
    # Nettoyage ciblé Android pour éviter les mélanges d'artefacts entre ABIs.
    foreach ($sub in @("Build\\Obj", "Build\\Lib", "Build\\Bin", "Build\\Tests")) {
        $base = Join-Path $path $sub
        if (Test-Path $base) {
            Get-ChildItem -Path $base -Directory -Filter "Debug-Android*" -ErrorAction SilentlyContinue |
                Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    $buildRoot = Join-Path $path "Build"
    if (Test-Path $buildRoot) {
        Get-ChildItem -Path $buildRoot -Directory -Recurse -Filter "android-build-*" -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }

    $logDir = Join-Path $path "Build\command_tests"
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $safeLabel = ($label -replace "[^A-Za-z0-9_-]", "_")
    $logFile = Join-Path $logDir "android_build_${safeLabel}_${stamp}.log"

    # Important: en PowerShell 7, stderr des commandes natives peut devenir une erreur
    # terminante si ErrorActionPreference=Stop. On le désactive localement pour garder
    # le flux de build intact et récupérer le code de retour réel.
    $oldNativePref = $null
    if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
        $oldNativePref = $global:PSNativeCommandUseErrorActionPreference
        $global:PSNativeCommandUseErrorActionPreference = $false
    }
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $pythonExe @pythonPrefix "..\\..\\jenga.py" "build" "--no-daemon" "--jenga-file" $jengaFile "--platform" "Android-arm64" 2>&1 | Tee-Object -FilePath $logFile
    } finally {
        $ErrorActionPreference = $oldEap
        if ($null -ne $oldNativePref) {
            $global:PSNativeCommandUseErrorActionPreference = $oldNativePref
        }
    }
    $code = $LASTEXITCODE
    Write-Host "===== RESULT ${label}: exit=$code ====="
    Write-Host "Log: $logFile"
    if ($code -ne 0) {
        Write-Host "----- LAST 120 LOG LINES ($label) -----"
        Get-Content -Path $logFile -Tail 120
        Write-Host "----- END LOG -----"
    }
    return $code
}

$code25 = Run-Build $example25 "25_opengl_triangle.jenga" "EXAMPLE 25"
$code27 = Run-Build $example27 "27_nk_window.jenga" "EXAMPLE 27"

if ($code25 -ne 0 -or $code27 -ne 0) {
    exit 1
}
exit 0
