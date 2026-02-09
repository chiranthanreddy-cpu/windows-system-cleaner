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

## 🔍 Feature Deep Dives

### Dev-Bloat Hunter
Designed for developers, this feature scans your project directories for massive dependency folders (`node_modules`, `venv`, `.venv`) that haven't been accessed or modified in over **30 days**. It helps you reclaim gigabytes of space from abandoned projects without touching your active work.

### Smart Health Scoring
Unlike simple linear percentages, this app uses **Logarithmic Scaling**:
- **Threshold:** 1GB of junk = 100% (Cleanup Required).
- **Small Scale:** Under 10MB is reported as 0% (Optimized) to avoid unnecessary cleaning.
- **Scaling:** The meter moves faster for the first few hundred MBs and slows down as it approaches 1GB, providing a more intuitive feel for "system weight."

---

## 🛠 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **App won't start** | Ensure you have Python 3.10+ installed. If using the `.exe`, try running as Administrator. |
| **Antivirus Flags** | Because the app interacts with system folders and the Registry, some AVs may flag it. It is 100% open source and safe. |
| **Files won't delete** | Some files are "sticky" (locked by Windows or Vendor services like Lenovo). The app whitelists these to prevent loops. |
| **Missing Icons** | If the logo disappears, the app will use built-in fallbacks. Re-downloading the `assets` folder fixes this. |

---

## 🛡 Security & Privacy
- **100% Local-Only:** No data ever leaves your machine. No telemetry, no analytics, no cloud pings.
- **Open Source:** Every line of code is available for audit.
- **Safe Trashing:** Defaults to using the Windows Recycle Bin (`send2trash`) rather than permanent deletion for maximum safety.

---

## 📦 Installation

### Option 1: Standalone (Recommended)
1. **[Download Latest WindowsSystemCleaner.exe](https://github.com/chiranthanreddy-cpu/windows-system-cleaner/releases/latest/download/WindowsSystemCleaner.exe)**
2. Run the `.exe` and click **"Yes"** on the first-run prompt.

### Option 2: ZIP Download / Developer Mode
1. Download and extract the source ZIP.
2. Double-click **`setup.bat`**. This will automatically install dependencies and launch the app.
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
