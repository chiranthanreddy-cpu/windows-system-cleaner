# Windows System Cleaner

A simple Python script to automate the cleanup of temporary files and the Recycle Bin on Windows.

## Features
- Cleans User Temp folder (`%TEMP%`)
- Cleans System Temp folder (`C:\Windows\Temp`)
- Cleans Prefetch folder (requires Administrator privileges)
- Empties the Recycle Bin
- **Dry Run Mode**: Preview changes before they happen
- **Logging**: Keeps a history of cleanups in `cleanup.log`
- **Safety Grace Period**: Automatically skips any files modified within the last 24 hours to prevent deleting active data.
- **Auto-Scheduling**: Includes a script to set up a weekly Windows Scheduled Task.

## Usage
Run the script using Python:
```powershell
python cleaner.py
```

### Scheduling Weekly
To automatically run this every Saturday at 10:00 AM:
1. Open PowerShell as Administrator.
2. Run the setup script:
   ```powershell
   ./schedule_task.ps1
   ```

### Dry Run (Recommended first)
To see what will be deleted without actually removing any files:
```powershell
python cleaner.py --dry-run
```
To clean system-protected folders, run your terminal as an Administrator.

## Version
1.0.0
