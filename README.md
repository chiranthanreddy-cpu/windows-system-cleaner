# Windows System Cleaner

A powerful utility to automate the cleanup of temporary files and the Recycle Bin on Windows.

## Features
- **Modern GUI (Lumina Cleaner Pro):** A professional, dark-themed dashboard built with CustomTkinter.
- **Deep Cleaning:** Targets User Temp, System Temp, Prefetch, **Discord Cache**, and **Spotify Cache**.
- **Safety First:** 
  - **Local-Only:** No internet access or data collection.
  - **Grace Period:** Automatically protects files modified in the last 24 hours.
  - **Review Mode:** Analyze what will be deleted before committing.
- **Empties the Recycle Bin** (Optional toggle).
- **Auto-Scheduling:** Includes a script to set up a weekly background task.

## Usage (GUI)
To launch the modern interface:
```powershell
python gui_cleaner.py
```
*Note: Run your terminal as Administrator to unlock deep system cleaning capabilities.*

## Usage (CLI)
Run the classic script using Python:
```powershell
python cleaner.py
```

### Scheduling Weekly (Background Mode)
To automatically run this cleanup every Saturday at 10:00 AM without any terminal windows flashing:

1. **Open PowerShell as Administrator** (Right-click Start > Terminal (Admin) or PowerShell (Admin)).
2. Navigate to this folder:
   ```powershell
   cd "C:\Users\chiru\windows-system-cleaner"
   ```
3. Run the setup script:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; ./schedule_task.ps1
   ```

*Note: The script is scheduled using `pythonw.exe` to ensure it runs silently in the background.*

### Dry Run (Recommended first)
To see what will be deleted without actually removing any files:
```powershell
python cleaner.py --dry-run
```
To clean system-protected folders, run your terminal as an Administrator.

## Version
2.0.0