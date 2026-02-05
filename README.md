# Windows System Cleaner

A simple Python script to automate the cleanup of temporary files and the Recycle Bin on Windows.

## Features
- Cleans User Temp folder (`%TEMP%`)
- Cleans System Temp folder (`C:\Windows\Temp`)
- Cleans Prefetch folder (requires Administrator privileges)
- Empties the Recycle Bin
- Provides a summary of space reclaimed

## Usage
Run the script using Python:
```powershell
python cleaner.py
```
To clean system-protected folders, run your terminal as an Administrator.

## Version
1.0.0
