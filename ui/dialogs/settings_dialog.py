import tkinter as tk
from tkinter import ttk

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, open_search_settings_callback):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("500x400")
        self.open_search_settings_callback = open_search_settings_callback
        
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General Tab
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text="General")
        ttk.Label(general_frame, text="General application settings can be configured here.").pack(anchor=tk.W)

        # Appearance Tab
        appearance_frame = ttk.Frame(notebook, padding=10)
        notebook.add(appearance_frame, text="Appearance")
        
        ttk.Label(appearance_frame, text="Application Theme:").pack(anchor=tk.W, pady=(0, 5))
        
        style = ttk.Style()
        current_theme = style.theme_use()
        theme_var = tk.StringVar(value=current_theme)
        
        themes = sorted(style.theme_names())
        theme_combo = ttk.Combobox(appearance_frame, textvariable=theme_var, values=themes, state="readonly")
        theme_combo.pack(fill=tk.X, pady=5)
        
        def on_theme_change(event):
            try:
                style.theme_use(theme_var.get())
            except Exception as e:
                print(f"Error changing theme: {e}")
                
        theme_combo.bind("<<ComboboxSelected>>", on_theme_change)
        
        # General Tab
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text="Search Settings")
        
        ttk.Button(general_frame, text="Configure Search Filters", command=self.open_search_settings_callback).pack(fill=tk.X, pady=5)
        
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)
