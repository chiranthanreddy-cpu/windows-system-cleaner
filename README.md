# Windows System Cleaner

A simple Python script to automate the cleanup of temporary files and the Recycle Bin on Windows.

## Features
- Cleans User Temp folder (`%TEMP%`)
- Cleans System Temp folder (`C:\Windows\Temp`)
- Cleans Prefetch folder (requires Administrator privileges)
- Empties the Recycle Bin
- **Dry Run Mode**: Preview changes before they happen
- **Logging**: Keeps a history of cleanups in `cleanup.log`
- Provides a summary of space reclaimed

## Usage
Run the script using Python:
```powershell
python cleaner.py
```

### Dry Run (Recommended first)
To see what will be deleted without actually removing any files:
```powershell
python cleaner.py --dry-run
```
To clean system-protected folders, run your terminal as an Administrator.

## Version
1.0.0
