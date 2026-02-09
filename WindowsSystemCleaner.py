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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows System Cleaner")
        self.geometry("1000x750")
        
        myappid = 'com.chiru.windowssystemcleaner.v1'
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

        self.base_path = Path(__file__).parent
        self.assets_path = self.base_path / "assets"
        
        icon_path = self.assets_path / "logo.ico"
        if icon_path.exists(): self.iconbitmap(str(icon_path))

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

    def close_splash(self):
        if pyi_splash:
            try: pyi_splash.close()
            except: pass

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        logo_img_path = self.assets_path / "logo.png"
        if logo_img_path.exists():
            self.logo_image = ctk.CTkImage(light_image=Image.open(logo_img_path),
                                            dark_image=Image.open(logo_img_path),
                                            size=(80, 80))
            ctk.CTkLabel(self.sidebar, image=self.logo_image, text="").pack(pady=(30, 0))

        ctk.CTkLabel(self.sidebar, text="SYSTEM\nCLEANER", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(10, 30))
        self.btn_dash = ctk.CTkButton(self.sidebar, text="Dashboard", fg_color="transparent", anchor="w", command=self.show_dash)
        self.btn_dash.pack(fill="x", padx=20, pady=5)
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Settings", fg_color="transparent", anchor="w", command=self.show_settings)
        self.btn_settings.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(self.sidebar, text="🛡 Local-Only Mode", text_color="#2ecc71", font=ctk.CTkFont(size=11)).pack(side="bottom", pady=20)

    def setup_content_areas(self):
        self.content_dash = ctk.CTkFrame(self, fg_color="transparent")
        self.content_settings = ctk.CTkFrame(self, fg_color="transparent")
        self.setup_dashboard()
        self.setup_settings_view()

    def setup_dashboard(self):
        stats_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        stats_row.pack(fill="x", pady=20)
        self.card_files = self.create_card(stats_row, "Items Found", "0")
        self.card_files.pack(side="left", expand=True, fill="both", padx=10)
        self.card_size = self.create_card(stats_row, "Total to Free", "0 KB")
        self.card_size.pack(side="left", expand=True, fill="both", padx=10)

        btn_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        btn_row.pack(fill="x", padx=10)
        self.btn_analyze = ctk.CTkButton(btn_row, text="Analyze System", height=40, command=self.start_analyze)
        self.btn_analyze.pack(side="left", expand=True, fill="x", padx=5)
        self.btn_clean = ctk.CTkButton(btn_row, text="Clean Selected", height=40, fg_color="#e74c3c", state="disabled", command=self.start_clean)
        self.btn_clean.pack(side="left", expand=True, fill="x", padx=5)

        # Bulk Selection Row
        bulk_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        bulk_row.pack(fill="x", padx=15, pady=(20, 0))
        ctk.CTkLabel(bulk_row, text="Scan Results", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        
        self.btn_sel_none = ctk.CTkButton(bulk_row, text="Deselect All", width=80, height=20, font=ctk.CTkFont(size=10), command=lambda: self.set_all_checks(False))
        self.btn_sel_none.pack(side="right", padx=5)
        self.btn_sel_all = ctk.CTkButton(bulk_row, text="Select All", width=80, height=20, font=ctk.CTkFont(size=10), command=lambda: self.set_all_checks(True))
        self.btn_sel_all.pack(side="right", padx=5)

        self.review_frame = ctk.CTkScrollableFrame(self.content_dash, height=300)
        self.review_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.prog_bar = ctk.CTkProgressBar(self.content_dash)
        self.prog_bar.pack(fill="x", pady=10, padx=10)
        self.status_lbl = ctk.CTkLabel(self.content_dash, text="Ready", font=ctk.CTkFont(size=11))
        self.status_lbl.pack(padx=10, anchor="w")

    def create_card(self, parent, title, val):
        f = ctk.CTkFrame(parent, corner_radius=15)
        ctk.CTkLabel(f, text=title).pack(pady=(15, 0))
        lbl_val = ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=32, weight="bold"))
        lbl_val.pack(pady=(0, 15))
        f.val_label = lbl_val
        return f

    def setup_settings_view(self):
        ctk.CTkLabel(self.content_settings, text="Application Settings", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=20, anchor="w", padx=40)
        s_frame = ctk.CTkFrame(self.content_settings, corner_radius=15)
        s_frame.pack(fill="x", padx=40, pady=10)
        
        self.sw_grace = ctk.CTkSwitch(s_frame, text="Enable 24-hour Safety Grace Period", command=self.save_settings)
        self.sw_grace.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("grace_period_hours", 0) > 0: self.sw_grace.select()

        self.sw_bin = ctk.CTkSwitch(s_frame, text="Empty Recycle Bin on Completion", command=self.save_settings)
        self.sw_bin.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("empty_recycle_bin"): self.sw_bin.select()

        self.sw_dev = ctk.CTkSwitch(s_frame, text="Enable Dev-Bloat Hunter", command=self.save_settings)
        self.sw_dev.pack(pady=10, padx=30, anchor="w")
        if self.engine.config.get("dev_bloat_hunter"): self.sw_dev.select()

        ctk.CTkLabel(self.content_settings, text="System Integration", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), anchor="w", padx=45)
        i_frame = ctk.CTkFrame(self.content_settings, corner_radius=15)
        i_frame.pack(fill="x", padx=40, pady=10)
        
        self.btn_install = ctk.CTkButton(i_frame, text="Add to Start Menu / Register App", command=self.create_start_menu_shortcut)
        self.btn_install.pack(pady=15, padx=30, fill="x")

        ctk.CTkLabel(self.content_settings, text="Search Locations (Dev-Bloat)", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), anchor="w", padx=45)
        p_frame = ctk.CTkFrame(self.content_settings, corner_radius=15)
        p_frame.pack(fill="both", expand=True, padx=40, pady=10)
        self.path_listbox = ctk.CTkScrollableFrame(p_frame, height=150)
        self.path_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_path_list()
        ctk.CTkButton(p_frame, text="+ Add Folder", command=self.add_search_path).pack(pady=10)

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
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.2.1")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Chiranthan Reddy")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, working_dir)
                
                uninstall_cmd = f'powershell.exe -Command "Remove-Item -Path \\"{shortcut_path}\\" -Force; Remove-Item -Path \\"{working_dir}\\" -Recurse -Force; Remove-Item -Path \\"HKCU:\\{reg_path}\\" -Force"'
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, uninstall_cmd)
            
            messagebox.showinfo("Success", "Application successfully added to Start Menu and registered!")
        except Exception as e:
            logging.error(f"Failed to create shortcut: {e}")
            messagebox.showerror("Error", f"Failed to create shortcut: {e}")

    def show_dash(self):
        self.content_settings.grid_forget(); self.content_dash.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.btn_dash.configure(fg_color=("gray80", "gray25")); self.btn_settings.configure(fg_color="transparent")

    def show_settings(self):
        self.content_dash.grid_forget(); self.content_settings.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.btn_settings.configure(fg_color=("gray80", "gray25")); self.btn_dash.configure(fg_color="transparent")

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
        self.prog_bar.configure(mode="indeterminate"); self.prog_bar.start()
        for w in self.review_frame.winfo_children(): w.destroy()
        self.checkbox_vars = []
        threading.Thread(target=self.work_analyze, daemon=True).start()

    def work_analyze(self):
        try:
            results = self.engine.scan(lambda m: self.after(0, lambda: self.status_lbl.configure(text=m)))
            self.after(0, lambda: self.finish_analyze(results))
        finally: self.after(0, self.stop_progress)

    def finish_analyze(self, results):
        self.scan_results = results
        self.card_files.val_label.configure(text=str(len(results)))
        
        for item in results:
            var = tk.StringVar(value="on")
            cb = ctk.CTkCheckBox(self.review_frame, text=f"[{item['category']}] {item['path'].name} ({self.engine.format_bytes(item['size'])})", 
                                 variable=var, onvalue="on", offvalue="off", command=self.update_live_stats)
            cb.pack(fill="x", pady=2, padx=10)
            self.checkbox_vars.append((item, var))
            
        self.update_live_stats()
        self.status_lbl.configure(text="Scan complete. Items older than 24h found." if results else "System is clean!")

    def start_clean(self):
        items_to_del = [item for item, var in self.checkbox_vars if var.get() == "on"]
        if not items_to_del: return
        if messagebox.askyesno("Confirm", f"Move {len(items_to_del)} items to Recycle Bin?"):
            self.btn_clean.configure(state="disabled"); self.btn_analyze.configure(state="disabled")
            threading.Thread(target=self.work_clean, args=(items_to_del,), daemon=True).start()

    def work_clean(self, items):
        try:
            count, size = self.engine.clean(items, lambda m: self.after(0, lambda: self.status_lbl.configure(text=m)))
            self.after(0, lambda: self.finish_clean(count, size))
        finally: self.after(0, self.stop_progress)

    def finish_clean(self, count, size):
        messagebox.showinfo("Success", f"Moved {count} items to Recycle Bin ({self.engine.format_bytes(size)})")
        self.card_files.val_label.configure(text="0")
        for w in self.review_frame.winfo_children(): w.destroy()
        self.checkbox_vars = []
        self.update_live_stats()

    def stop_progress(self):
        self.prog_bar.stop(); self.prog_bar.configure(mode="determinate"); self.prog_bar.set(1)
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