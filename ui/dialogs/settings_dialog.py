import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from ui.widgets import BaseToplevel, Tabview, Label, ComboBox, Button, set_appearance_mode, set_default_color_theme

class SettingsDialog(BaseToplevel):
    def __init__(self, parent, open_search_settings_callback, settings_service, restart_callback):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("500x400")
        self.open_search_settings_callback = open_search_settings_callback
        self.settings_service = settings_service
        self.restart_callback = restart_callback
        
        self.create_widgets()
        
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()
        
        # Keep on top to prevent being hidden behind main window during theme changes
        self.attributes("-topmost", True)

    def create_widgets(self):
        tabview = Tabview(self)
        tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tabview.add("Appearance")
        tabview.add("General")
        
        # Appearance Tab
        appearance_frame = tabview.tab("Appearance")
        
        Label(appearance_frame, text="UI Style (Requires Restart):").pack(anchor=tk.W, pady=(0, 5))
        style_var = tk.StringVar(value=self.settings_service.get("ui_style", "modern"))
        style_combo = ComboBox(appearance_frame, values=["modern", "classic"], 
                                     command=self.change_ui_style)
        style_combo.set(style_var.get())
        style_combo.pack(fill=tk.X, pady=5)

        Label(appearance_frame, text="Appearance Mode:").pack(anchor=tk.W, pady=(10, 5))
        
        mode_var = tk.StringVar(value=self.settings_service.get("appearance_mode"))
        mode_combo = ComboBox(appearance_frame, values=["System", "Light", "Dark"], 
                                     command=self.change_appearance_mode)
        mode_combo.set(mode_var.get())
        mode_combo.pack(fill=tk.X, pady=5)
        
        Label(appearance_frame, text="Color Theme:").pack(anchor=tk.W, pady=(10, 5))
        
        theme_var = tk.StringVar(value=self.settings_service.get("color_theme"))
        theme_combo = ComboBox(appearance_frame, values=["blue", "green", "dark-blue"],
                                      command=self.change_color_theme)
        theme_combo.set(theme_var.get()) 
        theme_combo.pack(fill=tk.X, pady=5)
        
        Label(appearance_frame, text="(Color theme changes require UI reload)", font=("Arial", 10)).pack(anchor=tk.W)
        
        # General Tab
        general_frame = tabview.tab("General")
        
        Button(general_frame, text="Configure Search Filters", command=self.open_search_settings_callback).pack(fill=tk.X, pady=5)
        
        Button(self, text="Close", command=self.destroy).pack(pady=10)

    def change_ui_style(self, new_style: str):
        self.settings_service.set("ui_style", new_style)
        from tkinter import messagebox
        messagebox.showinfo("Restart Required", "Changing UI Style requires a full application restart.")

    def change_appearance_mode(self, new_appearance_mode: str):
        set_appearance_mode(new_appearance_mode)
        self.settings_service.set("appearance_mode", new_appearance_mode)
        # Ensure window stays visible and focused after theme change
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

    def change_color_theme(self, new_color_theme: str):
        # Save setting
        self.settings_service.set("color_theme", new_color_theme)
        # Apply for future widgets
        set_default_color_theme(new_color_theme)
        # Reload UI immediately
        self.restart_callback()
