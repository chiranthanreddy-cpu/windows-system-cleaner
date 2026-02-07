import os
import shutil
import ctypes
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup internal engine logging
log_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / "WindowsSystemCleaner"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "engine_debug.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CleanerEngine")

class CleanerEngine:
    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.is_admin = self.check_admin()
        self.last_scan_results = [] # List of dicts: {'path': Path, 'size': int, 'category': str}

    def load_config(self):
        default_config = {
            "grace_period_hours": 24,
            "empty_recycle_bin": True,
            "targets": ["TEMP", "SYSTEM_TEMP", "PREFETCH", "DISCORD", "SPOTIFY"],
            "dev_bloat_hunter": False,
            "search_paths": [str(Path.home())] # Default to Home
        }
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    cfg = json.load(f)
                    # Ensure new keys exist if updating from older version
                    for k, v in default_config.items():
                        if k not in cfg: cfg[k] = v
                    return cfg
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
            # Faster iterative size calculation
            total = 0
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += self.get_size(Path(entry.path))
            return total
        except Exception:
            return 0

    def format_bytes(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def get_standard_targets(self):
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
                    paths.append((p, key))
        return paths

    def find_dev_bloat(self, base_path: Path, log_callback):
        bloat_found = []
        try:
            # Professional standard: os.scandir for high-speed traversal
            with os.scandir(base_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False) and not entry.name.startswith('.'):
                        # Check L1
                        if entry.name in ["node_modules", "venv", ".venv"]:
                            if (time.time() - entry.stat().st_mtime) > (30 * 24 * 3600):
                                bloat_found.append(Path(entry.path))
                        else:
                            # Check L2/L3
                            try:
                                with os.scandir(entry.path) as it2:
                                    for entry2 in it2:
                                        if entry2.is_dir(follow_symlinks=False):
                                            if entry2.name in ["node_modules", "venv", ".venv"]:
                                                if (time.time() - entry2.stat().st_mtime) > (30 * 24 * 3600):
                                                    bloat_found.append(Path(entry2.path))
                            except PermissionError: continue
        except Exception as e:
            logger.error(f"Dev-Bloat scan failed for {base_path}: {e}")
        return bloat_found

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        now = time.time()
        grace_period = self.config.get("grace_period_hours", 24) * 3600

        # 1. Standard Targets
        for target, cat in self.get_standard_targets():
            log_callback(f"Scanning: {cat}...")
            try:
                for item in target.iterdir():
                    try:
                        if (now - item.stat().st_mtime) > grace_period:
                            size = self.get_size(item)
                            self.last_scan_results.append({'path': item, 'size': size, 'category': cat})
                            total_size += size
                    except (PermissionError, FileNotFoundError):
                        continue
            except Exception as e:
                logger.error(f"Failed to scan {target}: {e}")
        
        # 2. Custom Dev-Bloat Paths
        if self.config.get("dev_bloat_hunter"):
            for path_str in self.config.get("search_paths", []):
                p = Path(path_str)
                if p.exists():
                    log_callback(f"Hunting in: {p.name}...")
                    for bloat_path in self.find_dev_bloat(p, log_callback):
                        size = self.get_size(bloat_path)
                        self.last_scan_results.append({'path': bloat_path, 'size': size, 'category': 'DEV-BLOAT'})
                        total_size += size
        
        return self.last_scan_results

    def clean(self, items_to_delete, log_callback):
        """Accepted items_to_delete: list of dicts from scan result"""
        files_deleted = 0
        size_cleared = 0
        
        for item in items_to_delete:
            item_path = item['path']
            size = item['size']
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
                log_callback(f"Error: {item_path.name}")
        
        if self.config.get("empty_recycle_bin"):
            log_callback("Emptying Recycle Bin...")
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except Exception as e:
                logger.error(f"Recycle bin failure: {e}")

        return files_deleted, size_cleared
