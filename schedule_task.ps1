# Windows System Cleaner - Task Scheduler Setup
$ScriptName = "cleaner.py"
$CurrentDir = Get-Location
$PythonPath = (Get-Command python).Source
$TaskName = "WindowsSystemCleanerWeekly"
$ActionExecutable = $PythonPath
$ActionArguments = "`"$CurrentDir\$ScriptName`""

# Create the action
$Action = New-ScheduledTaskAction -Execute $ActionExecutable -Argument $ActionArguments

# Create the trigger (Weekly on Saturday at 10:00 AM)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Saturday -At 10:00am

# Create the settings (Run only when on AC power, etc.)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$false -DontStopIfGoingOnBatteries:$false

# Register the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Automated weekly cleanup of temporary files using Python script." -Force

Write-Host "Task '$TaskName' has been scheduled successfully!" -ForegroundColor Green
Write-Host "It will run every Saturday at 10:00 AM."
Write-Host "Note: It will only delete files older than 24 hours for safety."
