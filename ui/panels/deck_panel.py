import tkinter as tk
from tkinter import ttk

class DeckPanel(ttk.Frame):
    def __init__(self, parent, on_card_select, on_commander_click, on_remove_card, on_preview_deck, on_change_version=None):
        super().__init__(parent, padding="10")
        self.on_card_select = on_card_select
        self.on_commander_click = on_commander_click
        self.on_remove_card = on_remove_card
        self.on_preview_deck = on_preview_deck
        self.on_change_version = on_change_version
        
        self.deck_list_data = [] # List of card objects
        
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Current Deck").pack(anchor=tk.W)
        
        # Commander Display Area
        cmd_frame = ttk.Frame(self)
        cmd_frame.pack(fill=tk.X, pady=5)
        
        self.commander_image_label = ttk.Label(cmd_frame, text="No Commander")
        self.commander_image_label.pack(side=tk.LEFT)
        
        self.commander_label = ttk.Label(cmd_frame, text="Commander: None", font=("Arial", 10, "bold"))
        self.commander_label.pack(side=tk.LEFT, padx=10)
        self.commander_label.bind("<Button-1>", lambda e: self.on_commander_click())

        self.deck_list = tk.Listbox(self, selectmode=tk.EXTENDED)
        self.deck_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.deck_list.bind('<<ListboxSelect>>', self._on_list_select)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)

        remove_btn = ttk.Button(btn_frame, text="Remove Card", command=self.on_remove_card)
        remove_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.change_ver_btn = ttk.Button(btn_frame, text="Change Version", command=self.change_version, state=tk.DISABLED)
        self.change_ver_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        preview_btn = ttk.Button(self, text="Preview Deck", command=self.on_preview_deck)
        preview_btn.pack(fill=tk.X, pady=5)
        
        self.count_label = ttk.Label(self, text="Count: 0/99")
        self.count_label.pack(anchor=tk.W)

    def change_version(self):
        selection = self.deck_list.curselection()
        if selection and self.on_change_version:
            index = selection[0]
            self.on_change_version(index)

    def update_commander(self, card, image_loader):
        if card:
            self.commander_label.config(text=f"Commander: {card.get('name')}")
            # Load image
            image_url = None
            if 'image_uris' in card:
                image_url = card['image_uris'].get('small') 
            elif 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
                image_url = card['card_faces'][0]['image_uris'].get('small')
            
            if image_url:
                image_loader.get_image(image_url, lambda photo: self.after(0, lambda: self.commander_image_label.config(image=photo, text="")), height=None)
            else:
                self.commander_image_label.config(text="No Image", image="")
        else:
            self.commander_label.config(text="Commander: None")
            self.commander_image_label.config(text="No Commander", image="")

    def add_card(self, card):
        self.deck_list_data.append(card)
        self.deck_list.insert(tk.END, self._get_display_string(card))
        self.update_counts()

    def remove_selected(self):
        selection = self.deck_list.curselection()
        if not selection:
            return
            
        # Remove in reverse order
        for index in reversed(selection):
            self.deck_list_data.pop(index)
            self.deck_list.delete(index)
        self.update_counts()

    def update_counts(self):
        count = len(self.deck_list_data)
        self.count_label.config(text=f"Count: {count}/99")

    def _on_list_select(self, event):
        selection = self.deck_list.curselection()
        if selection:
            index = selection[0]
            card = self.deck_list_data[index]
            self.on_card_select(card)
            if hasattr(self, 'change_ver_btn'):
                self.change_ver_btn.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'change_ver_btn'):
                self.change_ver_btn.config(state=tk.DISABLED)

    def get_selected_indices(self):
        return self.deck_list.curselection()

    def clear_deck(self):
        self.deck_list_data = []
        self.deck_list.delete(0, tk.END)
        self.update_counts()

    def refresh_deck(self, cards):
        self.deck_list_data = list(cards) # Copy
        self.deck_list.delete(0, tk.END)
        for card in self.deck_list_data:
            self.deck_list.insert(tk.END, self._get_display_string(card))
        self.update_counts()

    def _get_display_string(self, card):
        name = card.get('name', 'Unknown')
        
        # If it's the default version (user didn't explicitly choose a printing), hide version info
        if card.get('is_default_version', False):
            return name
            
        set_code = card.get('set', '').upper()
        cn = card.get('collector_number', '')
        if set_code and cn:
            return f"{name} ({set_code} #{cn})"
        return name
