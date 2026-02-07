import tkinter as tk
import customtkinter as ctk
import os
import ctypes
import threading
from datetime import datetime
from PIL import Image

# Import Modular Engine
from cleaner_engine import CleanerEngine

try:
    import pyi_splash
except ImportError:
    pyi_splash = None

# --- UI ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Windows System Cleaner")
        self.geometry("900x600")
        
        # Windows Taskbar Icon Fix
        myappid = 'com.chiru.windowssystemcleaner.v1'
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

        self.logo_text = ctk.CTkLabel(self.sidebar, text="SYSTEM\nCLEANER", font=ctk.CTkFont(size=20, weight="bold", family="Segoe UI"))
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

        # Close splash screen if running as EXE
        if pyi_splash:
            pyi_splash.close()

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
