import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import threading
from ui.widgets import BaseToplevel, Frame, Label, Button

class VersionsDialog(BaseToplevel):
    def __init__(self, parent, card, search_service, image_loader, on_add_card, action_label="Add Selected to Deck"):
        super().__init__(parent)
        self.title(f"Versions of {card.get('name')}")
        self.geometry("800x600")
        
        self.card = card
        self.search_service = search_service
        self.image_loader = image_loader
        self.on_add_card = on_add_card
        self.action_label = action_label
        
        self.prints = []
        self.current_print = None
        
        self.create_widgets()
        self.load_prints()
        
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

    def create_widgets(self):
        # Left: List of prints
        left_frame = Frame(self)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        columns = ("set", "number", "rarity", "artist")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings")
        self.tree.heading("set", text="Set")
        self.tree.heading("number", text="#")
        self.tree.heading("rarity", text="Rarity")
        self.tree.heading("artist", text="Artist")
        
        self.tree.column("set", width=150)
        self.tree.column("number", width=50)
        self.tree.column("rarity", width=80)
        self.tree.column("artist", width=150)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Right: Preview and Actions
        right_frame = Frame(self, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        self.image_label = Label(right_frame, text="Loading...")
        self.image_label.pack(pady=10)
        
        self.add_btn = Button(right_frame, text=self.action_label, command=self.add_selected, state=tk.DISABLED)
        self.add_btn.pack(pady=10)
        
        Button(right_frame, text="Close", command=self.destroy).pack(pady=5)

    def load_prints(self):
        uri = self.card.get('prints_search_uri')
        if not uri:
            # Fallback: search by oracle_id if available, or name
            if 'oracle_id' in self.card:
                uri = f"https://api.scryfall.com/cards/search?order=released&q=oracle_id%3A{self.card['oracle_id']}&unique=prints"
            else:
                # Fallback to name
                uri = f"https://api.scryfall.com/cards/search?order=released&q=%21%22{self.card['name']}%22&unique=prints"
        
        self.search_service.get_prints(uri, self.on_prints_loaded)

    def on_prints_loaded(self, prints):
        self.prints = prints
        self.after(0, self.populate_tree)

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for p in self.prints:
            self.tree.insert("", tk.END, iid=p['id'], values=(
                p.get('set_name', p.get('set', '').upper()),
                p.get('collector_number', ''),
                p.get('rarity', '').title(),
                p.get('artist', '')
            ))

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        card_id = selection[0]
        self.current_print = next((p for p in self.prints if p['id'] == card_id), None)
        
        if self.current_print:
            self.add_btn.configure(state=tk.NORMAL)
            self.show_image(self.current_print)

    def show_image(self, card):
        image_url = None
        if 'image_uris' in card:
            image_url = card['image_uris'].get('normal')
        elif 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
            image_url = card['card_faces'][0]['image_uris'].get('normal')
            
        if image_url:
            self.image_label.configure(text="Loading image...")
            self.image_loader.get_image(image_url, lambda photo: self.after(0, lambda: self._update_image(photo)))
        else:
            self.image_label.configure(image=None, text="No Image")

    def _update_image(self, photo):
        self.image_label.configure(image=photo, text="")
        self._current_image = photo # Keep reference to prevent GC

    def add_selected(self):
        if self.current_print:
            self.on_add_card(self.current_print)


