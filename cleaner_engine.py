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
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager # Alias for backward compatibility/ease of use
        
        # Whitelist of folders that should NEVER be touched
        self.WHITELIST = ["Lenovo", "Microsoft", "Package Cache", "Temp", "Speech", "SGR"]
        
        self.is_admin = self.check_admin()
        self.last_scan_results = [] # List of dicts: {'path': Path, 'size': int, 'category': str}

    # Config loading/saving moved to ConfigManager


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
        
        # Folders to completely ignore to save time (Updated to allow traversing User/Documents/Desktop)
        ignore_list = ["AppData", "Pictures", "Music", "Videos", 
                       ".git", ".vscode", "node_modules", "venv", ".venv"]
        
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

    def _scan_category(self, target, cat, grace_period, log_callback):
        """Helper to scan a single category (Thread-safe execution)"""
        results = []
        local_total = 0
        now = time.time()
        
        try:
            log_callback(f"Scanning: {cat}...")
            for item in target.iterdir():
                if item.name in self.WHITELIST:
                    continue
                    
                try:
                    if (now - item.stat().st_mtime) > grace_period:
                        size = self.get_size(item)
                        results.append({'path': item, 'size': size, 'category': cat})
                        local_total += size
                except (PermissionError, FileNotFoundError):
                    continue
        except Exception as e:
            logger.error(f"Failed to scan {cat}: {e}")
            
        return results

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        grace_period = self.config.get("grace_period_hours", 24) * 3600
        
        import concurrent.futures
        
        # Use a ThreadPool to scan multiple targets at once
        # Max workers = 4 is usually a sweet spot for disk I/O on typical SSDs
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            stop_event = False # In case we want to add stop logic later
            futures = []
            
            # 1. Submit Standard Targets
            for target, cat in self.get_standard_targets():
                futures.append(executor.submit(self._scan_category, target, cat, grace_period, log_callback))
            
            # 2. Submit Dev-Bloat (Recursive)
            if self.config.get("dev_bloat_hunter"):
                max_depth = self.config.get("max_scan_depth", 3)
                for path_str in self.config.get("search_paths", []):
                    p = Path(path_str)
                    if p.exists():
                        # We wrap the recursive search in a lambda or helper to fit the executor signature if needed
                        # But here we can just define a wrapper task
                        def _scan_bloat(path_to_scan):
                             log_callback(f"Hunting in: {path_to_scan.name}...")
                             found = []
                             bloat_items = self.find_bloat_recursive(path_to_scan, 1, max_depth, log_callback)
                             for bloat_path in bloat_items:
                                 size = self.get_size(bloat_path)
                                 found.append({'path': bloat_path, 'size': size, 'category': 'DEV-BLOAT'})
                             return found
                        
                        futures.append(executor.submit(_scan_bloat, p))
            
            # 3. Collect Results
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    self.last_scan_results.extend(res)
                except Exception as e:
                    logger.error(f"Scan thread failed: {e}")
        
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

        
        for item in items_to_delete:
            item_path = item['path']
            size = item['size']
            
            if item_path.name in self.WHITELIST:
                logger.debug(f"Skipping whitelisted item: {item_path}")
                continue

            try:
                log_callback(f"Cleaning: {item_path.name}")
                # Try professional trashing first
                try:
                    send2trash(str(item_path))
                except Exception:
                    logger.error(f"Send2Trash failed for {item_path}. Skipping permanent delete for safety.")
                    log_callback(f"Error: Recycle Bin unavailable for {item_path.name}")
                    continue
                
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
