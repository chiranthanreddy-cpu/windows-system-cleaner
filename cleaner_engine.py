import os
import shutil
import ctypes
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup internal engine logging
logging.basicConfig(
    filename="engine_debug.log",
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CleanerEngine")

class CleanerEngine:
    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.is_admin = self.check_admin()
        self.last_scan_results = []

    def load_config(self):
        default_config = {
            "grace_period_hours": 24,
            "empty_recycle_bin": True,
            "targets": ["TEMP", "SYSTEM_TEMP", "PREFETCH", "DISCORD", "SPOTIFY"],
            "dev_bloat_hunter": False
        }
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        return default_config

    def save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def get_size(self, path: Path):
        try:
            if path.is_file():
                return path.stat().st_size
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        except Exception:
            return 0

    def format_bytes(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def get_target_paths(self):
        paths = []
        user_appdata = os.environ.get('APPDATA')
        user_local = os.environ.get('LOCALAPPDATA')
        system_root = os.environ.get('SystemRoot', 'C:\\Windows')
        
        target_map = {
            "TEMP": os.environ.get('TEMP'),
            "SYSTEM_TEMP": os.path.join(system_root, 'Temp'),
            "PREFETCH": os.path.join(system_root, 'Prefetch') if self.is_admin else None,
            "DISCORD": os.path.join(user_appdata, "discord", "Cache") if user_appdata else None,
            "SPOTIFY": os.path.join(user_local, "Spotify", "PersistentCache") if user_local else None
        }

        for key in self.config.get("targets", []):
            path_str = target_map.get(key)
            if path_str:
                p = Path(path_str)
                if p.exists():
                    paths.append(p)
            
        return paths

    def find_dev_bloat(self, log_callback):
        log_callback("Hunting for Dev-Bloat (node_modules/venv)...")
        home = Path.home()
        bloat_found = []
        # Professional standard: Search up to 3 levels deep (e.g., Documents/Projects/App/node_modules)
        try:
            for p in home.iterdir():
                if p.is_dir() and not p.name.startswith('.'):
                    # Level 1
                    for p2 in p.iterdir():
                        try:
                            if p2.is_dir():
                                if p2.name in ["node_modules", "venv", ".venv"]:
                                    if (time.time() - p2.stat().st_mtime) > (30 * 24 * 3600):
                                        bloat_found.append(p2)
                                else:
                                    # Level 2
                                    for p3 in p2.iterdir():
                                        if p3.is_dir() and p3.name in ["node_modules", "venv", ".venv"]:
                                            if (time.time() - p3.stat().st_mtime) > (30 * 24 * 3600):
                                                bloat_found.append(p3)
                        except PermissionError: continue
        except Exception as e:
            logger.error(f"Dev-Bloat hunt failed: {e}")
        return bloat_found

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        now = time.time()
        grace_period = self.config.get("grace_period_hours", 24) * 3600

        for target in self.get_target_paths():
            log_callback(f"Scanning: {target.name}...")
            try:
                for item in target.iterdir():
                    try:
                        if (now - item.stat().st_mtime) > grace_period:
                            size = self.get_size(item)
                            self.last_scan_results.append((item, size))
                            total_size += size
                    except (PermissionError, FileNotFoundError):
                        continue
            except Exception as e:
                logger.error(f"Failed to scan {target}: {e}")
        
        if self.config.get("dev_bloat_hunter"):
            for path in self.find_dev_bloat(log_callback):
                size = self.get_size(path)
                self.last_scan_results.append((path, size))
                total_size += size
        
        return len(self.last_scan_results), total_size

    def clean(self, log_callback):
        files_deleted = 0
        size_cleared = 0
        
        for item_path, size in self.last_scan_results:
            try:
                log_callback(f"Deleting: {item_path.name}")
                if item_path.is_file() or item_path.is_symlink():
                    item_path.unlink()
                elif item_path.is_dir():
                    shutil.rmtree(item_path)
                files_deleted += 1
                size_cleared += size
            except PermissionError:
                log_callback(f"Skipped: {item_path.name} (In use)")
            except Exception as e:
                logger.error(f"Delete failed for {item_path}: {e}")
                log_callback(f"Error: {item_path.name} (Check logs)")
        
        if self.config.get("empty_recycle_bin"):
            log_callback("Emptying Recycle Bin...")
            try:
                # Flags: SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except Exception as e:
                logger.error(f"Recycle bin failure: {e}")

        return files_deleted, size_cleared