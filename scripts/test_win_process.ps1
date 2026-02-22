$ErrorActionPreference = "Stop"
Write-Host "PowerShell OK"
& "C:\Windows\System32\cmd.exe" /c "echo CMD_OK"
Write-Host "After cmd LASTEXITCODE=$LASTEXITCODE"
& "C:\Windows\System32\where.exe" cmd
Write-Host "After where LASTEXITCODE=$LASTEXITCODE"
