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
        # Ensure absolute path for config
        if not os.path.isabs(config_path):
            base_dir = Path(__file__).parent
            self.config_path = base_dir / config_path
        else:
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

    def get_size(self, path: Path, timeout=5):
        """High-performance size calculation with a safety timeout"""
        start_time = time.time()
        try:
            if path.is_file():
                return path.stat().st_size
            total = 0
            with os.scandir(path) as it:
                for entry in it:
                    if time.time() - start_time > timeout:
                        return total
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += self.get_size(Path(entry.path), timeout - (time.time() - start_time))
                    except (PermissionError, FileNotFoundError):
                        continue
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
        """Optimized recursive search with intelligent path skipping"""
        if depth > max_depth:
            return []
        
        # Folders to completely ignore to save time
        ignore_list = ["AppData", "Documents", "Pictures", "Music", "Videos", "Desktop", 
                       ".git", ".vscode", "node_modules", "venv", ".venv", "Downloads"]
        
        found = []
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name in ignore_list:
                            if entry.name in ["node_modules", "venv", ".venv"]:
                                try:
                                    if (time.time() - entry.stat().st_mtime) > (30 * 24 * 3600):
                                        found.append(Path(entry.path))
                                except Exception: pass
                            continue
                        
                        if not entry.name.startswith("."):
                            found.extend(self.find_bloat_recursive(Path(entry.path), depth + 1, max_depth, log_callback))
        except (PermissionError, FileNotFoundError):
            pass
        except Exception as e:
            logger.debug(f"Scan error at {current_path}: {e}")
            
        return found

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        now = time.time()
        grace_period = self.config.get("grace_period_hours", 24) * 3600
        whitelist = ["Lenovo", "Microsoft", "Package Cache", "Temp", "Speech", "SGR"]

        # 1. Standard Targets (System/App Caches)
        for target, cat in self.get_standard_targets():
            log_callback(f"Scanning: {cat}...")
            try:
                for item in target.iterdir():
                    # Skip whitelisted items during scan so they don't appear in results
                    if item.name in whitelist:
                        continue
                        
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

    def calculate_health_score(self, total_bytes):
        """
        Calculates health percentage based on total junk size.
        Threshold: 1GB = 100% full (Needs cleaning)
        Uses logarithmic scaling so small amounts don't look scary.
        """
        if total_bytes < 1024 * 1024 * 10: # Under 10MB is basically 0%
            return 0
        
        # 1GB threshold for 'Full' meter
        max_junk = 1024 * 1024 * 1024 
        
        import math
        # Logarithmic scale: percentage = log(size) / log(max)
        # This makes the first 100MB feel more significant than the last 100MB
        score = (math.log(total_bytes) / math.log(max_junk)) * 100
        return min(100, max(0, score))

    def clean(self, items_to_delete, log_callback):
        """Resilient Deletion: Send2Trash -> Direct Delete -> Log Failure"""
        files_deleted = 0
        size_cleared = 0
        
        # Whitelist of folders that should NEVER be touched (usually causes loops or errors)
        whitelist = ["Lenovo", "Microsoft", "Package Cache", "Temp"] # Specific named items to skip
        
        for item in items_to_delete:
            item_path = item['path']
            size = item['size']
            
            if item_path.name in whitelist:
                logger.debug(f"Skipping whitelisted item: {item_path}")
                continue

            try:
                log_callback(f"Cleaning: {item_path.name}")
                # Try professional trashing first
                try:
                    send2trash(str(item_path))
                except Exception:
                    # Fallback: Direct deletion if Recycle Bin is not available for this path
                    if item_path.is_file():
                        os.remove(item_path)
                    else:
                        import shutil
                        shutil.rmtree(item_path)
                
                files_deleted += 1
                size_cleared += size
            except PermissionError:
                log_callback(f"Skipped: {item_path.name} (In Use)")
            except Exception as e:
                logger.error(f"Permanent failure for {item_path}: {e}")
                log_callback(f"Error: {item_path.name}")
        
        if self.config.get("empty_recycle_bin"):
            log_callback("Finalizing: Emptying Recycle Bin...")
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except Exception as e:
                logger.error(f"Recycle bin failure: {e}")

        return files_deleted, size_cleared
