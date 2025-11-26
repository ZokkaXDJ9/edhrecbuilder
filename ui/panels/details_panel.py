import tkinter as tk
from tkinter import ttk
from ui.dialogs.versions_dialog import VersionsDialog

class DetailsPanel(ttk.Frame):
    def __init__(self, parent, image_loader, search_service=None, on_add_card=None):
        super().__init__(parent, padding="10")
        self.image_loader = image_loader
        self.search_service = search_service
        self.on_add_card = on_add_card
        self.current_card = None
        self.current_face_index = 0
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Card Preview").pack(anchor=tk.W)
        
        self.image_label = ttk.Label(self, text="No Image Selected")
        self.image_label.pack(pady=10)
        
        # Buttons Frame
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(fill=tk.X, pady=5)
        
        self.flip_btn = ttk.Button(self.btn_frame, text="Flip Card", command=self.flip_card)
        self.flip_btn.pack(side=tk.LEFT, padx=5)
        self.flip_btn.pack_forget() # Hide initially
        
        self.versions_btn = ttk.Button(self.btn_frame, text="View Alt Arts / Versions", command=self.open_versions)
        self.versions_btn.pack(side=tk.RIGHT, padx=5)
        self.versions_btn.config(state=tk.DISABLED)

        self.card_text = tk.Text(self, height=10, wrap=tk.WORD)
        self.card_text.pack(fill=tk.BOTH, expand=True)

    def display_card(self, card):
        self.current_card = card
        self.current_face_index = 0
        
        # Enable versions button
        self.versions_btn.config(state=tk.NORMAL)
        
        # Check for faces for Flip button
        has_faces = 'card_faces' in card and len(card['card_faces']) > 1
        # Ensure faces have images to flip between
        if has_faces:
            # Some DFCs (meld) might not have images on both faces in the same way, but usually yes.
            # Check if faces have image_uris
            if 'image_uris' in card['card_faces'][0]:
                self.flip_btn.pack(side=tk.LEFT, padx=5)
            else:
                self.flip_btn.pack_forget()
        else:
            self.flip_btn.pack_forget()

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

        self.update_image()

    def flip_card(self):
        if self.current_card and 'card_faces' in self.current_card:
            self.current_face_index = (self.current_face_index + 1) % len(self.current_card['card_faces'])
            self.update_image()

    def update_image(self):
        card = self.current_card
        if not card:
            return

        image_url = None
        
        # Logic for DFCs
        if 'card_faces' in card and 'image_uris' in card['card_faces'][0]:
            # Use current face index
            face = card['card_faces'][self.current_face_index]
            if 'image_uris' in face:
                image_url = face['image_uris'].get('normal')
        # Logic for Single Faced
        elif 'image_uris' in card:
            image_url = card['image_uris'].get('normal')

        if image_url:
            self.image_loader.get_image(image_url, lambda photo: self.after(0, lambda: self._update_image_label(photo)))
        else:
            self.image_label.config(image='', text="No Image Available")

    def _update_image_label(self, photo):
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo  # Keep reference

    def open_versions(self):
        if not self.current_card or not self.search_service:
            return
            
        VersionsDialog(self, self.current_card, self.search_service, self.image_loader, self.on_add_card)

