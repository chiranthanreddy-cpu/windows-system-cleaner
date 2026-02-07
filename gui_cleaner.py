import tkinter as tk
import customtkinter as ctk
import os
import shutil
import ctypes
import json
import threading
import time
from datetime import datetime
from PIL import Image

# --- Core Logic ---

class CleanerEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.is_admin = self.check_admin()
        self.last_scan_results = []

    def load_config(self):
        default_config = {
            "grace_period_hours": 24,
            "empty_recycle_bin": True,
            "targets": ["TEMP", "SYSTEM_TEMP", "PREFETCH", "DISCORD", "SPOTIFY"]
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
            paths.append(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'))
        if self.is_admin and "PREFETCH" in self.config["targets"]:
            paths.append(os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch'))
        
        # Surgical Strikes
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
        # Limit search to 2 levels deep to avoid scanning the entire drive
        try:
            for root, dirs, _ in os.walk(home):
                if root.count(os.sep) - home.count(os.sep) > 2:
                    del dirs[:] # Don't go deeper than 2 levels
                    continue
                
                for d in dirs:
                    if d in ["node_modules", "venv", ".venv"]:
                        path = os.path.join(root, d)
                        # Check if untouched for 30 days
                        if (time.time() - os.path.getmtime(path)) > (30 * 24 * 3600):
                            bloat_found.append(path)
        except: pass
        return bloat_found

    def scan(self, log_callback):
        self.last_scan_results = []
        total_size = 0
        now = time.time()
        grace_period = self.config["grace_period_hours"] * 3600

        # Standard Targets
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
        
        # Dev-Bloat Hunter (Optional/Experimental)
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

# --- UI ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows System Cleaner")
        self.geometry("900x600")
        
        # Windows Taskbar Icon Fix (Force OS to recognize custom icon)
        myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

        # Set App Icon
        self.base_path = os.path.dirname(__file__)
        icon_path = os.path.join(self.base_path, "logo.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            
        self.engine = CleanerEngine("config.json")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Navigation Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Sidebar Logo Image
        logo_img_path = os.path.join(self.base_path, "logo.png")
        if os.path.exists(logo_img_path):
            self.logo_image = ctk.CTkImage(light_image=Image.open(logo_img_path),
                                            dark_image=Image.open(logo_img_path),
                                            size=(80, 80))
            self.logo_img_label = ctk.CTkLabel(self.sidebar, image=self.logo_image, text="")
            self.logo_img_label.pack(pady=(30, 0))

        self.logo_text = ctk.CTkLabel(self.sidebar, text="CLEANER", font=ctk.CTkFont(size=24, weight="bold", family="Segoe UI"))
        self.logo_text.pack(pady=(10, 30))

        self.btn_dash = ctk.CTkButton(self.sidebar, text="Dashboard", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=self.show_dash)
        self.btn_dash.pack(fill="x", padx=20, pady=5)

        self.btn_settings = ctk.CTkButton(self.sidebar, text="Settings", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"), anchor="w", command=self.show_settings)
        self.btn_settings.pack(fill="x", padx=20, pady=5)

        self.safety_badge = ctk.CTkLabel(self.sidebar, text="🛡 Local-Only Mode", text_color="#2ecc71", font=ctk.CTkFont(size=11))
        self.safety_badge.pack(side="bottom", pady=20)

        # Content Area
        self.content_dash = ctk.CTkFrame(self, fg_color="transparent")
        self.content_dash.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.setup_dashboard()
        self.setup_settings()
        self.show_dash()

    def setup_dashboard(self):
        # Stats Row
        self.stats_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=20)
        
        self.card_files = self.create_card(self.stats_row, "Items to Clean", "0")
        self.card_files.pack(side="left", expand=True, fill="both", padx=10)
        
        self.card_size = self.create_card(self.stats_row, "Potential Savings", "0 KB")
        self.card_size.pack(side="left", expand=True, fill="both", padx=10)

        # Action Area
        self.action_frame = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        self.action_frame.pack(fill="both", expand=True)

        self.btn_analyze = ctk.CTkButton(self.action_frame, text="Analyze System", height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.start_analyze)
        self.btn_analyze.pack(pady=10, fill="x")

        self.btn_clean = ctk.CTkButton(self.action_frame, text="Execute Cleanup", height=50, fg_color="#e74c3c", hover_color="#c0392b", font=ctk.CTkFont(size=16, weight="bold"), state="disabled", command=self.start_clean)
        self.btn_clean.pack(pady=10, fill="x")

        # Progress & Logs
        self.prog_bar = ctk.CTkProgressBar(self.action_frame)
        self.prog_bar.pack(fill="x", pady=20)
        self.prog_bar.set(0)

        self.log_box = ctk.CTkTextbox(self.action_frame, height=150, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True, pady=10)
        self.log_box.insert("0.0", "System ready. Analysis recommended before cleanup.\n")
        self.log_box.configure(state="disabled")

    def create_card(self, parent, title, val):
        f = ctk.CTkFrame(parent, corner_radius=15)
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=13)).pack(pady=(15, 0))
        lbl_val = ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=32, weight="bold"))
        lbl_val.pack(pady=(0, 15))
        f.val_label = lbl_val
        return f

    def setup_settings(self):
        self.content_settings = ctk.CTkFrame(self, fg_color="transparent")
        
        ctk.CTkLabel(self.content_settings, text="Application Settings", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20, anchor="w", padx=40)
        
        # Safety Section
        s_frame = ctk.CTkFrame(self.content_settings, corner_radius=15)
        s_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(s_frame, text="Safety Measures", font=ctk.CTkFont(weight="bold")).pack(pady=10, padx=20, anchor="w")
        
        self.sw_grace = ctk.CTkSwitch(s_frame, text="Enable 24-hour Safety Grace Period", command=self.toggle_grace)
        self.sw_grace.pack(pady=10, padx=30, anchor="w")
        if self.engine.config["grace_period_hours"] > 0: self.sw_grace.select()

        self.sw_bin = ctk.CTkSwitch(s_frame, text="Empty Recycle Bin on Completion", command=self.toggle_bin)
        self.sw_bin.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("empty_recycle_bin"): self.sw_bin.select()

        self.sw_dev = ctk.CTkSwitch(s_frame, text="Enable Dev-Bloat Hunter (node_modules/venv)", command=self.toggle_dev)
        self.sw_dev.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("dev_bloat_hunter"): self.sw_dev.select()

    def show_dash(self):
        self.content_settings.grid_forget()
        self.content_dash.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.btn_dash.configure(fg_color=("gray80", "gray25"))
        self.btn_settings.configure(fg_color="transparent")

    def show_settings(self):
        self.content_dash.grid_forget()
        self.content_settings.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.btn_settings.configure(fg_color=("gray80", "gray25"))
        self.btn_dash.configure(fg_color="transparent")

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def toggle_grace(self):
        self.engine.config["grace_period_hours"] = 24 if self.sw_grace.get() else 0
        self.engine.save_config()
        self.log(f"Safety grace period set to {self.engine.config['grace_period_hours']}h")

    def toggle_bin(self):
        self.engine.config["empty_recycle_bin"] = bool(self.sw_bin.get())
        self.engine.save_config()

    def toggle_dev(self):
        self.engine.config["dev_bloat_hunter"] = bool(self.sw_dev.get())
        self.engine.save_config()
        self.log(f"Dev-Bloat Hunter {'enabled' if self.sw_dev.get() else 'disabled'}")

    # Threading Wrappers
    def start_analyze(self):
        self.btn_analyze.configure(state="disabled")
        self.prog_bar.configure(mode="indeterminate")
        self.prog_bar.start()
        threading.Thread(target=self.work_analyze, daemon=True).start()

    def work_analyze(self):
        count, size = self.engine.scan(self.log)
        self.after(0, lambda: self.finish_analyze(count, size))

    def finish_analyze(self, count, size):
        self.prog_bar.stop()
        self.prog_bar.configure(mode="determinate")
        self.prog_bar.set(1)
        self.card_files.val_label.configure(text=str(count))
        self.card_size.val_label.configure(text=self.engine.format_bytes(size))
        self.btn_analyze.configure(state="normal")
        if count > 0: self.btn_clean.configure(state="normal")
        self.log("Analysis complete. Ready for cleanup.")

    def start_clean(self):
        if tk.messagebox.askyesno("Confirm Cleanup", "Are you sure you want to delete these files? This cannot be undone."):
            self.btn_clean.configure(state="disabled")
            self.btn_analyze.configure(state="disabled")
            threading.Thread(target=self.work_clean, daemon=True).start()

    def work_clean(self):
        count, size = self.engine.clean(self.log)
        self.after(0, lambda: self.finish_clean(count, size))

    def finish_clean(self, count, size):
        self.prog_bar.set(1)
        self.log(f"SUCCESS: Cleaned {count} items ({self.engine.format_bytes(size)})")
        tk.messagebox.showinfo("Cleanup Complete", f"Successfully reclaimed {self.engine.format_bytes(size)} of space!")
        self.card_files.val_label.configure(text="0")
        self.card_size.val_label.configure(text="0 KB")
        self.btn_analyze.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()