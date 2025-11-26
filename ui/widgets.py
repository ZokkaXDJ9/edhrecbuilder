import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import json
import os
from typing import Any

STYLE = "classic"
if os.path.exists("settings.json"):
    try:
        with open("settings.json", "r") as f:
            data = json.load(f)
            STYLE = data.get("ui_style", "classic")
    except:
        pass

def clean_args(kwargs):
    keys_to_remove = ['corner_radius', 'fg_color', 'hover_color', 'text_color', 
                      'border_color', 'border_width', 'fg_color', 'bg_color', 
                      'button_color', 'button_hover_color', 'dropdown_hover_color',
                      'dropdown_fg_color', 'dropdown_text_color', 'placeholder_text_color',
                      'anchor'] # anchor in ctk is sometimes different or passed differently
    
    return {k: v for k, v in kwargs.items() if k not in keys_to_remove}

def convert_kwargs(kwargs, ignore_height=True):
    if ignore_height:
        kwargs.pop("height", None)
    
    if "width" in kwargs:
        try:
            # Convert pixels to approx characters (assuming ~9px per char)
            val = int(kwargs["width"])
            kwargs["width"] = max(1, int(val / 9))
        except:
            kwargs.pop("width", None)
    return kwargs

if STYLE == "classic":
    BaseWindow = tk.Tk
    BaseToplevel = tk.Toplevel
    
    class ScrollableFrame(ttk.Frame):
        def __init__(self, container, *args, **kwargs):
            kwargs = clean_args(kwargs)
            # Extract width/height for canvas
            canvas_kwargs = {}
            if "width" in kwargs:
                canvas_kwargs["width"] = kwargs.pop("width")
            if "height" in kwargs:
                canvas_kwargs["height"] = kwargs.pop("height")
                
            super().__init__(container, *args, **kwargs)
            canvas = tk.Canvas(self, highlightthickness=0, **canvas_kwargs)
            scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
            self.scrollable_frame = ttk.Frame(canvas)
            
            self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            
            # Ensure inner frame expands to fill canvas width
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
            
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

    def get_real_master(master):
        if isinstance(master, ScrollableFrame):
            return master.scrollable_frame
        return master

    class Button(ttk.Button):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            super().__init__(master, **kwargs)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

    class Label(ttk.Label):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            super().__init__(master, **kwargs)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

    class Frame(ttk.Frame):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            super().__init__(master, **kwargs)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            return super().configure(cnf, **kwargs)
            
    class Entry(ttk.Entry):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            super().__init__(master, **kwargs)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

    class CheckBox(ttk.Checkbutton):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            super().__init__(master, **kwargs)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

    class ComboBox(ttk.Combobox):
        def __init__(self, master=None, command=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            if "variable" in kwargs:
                kwargs["textvariable"] = kwargs.pop("variable")
            super().__init__(master, **kwargs)
            self.command = command
            if command:
                self.bind("<<ComboboxSelected>>", self._on_select)
        def _on_select(self, event):
            if self.command:
                self.command(self.get())
        def set(self, value):
            super().set(value)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

    class Textbox(tk.Text):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            super().__init__(master, **kwargs)
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            kwargs = convert_kwargs(kwargs)
            return super().configure(cnf, **kwargs)

    class Tabview(ttk.Frame):
        def __init__(self, master=None, **kwargs):
            master = get_real_master(master)
            kwargs = clean_args(kwargs)
            super().__init__(master, **kwargs)
            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill="both", expand=True)
            self.tabs_dict = {}
        def add(self, name):
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)
            self.tabs_dict[name] = frame
            return frame
        def tab(self, name):
            return self.tabs_dict[name]
        def configure(self, cnf=None, **kwargs) -> Any:
            kwargs = clean_args(kwargs)
            return super().configure(cnf, **kwargs)

    def set_appearance_mode(mode): pass
    def set_default_color_theme(theme): pass

else:
    BaseWindow = ctk.CTk
    BaseToplevel = ctk.CTkToplevel
    Button = ctk.CTkButton # type: ignore
    Label = ctk.CTkLabel # type: ignore
    Frame = ctk.CTkFrame # type: ignore
    Entry = ctk.CTkEntry # type: ignore
    CheckBox = ctk.CTkCheckBox # type: ignore
    ComboBox = ctk.CTkComboBox # type: ignore
    ScrollableFrame = ctk.CTkScrollableFrame # type: ignore
    Textbox = ctk.CTkTextbox # type: ignore
    Tabview = ctk.CTkTabview # type: ignore
    set_appearance_mode = ctk.set_appearance_mode # type: ignore
    set_default_color_theme = ctk.set_default_color_theme # type: ignore
