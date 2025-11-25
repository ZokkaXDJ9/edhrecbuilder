import tkinter as tk
from tkinter import ttk

class DetailsPanel(ttk.Frame):
    def __init__(self, parent, image_loader):
        super().__init__(parent, padding="10")
        self.image_loader = image_loader
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Card Preview").pack(anchor=tk.W)
        
        self.image_label = ttk.Label(self, text="No Image Selected")
        self.image_label.pack(pady=10)
        
        self.card_text = tk.Text(self, height=10, wrap=tk.WORD)
        self.card_text.pack(fill=tk.BOTH, expand=True)

    def display_card(self, card):
        # Update text
        self.card_text.delete(1.0, tk.END)
        
        if 'card_faces' in card:
            text_display = ""
            for face in card['card_faces']:
                name = face.get('name', '')
                mana_cost = face.get('mana_cost', '')
                type_line = face.get('type_line', '')
                oracle_text = face.get('oracle_text', '')
                
                text_display += f"{name}\nCost: {mana_cost}\nType: {type_line}\n\n{oracle_text}\n\n{'-'*30}\n\n"
            self.card_text.insert(tk.END, text_display)
        else:
            name = card.get('name', 'Unknown')
            type_line = card.get('type_line', '')
            oracle_text = card.get('oracle_text', '')
            mana_cost = card.get('mana_cost', '')
            
            text_display = f"Name: {name}\nCost: {mana_cost}\nType: {type_line}\n\n{oracle_text}"
            self.card_text.insert(tk.END, text_display)

        # Update Image
        image_url = None
        if 'image_uris' in card:
            image_url = card['image_uris'].get('normal')
        elif 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
            image_url = card['card_faces'][0]['image_uris'].get('normal')

        if image_url:
            self.image_loader.get_image(image_url, lambda photo: self.after(0, lambda: self._update_image_label(photo)))
        else:
            self.image_label.config(image='', text="No Image Available")

    def _update_image_label(self, photo):
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo  # Keep reference
