import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO
import threading
import os
import hashlib

class DeckPreviewWindow(tk.Toplevel):
    def __init__(self, parent, deck, commander, image_loader):
        super().__init__(parent)
        self.title("Deck Preview")
        self.geometry("1000x800")
        self.deck = deck
        self.commander = commander
        self.image_loader = image_loader
        
        # Control Frame
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Preview Style:").pack(side=tk.LEFT)
        self.style_var = tk.StringVar(value="Visual Grid")
        style_combo = ttk.Combobox(control_frame, textvariable=self.style_var, 
                                 values=["Visual Grid", "Text List", "Mana Curve"], state="readonly")
        style_combo.pack(side=tk.LEFT, padx=5)
        style_combo.bind("<<ComboboxSelected>>", self.refresh_view)

        # Content Frame
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_view()

    def refresh_view(self, event=None):
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        style = self.style_var.get()
        if style == "Visual Grid":
            self.render_visual_grid()
        elif style == "Text List":
            self.render_text_list()
        elif style == "Mana Curve":
            self.render_mana_curve()

    def render_visual_grid(self):
        # Scrollable canvas setup
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate
        cards_to_show = []
        if self.commander:
            cards_to_show.append(self.commander)
        cards_to_show.extend(self.deck)

        row = 0
        col = 0
        columns = 5
        
        for card in cards_to_show:
            # Card Frame
            card_frame = ttk.Frame(scrollable_frame, padding=5)
            card_frame.grid(row=row, column=col, padx=5, pady=5)
            
            # Label for Image
            lbl = ttk.Label(card_frame, text="Loading...")
            lbl.pack()
            
            # Name
            ttk.Label(card_frame, text=card.get('name')[:20], font=("Arial", 8)).pack()

            # Load Image
            self.load_card_image(card, lbl)

            col += 1
            if col >= columns:
                col = 0
                row += 1

    def load_card_image(self, card, label_widget):
        # Logic to get image url
        image_url = None
        if 'image_uris' in card:
            image_url = card['image_uris'].get('small') # Use small for grid
        elif 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
            image_url = card['card_faces'][0]['image_uris'].get('small')
        
        if not image_url:
            label_widget.config(text="No Image")
            return

        # Use ImageLoader
        # No explicit height resize for grid (small is fine)
        self.image_loader.get_image(image_url, lambda photo: self.after(0, lambda: self._update_label(label_widget, photo)), height=None)

    def _update_label(self, label, photo):
        label.config(image=photo, text="")

    def render_text_list(self):
        text_area = tk.Text(self.content_frame)
        text_area.pack(fill=tk.BOTH, expand=True)
        
        # Grouping logic
        groups = {}
        # Only list deck cards, exclude commander from the groups
        cards = self.deck
        
        for card in cards:
            if not card: continue
            type_line = card.get('type_line', 'Unknown')
            
            # Better grouping logic
            main_type = "Other"
            # Priority types for sorting
            priority_types = ["Creature", "Planeswalker", "Land", "Instant", "Sorcery", "Artifact", "Enchantment", "Battle"]
            
            found = False
            for t in priority_types:
                if t in type_line:
                    main_type = t
                    found = True
                    break
            
            if not found:
                 # Fallback: take the first word that isn't Legendary/Basic/Snow/World
                 parts = type_line.split('—')[0].split()
                 for p in parts:
                     if p not in ["Legendary", "Basic", "Snow", "World", "Tribal", "Kindred"]:
                         main_type = p
                         break

            if main_type not in groups:
                groups[main_type] = []
            groups[main_type].append(card.get('name'))

        if self.commander:
            text_area.insert(tk.END, f"COMMANDER:\n{self.commander.get('name')}\n\n")

        for g_name, c_list in sorted(groups.items()):
            text_area.insert(tk.END, f"{g_name} ({len(c_list)}):\n")
            for name in sorted(c_list):
                text_area.insert(tk.END, f"  {name}\n")
            text_area.insert(tk.END, "\n")

    def render_mana_curve(self):
        canvas = tk.Canvas(self.content_frame, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Calculate curve
        cmc_counts = {}
        cards = [self.commander] + self.deck if self.commander else self.deck
        
        max_cmc = 0
        max_count = 0
        
        for card in cards:
            if not card: continue
            cmc = int(card.get('cmc', 0))
            cmc_counts[cmc] = cmc_counts.get(cmc, 0) + 1
            max_cmc = max(max_cmc, cmc)
            max_count = max(max_count, cmc_counts[cmc])

        # Draw
        w = 800
        h = 400
        bar_width = 40
        start_x = 50
        start_y = 350
        
        for i in range(max_cmc + 1):
            count = cmc_counts.get(i, 0)
            if count > 0:
                bar_height = (count / max_count) * 300
                x1 = start_x + (i * (bar_width + 10))
                y1 = start_y - bar_height
                x2 = x1 + bar_width
                y2 = start_y
                
                canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
                canvas.create_text((x1+x2)/2, y2+15, text=str(i)) # CMC label
                canvas.create_text((x1+x2)/2, y1-10, text=str(count)) # Count label
        
        canvas.create_text(w/2, start_y + 40, text="Mana Value (CMC)")
