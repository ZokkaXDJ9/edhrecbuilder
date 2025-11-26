import tkinter as tk
from tkinter import ttk

class MultiSelectDialog(tk.Toplevel):
    def __init__(self, parent, title, items, initial_selection=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x500")
        
        self.all_items = sorted(items)
        self.selected_items = set(initial_selection) if initial_selection else set()
        self.current_view_items = []
        self.result = None
        
        self.create_widgets()
        self.filter_list() # Populate initially
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def create_widgets(self):
        # Search
        ttk.Label(self, text="Search:").pack(fill=tk.X, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        entry = ttk.Entry(self, textvariable=self.search_var)
        entry.pack(fill=tk.X, padx=5)

        # Listbox
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT)

    def filter_list(self, *args):
        search_term = self.search_var.get().lower()
        self.current_view_items = [item for item in self.all_items if search_term in item.lower()]
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, item in enumerate(self.current_view_items):
            self.listbox.insert(tk.END, item)
            if item in self.selected_items:
                self.listbox.selection_set(i)

    def on_select(self, event):
        # Get current selection indices
        selected_indices = self.listbox.curselection()
        
        # Determine which items in the CURRENT VIEW are selected
        view_selected = set()
        for i in selected_indices:
            if i < len(self.current_view_items):
                view_selected.add(self.current_view_items[i])
        
        # Update main set:
        # 1. Add newly selected items from view
        self.selected_items.update(view_selected)
        
        # 2. Remove items that are in view but NOT selected
        for item in self.current_view_items:
            if item not in view_selected:
                if item in self.selected_items:
                    self.selected_items.remove(item)

    def clear_all(self):
        self.selected_items.clear()
        self.listbox.selection_clear(0, tk.END)

    def on_ok(self):
        self.result = list(self.selected_items)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()
