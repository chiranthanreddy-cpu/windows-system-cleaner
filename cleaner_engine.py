import os
import ctypes
import json
import time
import logging
from pathlib import Path
from send2trash import send2trash

# Professional logging: Module-level logger (Configured by the entry point)
logger = logging.getLogger(__name__)

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
            "search_paths": [str(Path.home())],
            "max_scan_depth": 3
        }
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    cfg = json.load(f)
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

        paths = []
        for key in self.config.get("targets", []):
            path_str = target_map.get(key)
            if path_str:
                p = Path(path_str)
                if p.exists():
                    paths.append((p, key))
        return paths

    def find_bloat_recursive(self, current_path: Path, depth: int, max_depth: int, log_callback):
        """Elegant recursive search for dev artifacts"""
        if depth > max_depth:
            return []
        
        found = []
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        # Professional target detection
                        if entry.name in ["node_modules", "venv", ".venv"]:
                            # Check if older than 30 days
                            if (time.time() - entry.stat().st_mtime) > (30 * 24 * 3600):
                                found.append(Path(entry.path))
                        else:
                            # Recurse deeper if not a target
                            found.extend(self.find_bloat_recursive(Path(entry.path), depth + 1, max_depth, log_callback))
        except (PermissionError, FileNotFoundError):
            pass
        except Exception as e:
            logger.error(f"Error in recursive scan at {current_path}: {e}")
            
        return found

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        now = time.time()
        grace_period = self.config.get("grace_period_hours", 24) * 3600

        # 1. Standard Targets (System/App Caches)
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
        
        # 2. Custom Dev-Bloat Paths (Recursive)
        if self.config.get("dev_bloat_hunter"):
            max_depth = self.config.get("max_scan_depth", 3)
            for path_str in self.config.get("search_paths", []):
                p = Path(path_str)
                if p.exists():
                    log_callback(f"Hunting in: {p.name}...")
                    bloat_items = self.find_bloat_recursive(p, 1, max_depth, log_callback)
                    for bloat_path in bloat_items:
                        size = self.get_size(bloat_path)
                        self.last_scan_results.append({'path': bloat_path, 'size': size, 'category': 'DEV-BLOAT'})
                        total_size += size
        
        return self.last_scan_results

    def clean(self, items_to_delete, log_callback):
        """Professional Deletion using Send2Trash (Move to Recycle Bin)"""
        files_deleted = 0
        size_cleared = 0
        
        for item in items_to_delete:
            item_path = item['path']
            size = item['size']
            try:
                log_callback(f"Trashing: {item_path.name}")
                # Industry standard: Send to Recycle Bin for safety
                send2trash(str(item_path))
                files_deleted += 1
                size_cleared += size
            except PermissionError:
                log_callback(f"Skipped: {item_path.name} (In use)")
            except Exception as e:
                logger.error(f"Failed to trash {item_path}: {e}")
                log_callback(f"Error: {item_path.name}")
        
        if self.config.get("empty_recycle_bin"):
            log_callback("Finalizing: Emptying Recycle Bin...")
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except Exception as e:
                logger.error(f"Recycle bin failure: {e}")

        return files_deleted, size_cleared