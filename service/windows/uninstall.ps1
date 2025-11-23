# Nabu Windows Service Uninstallation Script
# Run this script as Administrator

$serviceName = "NabuMeetingSummarizer"

# Unregister the scheduled task
Unregister-ScheduledTask -TaskName $serviceName -Confirm:$false

Write-Host "✓ Nabu service uninstalled successfully!"
