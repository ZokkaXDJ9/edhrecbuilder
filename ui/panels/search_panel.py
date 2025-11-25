import tkinter as tk
from tkinter import ttk, messagebox

class SearchPanel(ttk.Frame):
    def __init__(self, parent, search_service, on_card_select, on_card_double_click, open_settings_callback, get_commander_callback):
        super().__init__(parent, padding="10")
        self.search_service = search_service
        self.on_card_select = on_card_select
        self.on_card_double_click = on_card_double_click
        self.open_settings_callback = open_settings_callback
        self.get_commander_callback = get_commander_callback
        
        self.current_search_results = []
        self.search_prefs = {
            'include_alchemy': tk.BooleanVar(value=False),
            'include_silver': tk.BooleanVar(value=False),
            'include_playtest': tk.BooleanVar(value=False),
            'include_oversized': tk.BooleanVar(value=False),
            'include_funny': tk.BooleanVar(value=False),
            'include_ub_group': tk.BooleanVar(value=True),
            'ub_other': tk.BooleanVar(value=True)
        }
        self.filter_commander_identity = tk.BooleanVar(value=False)
        
        # Initialize UB prefs
        for _, key, _ in self.search_service.ub_sets_config:
            self.search_prefs[key] = tk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        # --- Search Bar ---
        ttk.Label(self, text="Search Cards").pack(anchor=tk.W)
        
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', lambda e: self.perform_search())
        
        search_btn = ttk.Button(search_frame, text="Search", command=self.perform_search)
        search_btn.pack(side=tk.RIGHT, padx=5)

        # --- Filters ---
        filter_frame = ttk.LabelFrame(self, text="Filters", padding=5)
        filter_frame.pack(fill=tk.X, pady=5)

        # Colors
        color_frame = ttk.Frame(filter_frame)
        color_frame.pack(fill=tk.X)
        
        self.color_vars = {}
        colors = [('W', 'White'), ('U', 'Blue'), ('B', 'Black'), ('R', 'Red'), ('G', 'Green')]
        
        for code, name in colors:
            var = tk.BooleanVar()
            self.color_vars[code] = var
            cb = ttk.Checkbutton(color_frame, text=code, variable=var)
            cb.pack(side=tk.LEFT, padx=2)

        # Type
        type_frame = ttk.Frame(filter_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="Type:").pack(side=tk.LEFT)
        
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(type_frame, textvariable=self.type_var, 
                                values=["Any", "Creature", "Artifact", "Enchantment", "Instant", "Sorcery", "Planeswalker", "Land"],
                                state="readonly", width=15)
        type_combo.current(0)
        type_combo.pack(side=tk.LEFT, padx=5)

        # Commander Identity Filter
        cmd_filter_frame = ttk.Frame(filter_frame)
        cmd_filter_frame.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(cmd_filter_frame, text="Filter by Commander Identity", 
                       variable=self.filter_commander_identity).pack(side=tk.LEFT)

        # Settings Button
        settings_btn = ttk.Button(filter_frame, text="Search Settings", command=self.open_settings_callback)
        settings_btn.pack(side=tk.RIGHT, padx=5)

        # --- Results List ---
        self.results_list = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.results_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.results_list.bind('<<ListboxSelect>>', self._on_list_select)
        self.results_list.bind('<Double-1>', lambda e: self.on_card_double_click())

    def perform_search(self):
        query = self.search_var.get()
        if not query:
            return

        # Gather filters
        filters = {}
        
        # Commander Identity
        if self.filter_commander_identity.get():
            commander = self.get_commander_callback()
            if not commander:
                messagebox.showwarning("Commander Search", "Please set a commander first to use Commander Identity filter.")
                return
            filters['commander_identity'] = commander.get('color_identity', [])

        # Colors
        selected_colors = [code for code, var in self.color_vars.items() if var.get()]
        if selected_colors:
            filters['colors'] = selected_colors
            
        # Type
        selected_type = self.type_var.get()
        if selected_type and selected_type != "Any":
            filters['type'] = selected_type

        # Preferences
        prefs = {}
        for key, var in self.search_prefs.items():
            prefs[key] = var.get()
        filters['prefs'] = prefs

        self.results_list.delete(0, tk.END)
        self.results_list.insert(tk.END, "Searching...")
        
        self.search_service.search(query, filters, self._on_search_complete)

    def _on_search_complete(self, status_code, data):
        # This should be called on main thread via after() in service or here?
        # Service calls callback from thread. We need to schedule UI update.
        self.after(0, lambda: self._update_results_ui(status_code, data))

    def _update_results_ui(self, status_code, data):
        self.current_search_results = []
        self.results_list.delete(0, tk.END)

        if status_code == 200:
            cards = data.get('data', [])
            for card in cards:
                self.current_search_results.append(card)
                self.results_list.insert(tk.END, card.get('name'))
        else:
            self.results_list.insert(tk.END, "No results found")

    def _on_list_select(self, event):
        selection = self.results_list.curselection()
        if selection:
            index = selection[0]
            if index < len(self.current_search_results):
                card = self.current_search_results[index]
                self.on_card_select(card)

    def get_selected_cards(self):
        selection = self.results_list.curselection()
        cards = []
        for index in selection:
            if index < len(self.current_search_results):
                cards.append(self.current_search_results[index])
        return cards

    def set_results(self, cards):
        self.current_search_results = cards
        self.results_list.delete(0, tk.END)
        for card in cards:
            self.results_list.insert(tk.END, card.get('name'))
