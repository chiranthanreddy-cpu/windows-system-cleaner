import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
import ctypes
import threading
import logging
from datetime import datetime
from PIL import Image
from pathlib import Path
from collections import deque
import time

# Import Modular Engine
from cleaner_engine import CleanerEngine
from resource_manager import ResourceManager
from config_manager import ConfigManager

try:
    import pyi_splash
except ImportError:
    pyi_splash = None

# Configure Logging
log_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / "WindowsSystemCleaner"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(log_dir / "engine_debug.log"),
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============= OPTIMIZED CIRCULAR GAUGE =============
class CircularGauge(ctk.CTkCanvas):
    """Smooth animated gauge with spring physics"""
    def __init__(self, parent, size=150, color="#58A6FF", **kwargs):
        super().__init__(parent, width=size, height=size, bg="#161B22", highlightthickness=0, **kwargs)
        self.size = size
        self.target_color = color
        self.current_color = color
        self.percent = 0
        self.target_percent = 0
        self.velocity = 0  # For spring physics
        self.animation_id = None
        self.draw()

    def set_percent(self, p, animate=True):
        """Set percentage with optional spring animation"""
        self.target_percent = max(0, min(100, p))
        if animate:
            if self.animation_id is None:
                self.animate_spring()
        else:
            self.percent = self.target_percent
            self.velocity = 0
            self.draw()

    def animate_spring(self):
        """Spring physics for smooth, natural animation"""
        stiffness = 0.15  # How fast it moves toward target
        damping = 0.7     # How much it slows down
        
        # Calculate spring force
        force = (self.target_percent - self.percent) * stiffness
        self.velocity += force
        self.velocity *= damping
        
        # Update position
        self.percent += self.velocity
        
        # Stop when close enough (prevents infinite tiny movements)
        if abs(self.target_percent - self.percent) < 0.1 and abs(self.velocity) < 0.1:
            self.percent = self.target_percent
            self.velocity = 0
            self.animation_id = None
            self.draw()
            return
        
        self.draw()
        self.animation_id = self.after(16, self.animate_spring)  # 60 FPS

    def draw(self):
        """Optimized drawing with reduced redraws"""
        self.delete("all")
        padding = 10
        width = 12
        
        # Background arc
        self.create_arc(padding, padding, self.size-padding, self.size-padding, 
                        start=225, extent=-270, outline="#0d1117", width=width, style="arc")
        
        # Progress arc
        if self.percent > 0:
            extent = -(self.percent / 100) * 270
            self.create_arc(padding, padding, self.size-padding, self.size-padding, 
                            start=225, extent=extent, outline=self.target_color, width=width, style="arc")
        
        # Text
        self.create_text(self.size/2, self.size/2, text=f"{int(self.percent)}%", 
                         fill="#E6EDF3", font=("Segoe UI Variable Display", 32, "bold"))


# ============= VIRTUAL SCROLLING LIST =============
class VirtualScrollList(ctk.CTkScrollableFrame):
    """High-performance list that only renders visible items"""
    def __init__(self, parent, item_height=50, **kwargs):
        super().__init__(parent, **kwargs)
        self.item_height = item_height
        self.items = []
        self.visible_widgets = []
        self.checkbox_vars = []
        self.last_scroll_pos = 0
        self.render_batch_size = 50  # Render items in batches
        
        # Bind scroll event for dynamic rendering
        self._parent_canvas.bind("<Configure>", self._on_scroll)
    
    def set_items(self, items, on_change_callback):
        """Set items and render visible ones"""
        self.items = items
        self.on_change = on_change_callback
        self.checkbox_vars = []
        
        # Clear existing widgets
        for widget in self.visible_widgets:
            widget.destroy()
        self.visible_widgets = []
        
        # Render in batches to avoid UI freeze
        self._render_batch(0)
    
    def _render_batch(self, start_idx):
        """Render a batch of items progressively"""
        end_idx = min(start_idx + self.render_batch_size, len(self.items))
        
        for i in range(start_idx, end_idx):
            self._create_item_widget(self.items[i], i)
        
        # Schedule next batch if more items exist
        if end_idx < len(self.items):
            self.after(10, lambda: self._render_batch(end_idx))
    
    def _create_item_widget(self, item, index):
        """Create a single item widget"""
        var = tk.StringVar(value="on")
        self.checkbox_vars.append((item, var))
        
        # Card style row
        row = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=8)
        row.pack(fill="x", pady=4, padx=5)
        
        # Hover effect with lambda capture
        def make_hover_handlers(frame):
            return (
                lambda e: frame.configure(fg_color="#21262D"),
                lambda e: frame.configure(fg_color="#161B22")
            )
        
        enter_handler, leave_handler = make_hover_handlers(row)
        row.bind("<Enter>", enter_handler)
        row.bind("<Leave>", leave_handler)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        
        # Checkbox with debounced callback
        cb = ctk.CTkCheckBox(
            inner, 
            text=f"  {item['path'].name}", 
            variable=var, 
            onvalue="on", 
            offvalue="off",
            checkbox_width=20, 
            checkbox_height=20, 
            corner_radius=6,
            border_width=2, 
            fg_color="#2f81f7",
            hover_color="#2f81f7", 
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=13),
            command=self.on_change
        )
        cb.pack(side="left")
        
        # Metadata
        meta_frame = ctk.CTkFrame(inner, fg_color="transparent")
        meta_frame.pack(side="right")
        
        # Category badge
        ctk.CTkLabel(
            meta_frame, 
            text=item['category'], 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#7D8590",
            fg_color="#0D1117", 
            corner_radius=4
        ).pack(side="left", padx=(0, 10))
        
        # Size label
        size_text = self._format_bytes(item['size'])
        ctk.CTkLabel(
            meta_frame, 
            text=size_text, 
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=13, weight="bold"), 
            text_color="#E6EDF3"
        ).pack(side="left")
        
        self.visible_widgets.append(row)
    
    def _format_bytes(self, size):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def _on_scroll(self, event):
        """Handle scroll events (placeholder for future optimization)"""
        pass
    
    def get_selected_items(self):
        """Get all selected items"""
        return [item for item, var in self.checkbox_vars if var.get() == "on"]
    
    def select_all(self):
        """Select all items"""
        for item, var in self.checkbox_vars:
            var.set("on")
        self.on_change()
    
    def deselect_all(self):
        """Deselect all items"""
        for item, var in self.checkbox_vars:
            var.set("off")
        self.on_change()


# ============= MAIN APP =============
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows System Cleaner")
        self.geometry("1100x800")
        
        # Modern color palette
        self.colors = {
            "bg": "#0D1117",
            "sidebar": "#010409",
            "card": "#161B22",
            "card_hover": "#21262D",
            "accent": "#2f81f7",
            "text": "#E6EDF3",
            "text_dim": "#7D8590",
            "success": "#2EA043",
            "danger": "#DA3633",
            "border": "#30363D"
        }
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.colors["bg"])
        
        # App ID for Windows taskbar
        myappid = 'com.chiru.windowssystemcleaner.v1.3'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        self.base_path = Path(__file__).parent
        self.rm = ResourceManager(self.base_path)
        
        # Load icon
        icon_path = self.rm.get_path("logo.ico")
        if icon_path:
            try:
                self.iconbitmap(str(icon_path))
            except Exception as e:
                logging.warning(f"Could not load icon: {e}")

        # Initialize engine
        log_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / "WindowsSystemCleaner"
        log_dir.mkdir(exist_ok=True)
        self.config_manager = ConfigManager(str(log_dir / "config.json"))
        self.engine = CleanerEngine(self.config_manager)
        
        # State management
        self.scan_results = []
        self.scan_active = False
        self.debounce_timer = None  # For debounced updates
        
        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Setup UI
        self.setup_sidebar()
        self.setup_content_areas()
        self.show_dash()

        # Close splash screen
        if pyi_splash:
            self.after(200, self.close_splash)
        
        # First-run setup prompt
        self.after(1000, self.check_first_run_install)

    def check_first_run_install(self):
        """Prompt user to install on first run"""
        shortcut_path = os.path.join(
            os.environ["APPDATA"], 
            "Microsoft", 
            "Windows", 
            "Start Menu", 
            "Programs", 
            "Windows System Cleaner.lnk"
        )
        if not os.path.exists(shortcut_path):
            if messagebox.askyesno(
                "Easy Setup", 
                "Would you like to add Windows System Cleaner to your Start Menu for easy access?"
            ):
                self.create_start_menu_shortcut()

    def close_splash(self):
        """Close PyInstaller splash screen"""
        if pyi_splash:
            try:
                pyi_splash.close()
            except:
                pass

    def setup_sidebar(self):
        """Create sidebar navigation"""
        self.sidebar = ctk.CTkFrame(
            self, 
            width=260, 
            corner_radius=0, 
            fg_color=self.colors["sidebar"], 
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo
        self.logo_image = self.rm.get_image("logo.png", size=(72, 72))
        if self.logo_image:
            ctk.CTkLabel(self.sidebar, image=self.logo_image, text="").pack(pady=(40, 0))
        else:
            ctk.CTkLabel(self.sidebar, text="🛡", font=ctk.CTkFont(size=56)).pack(pady=(40, 0))

        # Title
        ctk.CTkLabel(
            self.sidebar, 
            text="SYSTEM\nCLEANER", 
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=20, weight="bold"),
            text_color=self.colors["text"]
        ).pack(pady=(15, 40))
        
        # Navigation buttons
        self.btn_dash = self.create_nav_button("Dashboard", self.show_dash)
        self.btn_dash.pack(fill="x", padx=15, pady=5)
        
        self.btn_settings = self.create_nav_button("Settings", self.show_settings)
        self.btn_settings.pack(fill="x", padx=15, pady=5)
        
        # Footer
        ctk.CTkLabel(
            self.sidebar, 
            text="🛡 100% Local Execution", 
            text_color=self.colors["success"], 
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="bottom", pady=30)
                     
    def create_nav_button(self, text, command):
        """Create styled navigation button"""
        return ctk.CTkButton(
            self.sidebar, 
            text=f"  {text}", 
            fg_color="transparent", 
            text_color=self.colors["text_dim"],
            hover_color=self.colors["card_hover"],
            anchor="w", 
            height=48,
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=14, weight="bold"),
            command=command,
            corner_radius=8
        )

    def setup_content_areas(self):
        """Initialize content frame containers"""
        self.content_dash = ctk.CTkFrame(self, fg_color="transparent")
        self.content_settings = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_dashboard()
        self.setup_settings_view()

    def setup_dashboard(self):
        """Create dashboard UI with optimized components"""
        self.entrance_animated = False
        # Header
        header = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        header.pack(fill="x", pady=(0, 25))
        ctk.CTkLabel(
            header, 
            text="Overview", 
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=32, weight="bold"), 
            text_color=self.colors["text"]
        ).pack(side="left")
        
        # Health meter hero section
        hero_frame = ctk.CTkFrame(
            self.content_dash, 
            fg_color=self.colors["card"], 
            corner_radius=16, 
            border_width=1, 
            border_color=self.colors["border"]
        )
        hero_frame.pack(fill="x", pady=10)
        
        # Gauge container (left side)
        gauge_container = ctk.CTkFrame(hero_frame, fg_color="transparent")
        gauge_container.pack(side="left", padx=45, pady=30)
        
        self.gauge = CircularGauge(gauge_container, size=150, color=self.colors["accent"])
        self.gauge.pack()
        
        # Status text (right side)
        info_side = ctk.CTkFrame(hero_frame, fg_color="transparent")
        info_side.pack(side="left", fill="both", expand=True, padx=15)
        
        self.health_lbl = ctk.CTkLabel(
            info_side, 
            text="Ready to Scan", 
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"), 
            text_color=self.colors["text"], 
            anchor="w"
        )
        self.health_lbl.pack(fill="x", pady=(40, 5))
        
        self.health_desc = ctk.CTkLabel(
            info_side, 
            text="Analyze your system to reclaim valuable space.", 
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=14), 
            text_color=self.colors["text_dim"], 
            anchor="w"
        )
        self.health_desc.pack(fill="x")

        # Stats cards
        stats_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        stats_row.pack(fill="x", pady=20)
        
        self.card_files = self.create_card(stats_row, "Items Detected", "0", "📁")
        self.card_files.pack(side="left", expand=True, fill="both", padx=(0, 10))
        
        self.card_size = self.create_card(stats_row, "Reclaimable", "0 KB", "💾")
        self.card_size.pack(side="left", expand=True, fill="both", padx=(10, 0))

        # Action buttons
        btn_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        btn_row.pack(fill="x", pady=10)
        
        self.btn_analyze = ctk.CTkButton(
            btn_row, 
            text="Generate Report", 
            height=50, 
            fg_color=self.colors["accent"], 
            hover_color="#4091f7",
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=14, weight="bold"), 
            corner_radius=8,
            command=self.start_analyze
        )
        self.btn_analyze.pack(side="left", expand=True, fill="x", padx=(0, 8))
        
        self.btn_clean = ctk.CTkButton(
            btn_row, 
            text="Clean Selected", 
            height=50, 
            fg_color=self.colors["danger"], 
            hover_color="#FF6A67",
            state="disabled", 
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=14, weight="bold"), 
            corner_radius=8,
            command=self.start_clean
        )
        self.btn_clean.pack(side="left", expand=True, fill="x", padx=(8, 0))

        # Results Container (Holds selection controls + list)
        self.results_container = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        self.results_container.pack(fill="both", expand=True, pady=10)

        # Selection controls (Inside container)
        self.selection_frame = ctk.CTkFrame(self.results_container, fg_color="transparent")
        self.selection_frame.pack(fill="x", pady=(0, 5))
        
        self.btn_select_all = ctk.CTkButton(
            self.selection_frame, 
            text="Select All", 
            width=80,
            height=24,
            fg_color="transparent", 
            text_color=self.colors["accent"],
            hover_color=self.colors["card_hover"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.results_list.select_all()
        )
        self.btn_select_all.pack(side="right", padx=5)
        
        self.btn_select_none = ctk.CTkButton(
            self.selection_frame, 
            text="Select None", 
            width=80,
            height=24,
            fg_color="transparent", 
            text_color=self.colors["text_dim"],
            hover_color=self.colors["card_hover"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.results_list.deselect_all()
        )
        self.btn_select_none.pack(side="right", padx=5)
        self.selection_frame.pack_forget() # Hide initially

        # Virtual scrolling results list (Inside container)
        self.results_list = VirtualScrollList(
            self.results_container, 
            fg_color="transparent",
            border_width=0, 
            corner_radius=0
        )
        self.results_list.pack(fill="both", expand=True)

        # Status bar
        self.status_lbl = ctk.CTkLabel(
            self.content_dash, 
            text="Shielding your privacy. 100% Local-Only.", 
            font=ctk.CTkFont(size=12), 
            text_color=self.colors["text_dim"]
        )
        self.status_lbl.pack(anchor="w", pady=(10, 0))

        # Smooth entrance animations
        self.dash_widgets = [header, hero_frame, stats_row, btn_row, self.results_container, self.status_lbl]
        for w in self.dash_widgets:
            w.pack_forget()
        # self.animate_entrance(0)  <-- REMOVED: Called in switch_view instead

    def animate_entrance(self, index):
        """Staggered entrance animation for dashboard widgets"""
        if index < len(self.dash_widgets):
            widget = self.dash_widgets[index]
            
            # Determine pack settings based on widget type
            if index < 4:
                widget.pack(fill="x", pady=10 if index < 4 else 0)
            elif index == 4: # Results container
                widget.pack(fill="both", expand=True, pady=10)
            else: # Status label
                widget.pack(anchor="w", pady=(10, 0))
            
            # Schedule next widget with stagger delay
            self.after(80, lambda: self.animate_entrance(index + 1))
        else:
            self.entrance_animated = True

    def create_card(self, parent, title, val, icon):
        """Create stat card widget"""
        f = ctk.CTkFrame(
            parent, 
            fg_color=self.colors["card"], 
            corner_radius=16, 
            border_width=1, 
            border_color=self.colors["border"]
        )
        
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(padx=20, pady=20, fill="both")
        
        # Icon
        icon_lbl = ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=32))
        icon_lbl.pack(side="left", padx=(0, 15))
        
        # Text container
        text_side = ctk.CTkFrame(inner, fg_color="transparent")
        text_side.pack(side="left", fill="both")
        
        # Title
        ctk.CTkLabel(
            text_side, 
            text=title.upper(), 
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"), 
            text_color=self.colors["text_dim"], 
            anchor="w"
        ).pack(fill="x")
        
        # Value
        lbl_val = ctk.CTkLabel(
            text_side, 
            text=val, 
            font=ctk.CTkFont(family="Segoe UI Variable Display", size=24, weight="bold"), 
            text_color=self.colors["text"], 
            anchor="w"
        )
        lbl_val.pack(fill="x")
        
        f.val_label = lbl_val
        return f

    def setup_settings_view(self):
        """Create settings panel"""
        ctk.CTkLabel(
            self.content_settings, 
            text="Application Settings", 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=self.colors["text"]
        ).pack(pady=(0, 20), anchor="w", padx=40)
        
        # Core preferences section
        s_frame = ctk.CTkFrame(
            self.content_settings, 
            fg_color=self.colors["card"], 
            corner_radius=20, 
            border_width=1, 
            border_color="#21262d"
        )
        s_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(
            s_frame, 
            text="CORE PREFERENCES", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color=self.colors["text_dim"]
        ).pack(pady=(15, 5), padx=30, anchor="w")

        # Grace period switch
        self.sw_grace = ctk.CTkSwitch(
            s_frame, 
            text="24-hour Safety Grace Period", 
            progress_color=self.colors["accent"],
            command=self.save_settings
        )
        self.sw_grace.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("grace_period_hours", 0) > 0:
            self.sw_grace.select()

        # Recycle bin switch
        self.sw_bin = ctk.CTkSwitch(
            s_frame, 
            text="Auto-Empty Recycle Bin", 
            progress_color=self.colors["accent"],
            command=self.save_settings
        )
        self.sw_bin.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("empty_recycle_bin"):
            self.sw_bin.select()

        # Dev-bloat hunter switch
        self.sw_dev = ctk.CTkSwitch(
            s_frame, 
            text="Enable Dev-Bloat Hunter", 
            progress_color=self.colors["accent"],
            command=self.save_settings
        )
        self.sw_dev.pack(pady=(10, 20), padx=30, anchor="w")
        if self.engine.config.get("dev_bloat_hunter"):
            self.sw_dev.select()

        # System integration section
        i_frame = ctk.CTkFrame(
            self.content_settings, 
            fg_color=self.colors["card"], 
            corner_radius=20, 
            border_width=1, 
            border_color="#21262d"
        )
        i_frame.pack(fill="x", padx=40, pady=10)
        
        self.btn_install = ctk.CTkButton(
            i_frame, 
            text="Add to Start Menu / Register App", 
            fg_color="transparent", 
            border_width=1,
            border_color=self.colors["accent"],
            text_color=self.colors["accent"],
            hover_color="#112131",
            command=self.create_start_menu_shortcut
        )
        self.btn_install.pack(pady=20, padx=30, fill="x")

        # Search paths section
        p_frame = ctk.CTkFrame(
            self.content_settings, 
            fg_color=self.colors["card"], 
            corner_radius=20, 
            border_width=1, 
            border_color="#21262d"
        )
        p_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        ctk.CTkLabel(
            p_frame, 
            text="DEV-BLOAT SEARCH PATHS", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color=self.colors["text_dim"]
        ).pack(pady=(15, 5), padx=30, anchor="w")
        
        self.path_listbox = ctk.CTkScrollableFrame(p_frame, fg_color="#0d1117", height=150)
        self.path_listbox.pack(fill="both", expand=True, padx=20, pady=5)
        self.refresh_path_list()
        
        ctk.CTkButton(
            p_frame, 
            text="+ Add Search Folder", 
            fg_color="transparent", 
            text_color=self.colors["accent"],
            font=ctk.CTkFont(weight="bold"),
            command=self.add_search_path
        ).pack(pady=15)

    def refresh_path_list(self):
        """Refresh the list of search paths"""
        for w in self.path_listbox.winfo_children():
            w.destroy()
        
        for path in self.engine.config.get("search_paths", []):
            row = ctk.CTkFrame(self.path_listbox, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=path, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            
            ctk.CTkButton(
                row, 
                text="X", 
                width=30, 
                fg_color="#e74c3c", 
                command=lambda p=path: self.remove_search_path(p)
            ).pack(side="right", padx=5)

    def add_search_path(self):
        """Add a new search path"""
        path = filedialog.askdirectory()
        if path and path not in self.engine.config["search_paths"]:
            self.engine.config["search_paths"].append(path)
            self.config_manager.save_config()
            self.refresh_path_list()

    def remove_search_path(self, path):
        """Remove a search path"""
        if path in self.engine.config["search_paths"]:
            self.engine.config["search_paths"].remove(path)
            self.config_manager.save_config()
            self.refresh_path_list()

    def save_settings(self):
        """Save settings to config"""
        self.engine.config["grace_period_hours"] = 24 if self.sw_grace.get() else 0
        self.engine.config["empty_recycle_bin"] = bool(self.sw_bin.get())
        self.engine.config["dev_bloat_hunter"] = bool(self.sw_dev.get())
        self.config_manager.save_config()

    def create_start_menu_shortcut(self):
        """Create Start Menu shortcut and register in Windows"""
        try:
            import win32com.client
            import winreg
            
            exe_path = str(Path(os.sys.executable if not getattr(os.sys, 'frozen', False) else os.sys.executable).absolute())
            if not exe_path.endswith(".exe"):
                exe_path = str((self.base_path.parent / "dist" / "WindowsSystemCleaner.exe").absolute())

            working_dir = str(Path(exe_path).parent)
            icon_path = self.rm.get_path("logo.ico")
            if icon_path:
                icon_path = str(icon_path.absolute())
            else:
                icon_path = ""
            
            shortcut_path = os.path.join(
                os.environ["APPDATA"], 
                "Microsoft", 
                "Windows", 
                "Start Menu", 
                "Programs", 
                "Windows System Cleaner.lnk"
            )

            # Create shortcut
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = working_dir
            shortcut.IconLocation = icon_path
            shortcut.save()

            # Register in Windows
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WindowsSystemCleaner"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Windows System Cleaner")
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.3.0")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Chiranthan Reddy")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, working_dir)
                
                uninstall_cmd = f'powershell.exe -Command "Remove-Item -Path \\"{shortcut_path}\\" -Force; Remove-Item -Path \\"{working_dir}\\" -Recurse -Force; Remove-Item -Path \\"HKCU:\\{reg_path}\\" -Force"'
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            
            messagebox.showinfo("Success", "Application successfully added to Start Menu and registered!")
        except Exception as e:
            logging.error(f"Failed to create shortcut: {e}")
            messagebox.showerror("Error", f"Failed to create shortcut: {e}")

    def switch_view(self, view_name):
        """Switch between dashboard and settings views"""
        # Hide all views
        self.content_dash.grid_forget()
        self.content_settings.grid_forget()
        
        # Reset button styles
        self.btn_dash.configure(fg_color="transparent", text_color=self.colors["text_dim"])
        self.btn_settings.configure(fg_color="transparent", text_color=self.colors["text_dim"])
        
        # Show selected view
        if view_name == "dashboard":
            self.content_dash.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
            self.btn_dash.configure(fg_color=self.colors["card"], text_color=self.colors["accent"])
            
            if not self.entrance_animated:
                self.animate_entrance(0)
            else:
                # Instant restore
                for w in self.dash_widgets:
                    # Determine pack settings based on widget index/type similar to animate_entrance
                    if w in [self.dash_widgets[0], self.dash_widgets[1], self.dash_widgets[2], self.dash_widgets[3]]:
                         w.pack(fill="x", pady=10)
                    elif w == self.results_container:
                         w.pack(fill="both", expand=True, pady=10)
                    else: # Status
                         w.pack(anchor="w", pady=(10, 0))

        elif view_name == "settings":
            self.content_settings.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
            self.btn_settings.configure(fg_color=self.colors["card"], text_color=self.colors["accent"])

    def show_dash(self):
        """Show dashboard view"""
        self.switch_view("dashboard")

    def show_settings(self):
        """Show settings view"""
        self.switch_view("settings")

    def update_live_stats(self):
        """Debounced update of stats when selection changes"""
        # Cancel pending update
        if self.debounce_timer:
            self.after_cancel(self.debounce_timer)
        
        # Schedule new update after 100ms (debounce)
        self.debounce_timer = self.after(100, self._do_update_stats)
    
    def _do_update_stats(self):
        """Actual stats update (called after debounce)"""
        selected_items = self.results_list.get_selected_items()
        total_size = sum(item['size'] for item in selected_items)
        
        # Update size card
        self.card_size.val_label.configure(text=self.engine.format_bytes(total_size))
        
        # Enable/disable clean button
        self.btn_clean.configure(state="normal" if selected_items else "disabled")

    def start_analyze(self):
        """Start system analysis"""
        # Disable buttons
        self.btn_analyze.configure(state="disabled")
        self.btn_clean.configure(state="disabled")
        
        # Update UI status
        self.health_lbl.configure(text="SCANNING SYSTEM...", text_color=self.colors["accent"])
        self.health_desc.configure(text="Searching for temporary files and app caches...")
        self.gauge.set_percent(0)
        
        # Start scanning animation
        self.scan_active = True
        self.animate_gauge_scanning()
        
        # Start scan in background thread
        threading.Thread(target=self.work_analyze, daemon=True).start()

    def animate_gauge_scanning(self):
        """Indeterminate progress animation during scan"""
        if self.scan_active:
            # Pulse between 0-30% for scanning visual feedback
            val = (self.gauge.percent + 3) % 30
            self.gauge.set_percent(val, animate=False)
            self.after(80, self.animate_gauge_scanning)  # Slower for less CPU usage

    def work_analyze(self):
        """Background worker for analysis"""
        try:
            results = self.engine.scan(
                lambda m: self.after(0, lambda msg=m: self.status_lbl.configure(text=msg))
            )
            self.after(0, lambda: self.finish_analyze(results))
        except Exception as e:
            logging.error(f"Scan failed: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {e}"))
        finally:
            self.scan_active = False
            self.after(0, self.stop_progress)

    def finish_analyze(self, results):
        """Process and display scan results"""
        self.scan_results = results
        total_size = sum(item['size'] for item in results)
        
        # Update file count
        self.card_files.val_label.configure(text=str(len(results)))
        
        # Calculate and display health score
        health_percent = self.engine.calculate_health_score(total_size)
        self.gauge.set_percent(health_percent, animate=True)
        
        # Update status based on results
        if not results or total_size < 1024 * 1024 * 10:  # Under 10MB
            self.health_lbl.configure(text="System Optimized", text_color=self.colors["success"])
            self.health_desc.configure(text="Your PC is in great shape! No significant junk found.")
            self.gauge.target_color = self.colors["success"]
        elif health_percent < 50:
            self.health_lbl.configure(text="Cleanup Recommended", text_color=self.colors["accent"])
            self.health_desc.configure(text=f"We found {self.engine.format_bytes(total_size)} of redundant files.")
            self.gauge.target_color = self.colors["accent"]
        else:
            self.health_lbl.configure(text="Action Recommended", text_color=self.colors["danger"])
            self.health_desc.configure(text=f"Reclaim {self.engine.format_bytes(total_size)} to boost performance.")
            self.gauge.target_color = self.colors["danger"]
        
        # Render results in virtual list
        self.results_list.set_items(results, self.update_live_stats)
        
        # Show selection controls directly above results_list
        # Since both are in results_container and results_list is always packed, before= works.
        self.selection_frame.pack(fill="x", pady=(0, 5))
        
        # Update initial stats
        self.update_live_stats()
        self.status_lbl.configure(text="Analysis complete. Ready to clean.")

    def start_clean(self):
        """Start cleaning selected items"""
        items_to_del = self.results_list.get_selected_items()
        if not items_to_del:
            return
        
        # Confirmation dialog
        msg = f"Move {len(items_to_del)} items to Recycle Bin?"
        if self.engine.config.get("empty_recycle_bin"):
            msg += "\n\n⚠️ WARNING: 'Empty Recycle Bin' is ENABLED."
        
        if messagebox.askyesno("Confirm Cleanup", msg):
            # Disable buttons
            self.btn_clean.configure(state="disabled")
            self.btn_analyze.configure(state="disabled")
            
            # Update status
            self.health_lbl.configure(text="CLEANING...", text_color=self.colors["accent"])
            
            # Start cleaning in background
            threading.Thread(target=self.work_clean, args=(items_to_del,), daemon=True).start()

    def work_clean(self, items):
        """Background worker for cleaning"""
        try:
            count, size = self.engine.clean(
                items, 
                lambda m: self.after(0, lambda msg=m: self.status_lbl.configure(text=msg))
            )
            self.after(0, lambda: self.finish_clean(count, size))
        except Exception as e:
            logging.error(f"Clean failed: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Clean failed: {e}"))
        finally:
            self.after(0, self.stop_progress)

    def finish_clean(self, count, size):
        """Update UI after cleaning completes"""
        # Update status
        self.health_lbl.configure(text="OPTIMIZED", text_color=self.colors["success"])
        self.health_desc.configure(text=f"Successfully reclaimed {self.engine.format_bytes(size)}.")
        
        # Animate gauge to success
        self.gauge.target_color = self.colors["success"]
        self.gauge.set_percent(0, animate=True)
        
        # Show success message
        messagebox.showinfo("Success", f"Reclaimed {self.engine.format_bytes(size)}!")
        
        # Reset UI
        self.card_files.val_label.configure(text="0")
        self.results_list.set_items([], self.update_live_stats)
        self.selection_frame.pack_forget() # Hide selection controls
        self.update_live_stats()

    def stop_progress(self):
        """Re-enable analyze button after operation"""
        self.btn_analyze.configure(state="normal")


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"Fatal Error:\n{traceback.format_exc()}"
        logging.critical(error_msg)
        try:
            temp_root = tk.Tk()
            temp_root.withdraw()
            messagebox.showerror("Startup Error", error_msg)
            temp_root.destroy()
        except:
            print(error_msg)