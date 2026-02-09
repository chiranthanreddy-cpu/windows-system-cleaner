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

# Import Modular Engine
from cleaner_engine import CleanerEngine

try:
    import pyi_splash
except ImportError:
    pyi_splash = None

# Configure Logging (UI is the entry point)
log_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / "WindowsSystemCleaner"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(log_dir / "engine_debug.log"),
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class CircularGauge(ctk.CTkCanvas):
    def __init__(self, parent, size=150, color="#58A6FF", **kwargs):
        super().__init__(parent, width=size, height=size, bg="#161B22", highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        self.percent = 0
        self.draw()

    def set_percent(self, p):
        self.percent = max(0, min(100, p))
        self.draw()

    def draw(self):
        self.delete("all")
        padding = 10
        # Background arc
        self.create_arc(padding, padding, self.size-padding, self.size-padding, 
                        start=225, extent=-270, outline="#0d1117", width=10, style="arc")
        # Progress arc
        if self.percent > 0:
            extent = -(self.percent / 100) * 270
            self.create_arc(padding, padding, self.size-padding, self.size-padding, 
                            start=225, extent=extent, outline=self.color, width=10, style="arc")
        # Text
        self.create_text(self.size/2, self.size/2, text=f"{int(self.percent)}%", 
                         fill="#C9D1D9", font=("Segoe UI Variable", 28, "bold"))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows System Cleaner")
        self.geometry("1100x800")
        
        # Modern Dark Theme Palette
        self.colors = {
            "bg": "#0B0E14",
            "sidebar": "#080A0F",
            "card": "#161B22",
            "accent": "#58A6FF",
            "text": "#C9D1D9",
            "text_dim": "#8B949E",
            "success": "#3FB950",
            "danger": "#F85149"
        }
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=self.colors["bg"])
        
        myappid = 'com.chiru.windowssystemcleaner.v1'
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

        self.base_path = Path(__file__).parent
        self.assets_path = self.base_path / "assets"
        
        # Resource Resilience
        try:
            icon_path = self.assets_path / "logo.ico"
            if icon_path.exists(): self.iconbitmap(str(icon_path))
        except Exception as e:
            logging.warning(f"Could not load icon: {e}")

        log_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / "WindowsSystemCleaner"
        log_dir.mkdir(exist_ok=True)
        self.engine = CleanerEngine(str(log_dir / "config.json"))
        self.scan_results = []
        self.checkbox_vars = [] # List of (dict, StringVar)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_content_areas()
        self.show_dash()

        if pyi_splash: self.after(200, self.close_splash)
        
        # User Friendly: Auto-prompt to install on first run
        self.after(1000, self.check_first_run_install)

    def check_first_run_install(self):
        shortcut_path = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Windows System Cleaner.lnk")
        if not os.path.exists(shortcut_path):
            if messagebox.askyesno("Easy Setup", "Would you like to add Windows System Cleaner to your Start Menu for easy access?"):
                self.create_start_menu_shortcut()

    def close_splash(self):
        if pyi_splash:
            try: pyi_splash.close()
            except: pass

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.colors["sidebar"], border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Resource Resilience
        logo_img_path = self.assets_path / "logo.png"
        if logo_img_path.exists():
            try:
                self.logo_image = ctk.CTkImage(light_image=Image.open(logo_img_path),
                                                dark_image=Image.open(logo_img_path),
                                                size=(60, 60))
                ctk.CTkLabel(self.sidebar, image=self.logo_image, text="").pack(pady=(40, 0))
            except Exception as e:
                logging.warning(f"Could not load logo image: {e}")
                ctk.CTkLabel(self.sidebar, text="🛡", font=ctk.CTkFont(size=40)).pack(pady=(40, 0))
        else:
            ctk.CTkLabel(self.sidebar, text="🛡", font=ctk.CTkFont(size=40)).pack(pady=(40, 0))

        ctk.CTkLabel(self.sidebar, text="SYSTEM\nCLEANER", 
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=self.colors["text"]).pack(pady=(10, 40))
        
        self.btn_dash = ctk.CTkButton(self.sidebar, text="  Dashboard", 
                                      fg_color="transparent", 
                                      text_color=self.colors["text_dim"],
                                      hover_color=self.colors["card"],
                                      anchor="w", height=45,
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      command=self.show_dash)
        self.btn_dash.pack(fill="x", padx=15, pady=5)
        
        self.btn_settings = ctk.CTkButton(self.sidebar, text="  Settings", 
                                          fg_color="transparent", 
                                          text_color=self.colors["text_dim"],
                                          hover_color=self.colors["card"],
                                          anchor="w", height=45,
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          command=self.show_settings)
        self.btn_settings.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(self.sidebar, text="🛡 Secure Local Mode", 
                     text_color=self.colors["success"], 
                     font=ctk.CTkFont(size=10)).pack(side="bottom", pady=25)

    def setup_content_areas(self):
        self.content_dash = ctk.CTkFrame(self, fg_color="transparent")
        self.content_settings = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_dashboard()
        self.setup_settings_view()

    def setup_dashboard(self):
        # Header Area
        header = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="System Dashboard", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        
        # Health Meter Hero Area
        hero_frame = ctk.CTkFrame(self.content_dash, fg_color=self.colors["card"], corner_radius=25, border_width=1, border_color="#21262d")
        hero_frame.pack(fill="x", pady=10)
        
        # Left side of hero: Circular Gauge
        gauge_container = ctk.CTkFrame(hero_frame, fg_color="transparent")
        gauge_container.pack(side="left", padx=40, pady=25)
        
        self.gauge = CircularGauge(gauge_container, size=140, color=self.colors["accent"])
        self.gauge.pack()
        
        # Right side of hero: Status Text
        info_side = ctk.CTkFrame(hero_frame, fg_color="transparent")
        info_side.pack(side="left", fill="both", expand=True, padx=10)
        
        self.health_lbl = ctk.CTkLabel(info_side, text="SYSTEM READY", 
                                        font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"], anchor="w")
        self.health_lbl.pack(fill="x", pady=(35, 5))
        
        self.health_desc = ctk.CTkLabel(info_side, text="Scan your system to detect reclaimable junk files.", 
                                        font=ctk.CTkFont(size=13), text_color=self.colors["text_dim"], anchor="w")
        self.health_desc.pack(fill="x")

        # Stats Grid
        stats_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        stats_row.pack(fill="x", pady=15)
        
        self.card_files = self.create_card(stats_row, "Items Detected", "0", "📁")
        self.card_files.pack(side="left", expand=True, fill="both", padx=(0, 10))
        
        self.card_size = self.create_card(stats_row, "Reclaimable Space", "0 KB", "💾")
        self.card_size.pack(side="left", expand=True, fill="both", padx=(10, 0))

        # Main Action Row
        btn_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        btn_row.pack(fill="x", pady=15)
        
        self.btn_analyze = ctk.CTkButton(btn_row, text="ANALYZE SYSTEM", height=55, 
                                         fg_color=self.colors["accent"], hover_color="#4091f7",
                                         font=ctk.CTkFont(size=14, weight="bold"), command=self.start_analyze)
        self.btn_analyze.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_clean = ctk.CTkButton(btn_row, text="CLEAN SELECTED", height=55, 
                                       fg_color=self.colors["danger"], hover_color="#da3633",
                                       state="disabled", font=ctk.CTkFont(size=14, weight="bold"), command=self.start_clean)
        self.btn_clean.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Results Area
        self.review_frame = ctk.CTkScrollableFrame(self.content_dash, fg_color="#0d1117", 
                                                   border_width=1, border_color="#21262d", corner_radius=15)
        self.review_frame.pack(fill="both", expand=True, pady=10)

        self.status_lbl = ctk.CTkLabel(self.content_dash, text="Shielding your privacy. 100% Local-Only.", 
                                       font=ctk.CTkFont(size=11), text_color=self.colors["text_dim"])
        self.status_lbl.pack(anchor="w")

        # Entrance Animation
        self.dash_widgets = [header, hero_frame, stats_row, btn_row, self.review_frame]
        for w in self.dash_widgets: w.pack_forget()
        self.animate_entrance(0)

    def animate_entrance(self, index):
        if index < len(self.dash_widgets):
            widget = self.dash_widgets[index]
            # Safety check: only access pack_info if the widget was previously packed
            if widget.winfo_manager() == 'pack':
                info = widget.pack_info()
                pady = info.get('pady', 0)
                padx = info.get('padx', 0)
            else:
                pady = 10 if index < 4 else 0 # Defaults for our layout
                padx = 0
                
            widget.pack(fill="both" if index > 3 else "x", 
                        expand=True if index > 3 or index == 2 else False, 
                        pady=pady, padx=padx)
            self.after(60, lambda: self.animate_entrance(index + 1))

    def create_card(self, parent, title, val, icon):
        f = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color="#21262d")
        ctk.CTkLabel(f, text=icon, font=ctk.CTkFont(size=24)).pack(pady=(20, 0))
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=12), text_color=self.colors["text_dim"]).pack()
        lbl_val = ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=28, weight="bold"), text_color=self.colors["text"])
        lbl_val.pack(pady=(0, 25))
        f.val_label = lbl_val
        return f

    def setup_settings_view(self):
        ctk.CTkLabel(self.content_settings, text="Application Settings", 
                     font=ctk.CTkFont(size=24, weight="bold"), 
                     text_color=self.colors["text"]).pack(pady=(0, 20), anchor="w", padx=40)
        
        # General Settings Section
        s_frame = ctk.CTkFrame(self.content_settings, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color="#21262d")
        s_frame.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(s_frame, text="CORE PREFERENCES", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dim"]).pack(pady=(15, 5), padx=30, anchor="w")

        self.sw_grace = ctk.CTkSwitch(s_frame, text="24-hour Safety Grace Period", 
                                       progress_color=self.colors["accent"],
                                       command=self.save_settings)
        self.sw_grace.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("grace_period_hours", 0) > 0: self.sw_grace.select()

        self.sw_bin = ctk.CTkSwitch(s_frame, text="Auto-Empty Recycle Bin", 
                                     progress_color=self.colors["accent"],
                                     command=self.save_settings)
        self.sw_bin.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("empty_recycle_bin"): self.sw_bin.select()

        self.sw_dev = ctk.CTkSwitch(s_frame, text="Enable Dev-Bloat Hunter", 
                                     progress_color=self.colors["accent"],
                                     command=self.save_settings)
        self.sw_dev.pack(pady=(10, 20), padx=30, anchor="w")
        if self.engine.config.get("dev_bloat_hunter"): self.sw_dev.select()

        # System Integration
        i_frame = ctk.CTkFrame(self.content_settings, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color="#21262d")
        i_frame.pack(fill="x", padx=40, pady=10)
        
        self.btn_install = ctk.CTkButton(i_frame, text="Add to Start Menu / Register App", 
                                         fg_color="transparent", 
                                         border_width=1,
                                         border_color=self.colors["accent"],
                                         text_color=self.colors["accent"],
                                         hover_color="#112131",
                                         command=self.create_start_menu_shortcut)
        self.btn_install.pack(pady=20, padx=30, fill="x")

        # Search Locations
        p_frame = ctk.CTkFrame(self.content_settings, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color="#21262d")
        p_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        ctk.CTkLabel(p_frame, text="DEV-BLOAT SEARCH PATHS", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dim"]).pack(pady=(15, 5), padx=30, anchor="w")
        
        self.path_listbox = ctk.CTkScrollableFrame(p_frame, fg_color="#0d1117", height=150)
        self.path_listbox.pack(fill="both", expand=True, padx=20, pady=5)
        self.refresh_path_list()
        
        ctk.CTkButton(p_frame, text="+ Add Search Folder", 
                      fg_color="transparent", 
                      text_color=self.colors["accent"],
                      font=ctk.CTkFont(weight="bold"),
                      command=self.add_search_path).pack(pady=15)

    def refresh_path_list(self):
        for w in self.path_listbox.winfo_children(): w.destroy()
        for path in self.engine.config.get("search_paths", []):
            row = ctk.CTkFrame(self.path_listbox, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=path, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkButton(row, text="X", width=30, fg_color="#e74c3c", command=lambda p=path: self.remove_search_path(p)).pack(side="right", padx=5)

    def add_search_path(self):
        path = filedialog.askdirectory()
        if path and path not in self.engine.config["search_paths"]:
            self.engine.config["search_paths"].append(path)
            self.engine.save_config(); self.refresh_path_list()

    def remove_search_path(self, path):
        if path in self.engine.config["search_paths"]:
            self.engine.config["search_paths"].remove(path)
            self.engine.save_config(); self.refresh_path_list()

    def save_settings(self):
        self.engine.config["grace_period_hours"] = 24 if self.sw_grace.get() else 0
        self.engine.config["empty_recycle_bin"] = bool(self.sw_bin.get())
        self.engine.config["dev_bloat_hunter"] = bool(self.sw_dev.get())
        self.engine.save_config()

    def create_start_menu_shortcut(self):
        try:
            import win32com.client
            import winreg
            
            exe_path = str(Path(os.sys.executable if not getattr(os.sys, 'frozen', False) else os.sys.executable).absolute())
            if not exe_path.endswith(".exe"): # Handle running from python.exe
                 exe_path = str((self.base_path.parent / "dist" / "WindowsSystemCleaner.exe").absolute())

            working_dir = str(Path(exe_path).parent)
            icon_path = str((self.assets_path / "logo.ico").absolute())
            shortcut_path = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Windows System Cleaner.lnk")

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = working_dir
            shortcut.IconLocation = icon_path
            shortcut.save()

            # Registry registration
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

    def show_dash(self):
        self.content_settings.grid_forget(); self.content_dash.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.btn_dash.configure(fg_color=self.colors["card"], text_color=self.colors["accent"])
        self.btn_settings.configure(fg_color="transparent", text_color=self.colors["text_dim"])

    def show_settings(self):
        self.content_dash.grid_forget(); self.content_settings.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.btn_settings.configure(fg_color=self.colors["card"], text_color=self.colors["accent"])
        self.btn_dash.configure(fg_color="transparent", text_color=self.colors["text_dim"])

    def set_all_checks(self, val):
        for item, var in self.checkbox_vars:
            var.set("on" if val else "off")
        self.update_live_stats()

    def update_live_stats(self):
        selected_items = [item for item, var in self.checkbox_vars if var.get() == "on"]
        total_size = sum(item['size'] for item in selected_items)
        self.card_size.val_label.configure(text=self.engine.format_bytes(total_size))
        self.btn_clean.configure(state="normal" if selected_items else "disabled")

    def start_analyze(self):
        self.btn_analyze.configure(state="disabled"); self.btn_clean.configure(state="disabled")
        self.health_lbl.configure(text="SCANNING SYSTEM...", text_color=self.colors["accent"])
        self.health_desc.configure(text="Searching for temporary files and app caches...")
        self.gauge.set_percent(0)
        # Indeterminate loop for gauge
        self.scan_active = True
        self.animate_gauge_scanning()
        for w in self.review_frame.winfo_children(): w.destroy()
        self.checkbox_vars = []
        threading.Thread(target=self.work_analyze, daemon=True).start()

    def animate_gauge_scanning(self):
        if hasattr(self, 'scan_active') and self.scan_active:
            val = (self.gauge.percent + 5) % 100
            self.gauge.set_percent(val)
            self.after(100, self.animate_gauge_scanning)

    def work_analyze(self):
        try:
            results = self.engine.scan(lambda m: self.after(0, lambda: self.status_lbl.configure(text=m)))
            self.after(0, lambda: self.finish_analyze(results))
        finally: 
            self.scan_active = False
            self.after(0, self.stop_progress)

    def finish_analyze(self, results):
        self.scan_results = results
        total_size = sum(item['size'] for item in results)
        self.card_files.val_label.configure(text=str(len(results)))
        
        # Calculate dynamic health score
        health_percent = self.engine.calculate_health_score(total_size)
        self.gauge.set_percent(health_percent)
        
        if not results or total_size < 1024 * 1024 * 10: # Under 10MB
            self.health_lbl.configure(text="SYSTEM OPTIMIZED", text_color=self.colors["success"])
            self.health_desc.configure(text="Your PC is in great shape! No significant junk found.")
            self.gauge.color = self.colors["success"]
        elif health_percent < 50:
            self.health_lbl.configure(text="SYSTEM GOOD", text_color=self.colors["accent"])
            self.health_desc.configure(text=f"A few items ({self.engine.format_bytes(total_size)}) can be cleaned.")
            self.gauge.color = self.colors["accent"]
        else:
            self.health_lbl.configure(text="CLEANUP RECOMMENDED", text_color=self.colors["danger"])
            self.health_desc.configure(text=f"Reclaim {self.engine.format_bytes(total_size)} to boost performance.")
            self.gauge.color = self.colors["danger"]
            
        self.gauge.draw()
            
        for item in results:
            var = tk.StringVar(value="on")
            row = ctk.CTkFrame(self.review_frame, fg_color="transparent")
            row.pack(fill="x", pady=4, padx=5)
            
            cb = ctk.CTkCheckBox(row, text=f"[{item['category']}] {item['path'].name}", 
                                 variable=var, onvalue="on", offvalue="off",
                                 checkbox_width=18, checkbox_height=18,
                                 border_width=2, fg_color=self.colors["accent"],
                                 hover_color="#112131", font=ctk.CTkFont(size=12),
                                 command=self.update_live_stats)
            cb.pack(side="left", padx=5)
            
            ctk.CTkLabel(row, text=self.engine.format_bytes(item['size']), 
                         font=ctk.CTkFont(size=11), text_color=self.colors["text_dim"]).pack(side="right", padx=10)
            self.checkbox_vars.append((item, var))
            
        self.update_live_stats()
        self.status_lbl.configure(text="Scan complete. Industry-standard trashing enabled.")

    def start_clean(self):
        items_to_del = [item for item, var in self.checkbox_vars if var.get() == "on"]
        if not items_to_del: return
        
        msg = f"Move {len(items_to_del)} items to Recycle Bin?"
        if self.engine.config.get("empty_recycle_bin"):
            msg += "\n\n⚠️ WARNING: 'Empty Recycle Bin' is ENABLED."
            
        if messagebox.askyesno("Confirm Cleanup", msg):
            self.btn_clean.configure(state="disabled"); self.btn_analyze.configure(state="disabled")
            self.health_lbl.configure(text="CLEANING...", text_color=self.colors["accent"])
            threading.Thread(target=self.work_clean, args=(items_to_del,), daemon=True).start()

    def work_clean(self, items):
        try:
            count, size = self.engine.clean(items, lambda m: self.after(0, lambda: self.status_lbl.configure(text=m)))
            self.after(0, lambda: self.finish_clean(count, size))
        finally: self.after(0, self.stop_progress)

    def finish_clean(self, count, size):
        self.health_lbl.configure(text="OPTIMIZED", text_color=self.colors["success"])
        self.health_desc.configure(text=f"Successfully reclaimed {self.engine.format_bytes(size)}.")
        self.gauge.set_percent(100)
        self.gauge.color = self.colors["success"]
        self.gauge.draw()
        messagebox.showinfo("Success", f"Reclaimed {self.engine.format_bytes(size)}!")
        self.card_files.val_label.configure(text="0")
        for w in self.review_frame.winfo_children(): w.destroy()
        self.checkbox_vars = []
        self.update_live_stats()

    def stop_progress(self):
        self.btn_analyze.configure(state="normal")

if __name__ == "__main__":
    try:
        # Final safety check for stuck processes
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