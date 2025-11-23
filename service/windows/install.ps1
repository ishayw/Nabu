# Nabu Windows Service Installation Script
# Run this script as Administrator

$serviceName = "NabuMeetingSummarizer"
$pythonPath = (Get-Command python).Source
$scriptPath = Join-Path $PSScriptRoot "..\..\main.py"
$workingDir = Join-Path $PSScriptRoot "..\..\"

# Create a scheduled task to run at startup
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit 0

# Register the task
Register-ScheduledTask -TaskName $serviceName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

Write-Host "✓ Nabu service installed successfully!"
Write-Host "The service will start automatically on next login."
Write-Host ""
Write-Host "To start now: Start-ScheduledTask -TaskName '$serviceName'"
Write-Host "To stop: Stop-ScheduledTask -TaskName '$serviceName'"
Write-Host "To uninstall: Unregister-ScheduledTask -TaskName '$serviceName'"
