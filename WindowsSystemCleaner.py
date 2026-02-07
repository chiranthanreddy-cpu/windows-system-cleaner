import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import os
import ctypes
import threading
from datetime import datetime
from PIL import Image
from pathlib import Path

# Import Modular Engine
from cleaner_engine import CleanerEngine

try:
    import pyi_splash
except ImportError:
    pyi_splash = None

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows System Cleaner")
        self.geometry("1000x700")
        
        # Windows Taskbar Icon Fix
        myappid = 'com.chiru.windowssystemcleaner.v1'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except: pass

        # Path Handling for Assets
        self.base_path = Path(__file__).parent
        self.assets_path = self.base_path / "assets"
        
        icon_path = self.assets_path / "logo.ico"
        if icon_path.exists():
            self.iconbitmap(str(icon_path))
            
        self.engine = CleanerEngine("config.json")
        self.scan_results = []
        self.checkboxes = [] # List of (dict, CTkCheckBox)
        
        # UI Layout setup
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_content_areas()
        
        self.show_dash()

        if pyi_splash:
            self.after(200, self.close_splash)

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
        # Stats
        stats_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        stats_row.pack(fill="x", pady=20)
        
        self.card_files = self.create_card(stats_row, "Items Found", "0")
        self.card_files.pack(side="left", expand=True, fill="both", padx=10)
        
        self.card_size = self.create_card(stats_row, "Reclaimable Space", "0 KB")
        self.card_size.pack(side="left", expand=True, fill="both", padx=10)

        # Action Buttons
        btn_row = ctk.CTkFrame(self.content_dash, fg_color="transparent")
        btn_row.pack(fill="x", padx=10)

        self.btn_analyze = ctk.CTkButton(btn_row, text="Analyze System", height=40, command=self.start_analyze)
        self.btn_analyze.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_clean = ctk.CTkButton(btn_row, text="Clean Selected", height=40, fg_color="#e74c3c", state="disabled", command=self.start_clean)
        self.btn_clean.pack(side="left", expand=True, fill="x", padx=5)

        # Review List Header
        ctk.CTkLabel(self.content_dash, text="Scan Results (Uncheck items to exclude)", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20, 5), anchor="w", padx=15)

        # Scrollable Review List
        self.review_frame = ctk.CTkScrollableFrame(self.content_dash, height=300)
        self.review_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Progress & Mini Log
        self.prog_bar = ctk.CTkProgressBar(self.content_dash)
        self.prog_bar.pack(fill="x", pady=10, padx=10)
        self.prog_bar.set(0)

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
        
        # General Switches
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

        # Path Management
        ctk.CTkLabel(self.content_settings, text="Search Locations (Dev-Bloat)", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), anchor="w", padx=45)
        p_frame = ctk.CTkFrame(self.content_settings, corner_radius=15)
        p_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self.path_listbox = ctk.CTkScrollableFrame(p_frame, height=150)
        self.path_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refresh_path_list()

        btn_add = ctk.CTkButton(p_frame, text="+ Add Folder", command=self.add_search_path)
        btn_add.pack(pady=10)

    def refresh_path_list(self):
        for widget in self.path_listbox.winfo_children():
            widget.destroy()
        
        for path in self.engine.config.get("search_paths", []):
            row = ctk.CTkFrame(self.path_listbox, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=path, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkButton(row, text="X", width=30, fg_color="#e74c3c", command=lambda p=path: self.remove_search_path(p)).pack(side="right", padx=5)

    def add_search_path(self):
        path = filedialog.askdirectory()
        if path:
            if path not in self.engine.config["search_paths"]:
                self.engine.config["search_paths"].append(path)
                self.engine.save_config()
                self.refresh_path_list()

    def remove_search_path(self, path):
        if path in self.engine.config["search_paths"]:
            self.engine.config["search_paths"].remove(path)
            self.engine.save_config()
            self.refresh_path_list()

    def save_settings(self):
        self.engine.config["grace_period_hours"] = 24 if self.sw_grace.get() else 0
        self.engine.config["empty_recycle_bin"] = bool(self.sw_bin.get())
        self.engine.config["dev_bloat_hunter"] = bool(self.sw_dev.get())
        self.engine.save_config()

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

    def start_analyze(self):
        self.btn_analyze.configure(state="disabled")
        self.btn_clean.configure(state="disabled")
        self.prog_bar.configure(mode="indeterminate")
        self.prog_bar.start()
        for widget in self.review_frame.winfo_children(): widget.destroy()
        self.checkboxes = []
        threading.Thread(target=self.work_analyze, daemon=True).start()

    def work_analyze(self):
        try:
            results = self.engine.scan(lambda m: self.after(0, lambda: self.status_lbl.configure(text=m)))
            self.after(0, lambda: self.finish_analyze(results))
        finally:
            self.after(0, self.stop_progress)

    def finish_analyze(self, results):
        self.scan_results = results
        total_size = sum(item['size'] for item in results)
        self.card_files.val_label.configure(text=str(len(results)))
        self.card_size.val_label.configure(text=self.engine.format_bytes(total_size))
        
        # Populate Review List
        for item in results:
            cb = ctk.CTkCheckBox(self.review_frame, text=f"[{item['category']}] {item['path'].name} ({self.engine.format_bytes(item['size'])})")
            cb.pack(fill="x", pady=2, padx=10)
            cb.select()
            self.checkboxes.append((item, cb))
            
        if results:
            self.btn_clean.configure(state="normal")
            self.status_lbl.configure(text="Analysis complete. Review results before cleaning.")
        else:
            self.status_lbl.configure(text="Scan complete. No items found to clean.")

    def start_clean(self):
        items_to_del = [item for item, cb in self.checkboxes if cb.get()]
        if not items_to_del: return
        
        if messagebox.askyesno("Confirm", f"Delete {len(items_to_del)} selected items permanently?"):
            self.btn_clean.configure(state="disabled")
            self.btn_analyze.configure(state="disabled")
            threading.Thread(target=self.work_clean, args=(items_to_del,), daemon=True).start()

    def work_clean(self, items):
        try:
            count, size = self.engine.clean(items, lambda m: self.after(0, lambda: self.status_lbl.configure(text=m)))
            self.after(0, lambda: self.finish_clean(count, size))
        finally:
            self.after(0, self.stop_progress)

    def finish_clean(self, count, size):
        messagebox.showinfo("Success", f"Reclaimed {self.engine.format_bytes(size)}!")
        self.card_files.val_label.configure(text="0")
        self.card_size.val_label.configure(text="0 KB")
        for widget in self.review_frame.winfo_children(): widget.destroy()

    def stop_progress(self):
        self.prog_bar.stop()
        self.prog_bar.configure(mode="determinate")
        self.prog_bar.set(1)
        self.btn_analyze.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
