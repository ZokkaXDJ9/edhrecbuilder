import json
import os
import customtkinter as ctk

class SettingsService:
    def __init__(self, config_file="settings.json"):
        self.config_file = config_file
        self.settings = {
            "appearance_mode": "System",
            "color_theme": "blue",
            "ui_style": "classic"
        }
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()
        
    def apply_settings(self):
        # Only apply ctk settings if in modern mode or if we want to support theming in classic too (for ctk widgets that might still exist?)
        # But ui/widgets.py handles the import.
        # However, ctk functions are global.
        try:
            ctk.set_appearance_mode(self.settings["appearance_mode"])
            ctk.set_default_color_theme(self.settings["color_theme"])
        except:
            pass
