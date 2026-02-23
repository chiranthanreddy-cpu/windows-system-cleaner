# Changelog

All notable changes to this project will be documented in this file.

## [1.3.1] - 2026-02-23
### Changed
- Improved scanning performance with multi-threading.
- Enhanced gauge animation with spring physics for a smoother feel.
- Added a high-performance virtual scroll list for the results view to handle a large number of files without freezing.
- Made cleaning safer by removing the direct-deletion fallback.

### Fixed
- Fixed a `SyntaxError` in the backup script.
- Fixed a `TclError` crash when displaying scan results.
- Fixed a bug where duplicate methods were defined in the cleaner engine.

## [1.3.0] - 2026-02-09
### The "Deep Space" Update
### Added
- **UI Redesign:** New premium "Deep Space" dark theme using CustomTkinter.
- **Circular Health Meter:** Custom-built animated gauge for real-time system health visualization.
- **Entrance Animations:** Smooth sequential UI loading for a more polished feel.
- **setup.bat:** New one-click environment setup for users running from source.
- **Intelligent Whitelisting:** Automatic skipping of "sticky" system/vendor files (Lenovo, Microsoft, etc.) during scans.
- **Uninstaller Support:** Full registration in Windows "Apps & Features" with a dedicated uninstall command.

### Changed
- **Performance Boost:** Optimized scanning engine with `os.scandir` for 3x faster disk traversal.
- **Health Calculation:** Implemented logarithmic scoring with a 1GB threshold for realistic health reporting.
- **Resilient Assets:** Improved resource loading to prevent crashes if icons or logos are missing.

### Fixed
- Fixed permission issues by moving `config.json` to `%LOCALAPPDATA%`.
- Resolved `TclError` during rapid UI transitions.

## [1.2.2] - 2026-02-09
### Added
- "Add to Start Menu" integration in Settings.
- Standalone `.exe` build via PyInstaller with splash screen.

## [1.2.1] - 2026-02-09
### Fixed
- Initial stability fixes for scanning large directories.

## [1.1.0] - 2026-02-07
### Added
- Initial GUI implementation using CustomTkinter.
- Basic target categories (Temp, Prefetch, Discord, Spotify).

## [1.0.0] - 2026-02-07
### Added
- Initial project release (CLI version).
- Core cleaning engine functionality.
