# 🛡️ Windows System Cleaner

A professional, local-only cleanup utility designed for power users and developers. Reclaim disk space by purging caches and hunting down old project bloat.

![Language](https://img.shields.io/badge/Language-Python-blue)
![Version](https://img.shields.io/badge/Version-1.2.1-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![Security](https://img.shields.io/badge/Security-Local--Only-brightgreen)

## ✨ Key Features
- **Modern Dashboard:** High-performance UI built with `CustomTkinter`.
- **Deep Cleaning:** Targets User Temp, System Temp, Prefetch, **Discord**, and **Spotify** caches.
- **Dev-Bloat Hunter:** Automatically finds `node_modules` or `venv` folders untouched for 30+ days.
- **Safety First:** 
  - **24h Grace Period:** Protects files modified within the last 24 hours.
  - **Local-Only:** Zero data collection, zero telemetry.
- **Splash Screen:** Instant visual feedback on startup.

---

## 🚀 Installation & Usage

### Option 1: Standalone (Recommended for Users)
1. **[Download Latest WindowsSystemCleaner.exe](https://github.com/chiranthanreddy-cpu/windows-system-cleaner/releases/latest/download/WindowsSystemCleaner.exe)**
2. Run the `.exe` and click **"Yes"** when it asks to add itself to your Start Menu.

### Option 2: ZIP Download / Developer Mode
1. Extract the downloaded ZIP folder.
2. Double-click **`setup.bat`**. This will automatically install dependencies and launch the app.
3. Once open, go to **Settings** and click **"Add to Start Menu"** to finish setup.

### Manual Setup (CLI)
If you prefer the terminal:
```powershell
pip install -r requirements.txt
python WindowsSystemCleaner.py
```

---

## ⚙️ Configuration
The app uses a `config.json` file created on the first run. You can manually adjust:
- `grace_period_hours`: Default is 24.
- `targets`: List of folders to clean.
- `empty_recycle_bin`: Boolean toggle.

---
*Created by [Chiranthan Reddy](https://github.com/chiranthanreddy-cpu)*