param(
  [string]$PythonCmd = "py",
  [switch]$NoCache,
  [string]$Config = "Debug",
  [switch]$ForceAllPlatforms,
  [switch]$SkipSmoke,
  [switch]$SmokeOnly
)

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Force UTF-8 to avoid cp1252 banner crash with box-drawing characters.
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

$resultsDir = Join-Path $root ".jenga\windows-test-results"
New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null

$examples = Get-ChildItem -Directory (Join-Path $root "Exemples") | Where-Object { $_.Name -match '^[0-9][0-9]_' } | Sort-Object Name

# Detect installed toolchains/platform capability.
$hasEmcc = [bool](Get-Command emcc -ErrorAction SilentlyContinue)
$hasAndroidSdk = [bool]$env:ANDROID_SDK_ROOT -or [bool]$env:ANDROID_HOME
$hasAndroidNdk = [bool]$env:ANDROID_NDK_ROOT -or [bool]$env:ANDROID_NDK_HOME
$hasHarmony = [bool]$env:HARMONY_OS_SDK
$hasGdk = [bool]$env:GameDK -or (Test-Path "C:\Program Files\Microsoft GDK")
$hasZig = [bool](Get-Command zig -ErrorAction SilentlyContinue)

# Base matrix.
$platforms = @($null, "Windows-x86_64")

# Cross Linux from Windows if zig or clang/gcc cross is likely available.
if ($ForceAllPlatforms -or $hasZig -or (Get-Command clang -ErrorAction SilentlyContinue) -or (Get-Command gcc -ErrorAction SilentlyContinue)) {
  $platforms += "Linux-x86_64"
}
if ($ForceAllPlatforms -or ($hasAndroidSdk -and $hasAndroidNdk)) {
  $platforms += "Android-arm64"
}
if ($ForceAllPlatforms -or $hasEmcc) {
  $platforms += "Web-wasm32"
}
if ($ForceAllPlatforms -or $hasHarmony) {
  $platforms += "HarmonyOS-arm64"
}
if ($ForceAllPlatforms -or $hasGdk) {
  $platforms += "XboxOne-x86_64"
  $platforms += "XboxSeries-x86_64"
}

# macOS/iOS builders are intentionally host-restricted to macOS.
if ($ForceAllPlatforms) {
  $platforms += "macOS-arm64"
  $platforms += "iOS-arm64"
}

Write-Host "Detected toolchains:"
Write-Host ("  emcc={0} androidSdk={1} androidNdk={2} zig={3} harmony={4} gdk={5}" -f $hasEmcc, $hasAndroidSdk, $hasAndroidNdk, $hasZig, $hasHarmony, $hasGdk)
Write-Host ("Platform matrix: {0}" -f (($platforms | ForEach-Object { if ($_){$_} else {"default"} }) -join ", "))

# Refresh global toolchains from current machine first.
& $PythonCmd -X utf8 -m Jenga.Jenga install toolchain detect | Out-Host

$summary = @()

function Invoke-ExampleBuild {
  param(
    [Parameter(Mandatory = $true)] [System.IO.DirectoryInfo]$ExampleDir,
    [Parameter(Mandatory = $false)] [string]$Platform
  )

  $jengaFile = Get-ChildItem -Path $ExampleDir.FullName -Filter *.jenga | Select-Object -First 1
  if (-not $jengaFile) { return $null }

  $name = $ExampleDir.Name
  $platTag = if ($Platform) { $Platform } else { "default" }
  $safeTag = ($platTag -replace '[^A-Za-z0-9_\-]', '_')
  $logPath = Join-Path $resultsDir ("{0}_{1}.log" -f $name, $safeTag)
  $outPath = Join-Path $resultsDir ("{0}_{1}.out.log" -f $name, $safeTag)
  $errPath = Join-Path $resultsDir ("{0}_{1}.err.log" -f $name, $safeTag)

  $args = @("-X", "utf8", "-m", "Jenga.Jenga", "build", "--jenga-file", $jengaFile.FullName, "--no-daemon", "--config", $Config)
  if ($NoCache) { $args += "--no-cache" }
  if ($Platform) { $args += @("--platform", $Platform) }

  Write-Host ("===== {0} [{1}] =====" -f $name, $platTag)
  $exitCode = -1
  try {
    $proc = Start-Process -FilePath $PythonCmd -ArgumentList $args -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outPath -RedirectStandardError $errPath
    $exitCode = $proc.ExitCode
  } catch {
    $_ | Out-String | Set-Content -Path $errPath -Encoding UTF8
    $exitCode = -1
  }
  if (Test-Path $outPath) { Get-Content $outPath | Set-Content -Path $logPath -Encoding UTF8 } else { "" | Set-Content -Path $logPath -Encoding UTF8 }
  if (Test-Path $errPath) { Add-Content -Path $logPath -Value "`n----- STDERR -----`n" -Encoding UTF8; Get-Content $errPath | Add-Content -Path $logPath -Encoding UTF8 }

  $status = if ($exitCode -eq 0) { "OK" } else { "FAIL" }
  Write-Host ("{0} -> exit={1}" -f $status, $exitCode)

  return [PSCustomObject]@{
    Example = $name
    Platform = $platTag
    ExitCode = $exitCode
    Log = $logPath
  }
}

$smokeSet = @("01_hello_console", "02_static_library", "09_multi_projects", "18_window_android_native")
if (-not $SkipSmoke) {
  $smokeExamples = $examples | Where-Object { $smokeSet -contains $_.Name }
  Write-Host "`n=== Smoke pass (01, 02, 09, 18) ==="
  foreach ($ex in $smokeExamples) {
    foreach ($plat in $platforms) {
      $row = Invoke-ExampleBuild -ExampleDir $ex -Platform $plat
      if ($null -ne $row) { $summary += $row }
    }
  }
  $smokeFailures = ($summary | Where-Object { $_.ExitCode -ne 0 }).Count
  if ($smokeFailures -gt 0) {
    Write-Host "`nSmoke failed ($smokeFailures failures). Stopping before full matrix."
    $csv = Join-Path $resultsDir "summary.csv"
    $summary | Export-Csv -NoTypeInformation -Path $csv -Encoding UTF8
    Write-Host "Summary CSV: $csv"
    exit 1
  }
  if ($SmokeOnly) {
    $csv = Join-Path $resultsDir "summary.csv"
    $summary | Export-Csv -NoTypeInformation -Path $csv -Encoding UTF8
    Write-Host "`nSmoke-only run completed. Summary CSV: $csv"
    exit 0
  }
}

foreach ($ex in $examples) {
  if ((-not $SkipSmoke) -and ($smokeSet -contains $ex.Name)) { continue }
  foreach ($plat in $platforms) {
    $row = Invoke-ExampleBuild -ExampleDir $ex -Platform $plat
    if ($null -ne $row) { $summary += $row }
  }
}

$csv = Join-Path $resultsDir "summary.csv"
$summary | Export-Csv -NoTypeInformation -Path $csv -Encoding UTF8
Write-Host "\nSummary CSV: $csv"

$ok = ($summary | Where-Object { $_.ExitCode -eq 0 }).Count
$ko = ($summary | Where-Object { $_.ExitCode -ne 0 }).Count
Write-Host ("Total: {0} OK / {1} FAIL" -f $ok, $ko)

if ($ko -gt 0) {
  $firstFail = $summary | Where-Object { $_.ExitCode -ne 0 } | Select-Object -First 1
  if ($firstFail -and (Test-Path $firstFail.Log)) {
    Write-Host "`nFirst failure: $($firstFail.Example) [$($firstFail.Platform)]"
    Write-Host "Log: $($firstFail.Log)"
    Write-Host "----- log tail -----"
    Get-Content $firstFail.Log -Tail 60 | Out-Host
  }
}
