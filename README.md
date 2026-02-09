# 🛡️ Windows System Cleaner

A premium, local-only cleanup utility designed for power users and developers. Reclaim disk space by purging system caches, app bloat, and long-forgotten project dependencies.

![Language](https://img.shields.io/badge/Language-Python-blue)
![Version](https://img.shields.io/badge/Version-1.3.0-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![Security](https://img.shields.io/badge/Security-Local--Only-brightgreen)

## ✨ What's New in v1.3.0 (The "Deep Space" Update)
- **Modern UI/UX:** A completely redesigned "Deep Space" dark theme with smooth entrance animations.
- **Circular Health Meter:** Real-time visual feedback on system health with a custom animated gauge.
- **High-Performance Scanning:** Engine optimized with `os.scandir` for up to 3x faster disk traversal.
- **Resilient Cleaning:** Intelligent whitelisting of "sticky" system files and automated direct-deletion fallbacks.
- **One-Click Installation:** New `setup.bat` for instant environment configuration.

## 🚀 Key Features
- **Modern Dashboard:** High-performance UI built with `CustomTkinter`.
- **Deep Cleaning:** Targets User Temp, System Temp, Prefetch, **Discord**, and **Spotify** caches.
- **Dev-Bloat Hunter:** Automatically finds `node_modules` or `venv` folders untouched for 30+ days.
- **Safety First:** 
  - **24h Grace Period:** Protects files modified within the last 24 hours.
  - **Logarithmic Scoring:** Health percentage scales realistically based on junk size (1GB threshold).
- **Professional Presence:** Full Start Menu integration and "Apps & Features" registration for easy uninstallation.

---

## 📦 Installation

### Option 1: Standalone (Recommended)
1. **[Download WindowsSystemCleaner.exe](https://github.com/chiranthanreddy-cpu/windows-system-cleaner/releases/latest/download/WindowsSystemCleaner.exe)**
2. Run the `.exe`.
3. Click **"Yes"** on the first-run prompt to instantly add the app to your Start Menu.

### Option 2: ZIP Download / Developer Mode
1. Download and extract the source ZIP.
2. Double-click **`setup.bat`**. This will automatically install Python dependencies and launch the app.
3. Once open, go to **Settings** and click **"Add to Start Menu"** to complete the registration.

### Manual Setup
```powershell
pip install -r requirements.txt
python WindowsSystemCleaner.py
```

---

## ⚙️ Configuration
The app stores persistent configuration in `%LOCALAPPDATA%\WindowsSystemCleaner\config.json`.
- `grace_period_hours`: Protect items newer than X hours (Default: 24).
- `empty_recycle_bin`: Toggle automatic final trashing (Default: True).
- `dev_bloat_hunter`: Enable/Disable deep project scanning (Default: False).

---
*Created by [Chiranthan Reddy](https://github.com/chiranthanreddy-cpu)*
