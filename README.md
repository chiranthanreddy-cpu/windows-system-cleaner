# 🛡️ Windows System Cleaner

A professional, local-only cleanup utility designed for power users and developers. Reclaim disk space by purging caches and hunting down old project bloat.

![Language](https://img.shields.io/badge/Language-Python-blue)
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
1. Go to the [Releases](https://github.com/chiranthanreddy-cpu/windows-system-cleaner/releases) page.
2. Download `Windows System Cleaner.exe`.
3. Right-click and **Run as Administrator** (required for deep system cleaning).

### Option 2: Run from Source (For Developers)
1. **Clone the repo:**
   ```powershell
   git clone https://github.com/chiranthanreddy-cpu/windows-system-cleaner.git
   cd windows-system-cleaner
   ```
2. **Install requirements:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Launch the App:**
   ```powershell
   python WindowsSystemCleaner.py
   ```

---

## 🛠️ CLI Mode
For automated or headless cleanup, use the CLI tool:
```powershell
python SystemCleanerCLI.py
```
**Dry Run (Safety Check):**
```powershell
python SystemCleanerCLI.py --dry-run
```

## ⚙️ Configuration
The app uses a `config.json` file created on the first run. You can manually adjust:
- `grace_period_hours`: Default is 24.
- `targets`: List of folders to clean.
- `empty_recycle_bin`: Boolean toggle.

---
*Created by [Chiranthan Reddy](https://github.com/chiranthanreddy-cpu)*