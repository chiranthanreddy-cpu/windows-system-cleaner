# Windows System Cleaner

A powerful utility to automate the cleanup of temporary files and the Recycle Bin on Windows.

## Features
- **Modern GUI (Lumina Cleaner Pro):** A professional, dark-themed dashboard built with CustomTkinter.
- **Deep Cleaning:** Targets User Temp, System Temp, Prefetch, **Discord Cache**, and **Spotify Cache**.
- **Dev-Bloat Hunter:** Safely scans for old `node_modules` and `venv` folders (30+ days untouched).
- **Safety First:** 
  - **Local-Only:** No internet access or data collection.
  - **Grace Period:** Automatically protects files modified in the last 24 hours.
  - **Review Mode:** Analyze what will be deleted before committing.
- **Empties the Recycle Bin** (Optional toggle).

## Installation
1. **Download the code** (or clone the repo).
2. **Install Python** (make sure to check "Add Python to PATH" during installation).
3. **Install dependencies** by running this in your terminal:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage (GUI)
To launch the modern interface:
1. Open your terminal (PowerShell or Command Prompt).
2. Navigate to this folder.
3. Run:
   ```powershell
   python gui_cleaner.py
   ```
*Note: Run your terminal as **Administrator** to unlock deep system cleaning capabilities.*

## Usage (CLI)
For a quick, text-based cleanup without a GUI:
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
2.0.0