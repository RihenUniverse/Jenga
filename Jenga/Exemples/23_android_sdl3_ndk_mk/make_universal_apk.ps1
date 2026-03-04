param(
    [string]$Config = "Debug",
    [string]$Project = "SDL3NativeDemo"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-BuildTool {
    param(
        [string]$SdkPath,
        [string]$ToolName
    )

    $buildTools = Join-Path $SdkPath "build-tools"
    if (!(Test-Path $buildTools)) {
        throw "Android build-tools directory not found: $buildTools"
    }

    $latest = Get-ChildItem -Path $buildTools -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $latest) {
        throw "No Android build-tools version found in: $buildTools"
    }

    $candidates = @(
        (Join-Path $latest.FullName "$ToolName.exe"),
        (Join-Path $latest.FullName "$ToolName.bat"),
        (Join-Path $latest.FullName $ToolName)
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            return $c
        }
    }
    throw "$ToolName not found in $($latest.FullName)"
}

function Expand-ApkToDirectory {
    param(
        [string]$ApkPath,
        [string]$Destination
    )

    $zipCopy = Join-Path (Split-Path $Destination -Parent) ((Split-Path $ApkPath -Leaf) + ".zip")
    Copy-Item -Force $ApkPath $zipCopy
    Expand-Archive -Path $zipCopy -DestinationPath $Destination -Force
}

$sdkRoot = $env:ANDROID_SDK_ROOT
if ([string]::IsNullOrWhiteSpace($sdkRoot)) {
    $sdkRoot = $env:ANDROID_HOME
}
if ([string]::IsNullOrWhiteSpace($sdkRoot)) {
    $sdkRoot = "C:/Android/sdk"
}
if (!(Test-Path $sdkRoot)) {
    throw "Android SDK not found. Set ANDROID_SDK_ROOT or ANDROID_HOME."
}

$zipalign = Resolve-BuildTool -SdkPath $sdkRoot -ToolName "zipalign"
$apksigner = Resolve-BuildTool -SdkPath $sdkRoot -ToolName "apksigner"

$exampleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apkRoot = Join-Path $exampleRoot ("Build/Bin/{0}-Android/{1}" -f $Config, $Project)

$abiMap = @{
    "armeabi-v7a" = Join-Path $apkRoot "$("android-build-armeabi-v7a")/$Project-$Config.apk"
    "arm64-v8a"   = Join-Path $apkRoot "$("android-build-arm64-v8a")/$Project-$Config.apk"
    "x86"         = Join-Path $apkRoot "$("android-build-x86")/$Project-$Config.apk"
    "x86_64"      = Join-Path $apkRoot "$("android-build-x86_64")/$Project-$Config.apk"
}

foreach ($abi in $abiMap.Keys) {
    if (!(Test-Path $abiMap[$abi])) {
        throw "Missing ABI APK for '$abi': $($abiMap[$abi])"
    }
}

$outDir = Join-Path $apkRoot "android-build-universal-ndk-mk"
$workDir = Join-Path $outDir "_work"
if (Test-Path $workDir) {
    Remove-Item -Recurse -Force $workDir
}
New-Item -ItemType Directory -Force -Path $workDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$baseDir = Join-Path $workDir "base"
Expand-ApkToDirectory -ApkPath $abiMap["arm64-v8a"] -Destination $baseDir

foreach ($abi in $abiMap.Keys) {
    $abiDir = Join-Path $workDir ("abi_" + $abi)
    Expand-ApkToDirectory -ApkPath $abiMap[$abi] -Destination $abiDir

    $src = Join-Path $abiDir ("lib/" + $abi)
    $dst = Join-Path $baseDir ("lib/" + $abi)
    if (Test-Path $src) {
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
    }
}

$metaInf = Join-Path $baseDir "META-INF"
if (Test-Path $metaInf) {
    Remove-Item -Recurse -Force $metaInf
}

$unsignedZip = Join-Path $outDir "$Project-$Config-universal-unsigned-unaligned.zip"
$unsignedUnalignedApk = Join-Path $outDir "$Project-$Config-universal-unsigned-unaligned.apk"
$unsignedApk = Join-Path $outDir "$Project-$Config-universal-unsigned.apk"
$signedApk = Join-Path $outDir "$Project-$Config-universal.apk"

foreach ($f in @($unsignedZip, $unsignedUnalignedApk, $unsignedApk, $signedApk)) {
    if (Test-Path $f) {
        Remove-Item -Force $f
    }
}

Compress-Archive -Path (Join-Path $baseDir "*") -DestinationPath $unsignedZip -CompressionLevel Optimal
Copy-Item -Force $unsignedZip $unsignedUnalignedApk

& $zipalign -f -p 4 $unsignedUnalignedApk $unsignedApk
if ($LASTEXITCODE -ne 0) {
    throw "zipalign failed"
}

$debugKeystore = Join-Path $HOME ".android/debug.keystore"
if (!(Test-Path $debugKeystore)) {
    throw "Debug keystore not found: $debugKeystore"
}

& $apksigner sign --ks $debugKeystore --ks-pass pass:android --ks-key-alias androiddebugkey --out $signedApk $unsignedApk
if ($LASTEXITCODE -ne 0) {
    throw "apksigner sign failed"
}

& $apksigner verify --print-certs $signedApk
if ($LASTEXITCODE -ne 0) {
    throw "apksigner verify failed"
}

Write-Host "Universal APK generated:" -ForegroundColor Green
Write-Host "  $signedApk"
