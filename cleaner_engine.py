import os
import shutil
import ctypes
import json
import time
from datetime import datetime

class CleanerEngine:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
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
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except: pass
        return default_config

    def save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except: pass

    def check_admin(self):
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except: return False

    def get_size(self, path):
        try:
            if os.path.isfile(path): return os.path.getsize(path)
            total = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp): total += os.path.getsize(fp)
            return total
        except: return 0

    def format_bytes(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024: return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def get_target_paths(self):
        paths = []
        user_appdata = os.environ.get('APPDATA')
        user_local = os.environ.get('LOCALAPPDATA')
        
        if "TEMP" in self.config["targets"]:
            paths.append(os.environ.get('TEMP'))
        if "SYSTEM_TEMP" in self.config["targets"]:
            paths.append(os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Temp'))
        if self.is_admin and "PREFETCH" in self.config["targets"]:
            paths.append(os.path.join(os.environ.get('SystemRoot', 'C:\Windows'), 'Prefetch'))
        
        if "DISCORD" in self.config["targets"] and user_appdata:
            discord_cache = os.path.join(user_appdata, "discord", "Cache")
            if os.path.exists(discord_cache): paths.append(discord_cache)
            
        if "SPOTIFY" in self.config["targets"] and user_local:
            spotify_cache = os.path.join(user_local, "Spotify", "PersistentCache")
            if os.path.exists(spotify_cache): paths.append(spotify_cache)
            
        return [p for p in paths if p and os.path.exists(p)]

    def find_dev_bloat(self, log_callback):
        log_callback("Hunting for Dev-Bloat (node_modules/venv)...")
        home = os.path.expanduser("~")
        bloat_found = []
        try:
            for root, dirs, _ in os.walk(home):
                if root.count(os.sep) - home.count(os.sep) > 2:
                    del dirs[:]
                    continue
                for d in dirs:
                    if d in ["node_modules", "venv", ".venv"]:
                        path = os.path.join(root, d)
                        if (time.time() - os.path.getmtime(path)) > (30 * 24 * 3600):
                            bloat_found.append(path)
        except: pass
        return bloat_found

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        now = time.time()
        grace_period = self.config["grace_period_hours"] * 3600

        for target in self.get_target_paths():
            log_callback(f"Scanning: {os.path.basename(target)}...")
            try:
                for item in os.listdir(target):
                    item_path = os.path.join(target, item)
                    try:
                        if (now - os.path.getmtime(item_path)) > grace_period:
                            size = self.get_size(item_path)
                            self.last_scan_results.append((item_path, size))
                            total_size += size
                    except: continue
            except: continue
        
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
                log_callback(f"Deleting: {os.path.basename(item_path)}")
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                files_deleted += 1
                size_cleared += size
            except:
                log_callback(f"Skipped: {os.path.basename(item_path)} (In use)")
        
        if self.config.get("empty_recycle_bin"):
            log_callback("Emptying Recycle Bin...")
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            except: pass

        return files_deleted, size_cleared
