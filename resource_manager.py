import logging
from pathlib import Path
from PIL import Image
import customtkinter as ctk

class ResourceManager:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.assets_path = self.base_path / "assets"
        self.logger = logging.getLogger(__name__)

    def get_path(self, filename):
        """Returns the absolute path to an asset if it exists, else None."""
        path = self.assets_path / filename
        return path if path.exists() else None

    def get_image(self, filename, size):
        """
        Returns a CTkImage object if the asset exists and is valid.
        Returns None if missing or invalid.
        """
        path = self.get_path(filename)
        if path:
            try:
                img = Image.open(path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            except Exception as e:
                self.logger.warning(f"Failed to load image {filename}: {e}")
        return None
