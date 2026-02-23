import json
import logging
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.config = self.load_config()

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
                    # Merge with defaults to ensure new keys exist
                    for k, v in default_config.items():
                        if k not in cfg:
                            cfg[k] = v
                    return cfg
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
        
        return default_config

    def save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __contains__(self, key):
        return key in self.config
