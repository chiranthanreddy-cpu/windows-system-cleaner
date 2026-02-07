# Windows System Cleaner - Task Removal Script
$TaskName = "WindowsSystemCleanerWeekly"

try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Success: Task '$TaskName' has been removed." -ForegroundColor Green
} catch {
    Write-Host "Note: Task '$TaskName' was not found or is already removed." -ForegroundColor Yellow
}
