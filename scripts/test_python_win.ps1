$py = "C:\Users\Rihen\AppData\Local\Programs\Python\Python313\python.exe"
Get-Item $py | Select-Object FullName,Length,VersionInfo | Format-List
cmd.exe /c "\"$py\" --version"
Write-Host "cmd LASTEXITCODE=$LASTEXITCODE"
