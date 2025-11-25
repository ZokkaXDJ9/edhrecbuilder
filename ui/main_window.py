import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import threading
import queue
import time
import json
import os
import re

from database import CardDatabase
from ui.preview_window import DeckPreviewWindow
from services.image_service import ImageService
from services.search_service import SearchService
from services.edhrec_service import EDHRecService
from services.data_updater import DataUpdater
from services.deck_service import DeckService
from services.legality_service import LegalityService
from ui.panels.search_panel import SearchPanel
from ui.panels.deck_panel import DeckPanel
from ui.panels.details_panel import DetailsPanel
from utils import UNLIMITED_CARDS

class MTGDeckBuilder(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("MTG Commander Deckbuilder")
        self.geometry("1200x800")

        self.deck = []
        self.commander = None
        
        self.db = CardDatabase()

        # Network Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EDHRecBuilder/1.0',
            'Accept': 'application/json;q=0.9,*/*;q=0.8'
        })
        
        # Services
        self.image_loader = ImageService(self.session)
        self.edhrec_service = EDHRecService(self.session)
        self.data_updater = DataUpdater(self.db, self.session)
        self.deck_service = DeckService()
        self.legality_service = LegalityService(self.session)
        
        # Update banlist at startup
        self.legality_service.update_banlist()
        
        self.ub_sets_config = [
            ("Warhammer 40,000", "ub_40k", ["40k"]),
            ("Lord of the Rings", "ub_lotr", ["ltr", "ltc"]),
            ("Doctor Who", "ub_who", ["who"]),
            ("Fallout", "ub_fallout", ["pip"]),
            ("Assassin's Creed", "ub_acr", ["acr"]),
            ("Transformers", "ub_bot", ["bot"]),
            ("Jurassic World", "ub_rex", ["rex"]),
            ("Dungeons & Dragons", "ub_dnd", ["afr", "afc", "clb"]),
            ("Final Fantasy", "ub_ff", ["fin", "fic"]),
            ("Marvel", "ub_marvel", ["mar"]),
        ]
        
        self.search_service = SearchService(self.db, self.session, self.ub_sets_config)
        
        # Fetching Queue for rate limiting
        self.fetch_queue = queue.Queue()
        threading.Thread(target=self._process_fetch_queue, daemon=True).start()

        self.create_menu()
        self.create_widgets()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Deck", command=self.save_deck)
        file_menu.add_command(label="Load Deck", command=self.load_deck)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Import Card List", command=self.import_card_list)
        tools_menu.add_command(label="Preview Deck", command=self.open_preview)
        tools_menu.add_command(label="Check Deck Legality", command=self.check_deck_legality)
        tools_menu.add_command(label="Get Recommendations", command=self.get_recommendations)
        tools_menu.add_command(label="Download Deck Images", command=self.download_deck_images)
        tools_menu.add_command(label="Bulk-Download all Images", command=self.download_all_images)
        tools_menu.add_separator()
        tools_menu.add_command(label="Update Database (Offline Mode)", command=self.update_database)

    def create_widgets(self):
        # Main Layout
        left_panel_frame = ttk.Frame(self)
        left_panel_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        center_panel_frame = ttk.Frame(self)
        center_panel_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel_frame = ttk.Frame(self)
        right_panel_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Panels ---
        self.search_panel = SearchPanel(
            left_panel_frame, 
            self.search_service, 
            self.on_search_result_select, 
            self.add_card_to_deck,
            self.open_search_settings,
            lambda: self.commander
        )
        self.search_panel.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons below search panel
        btn_frame = ttk.Frame(left_panel_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Add to Deck", command=self.add_card_to_deck).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Set as Commander", command=self.set_commander).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Get Recommendations (EDHRec)", command=self.get_recommendations).pack(fill=tk.X, pady=2)

        self.deck_panel = DeckPanel(
            center_panel_frame,
            self.on_deck_select,
            self.on_commander_click,
            self.remove_card,
            self.open_preview
        )
        self.deck_panel.pack(fill=tk.BOTH, expand=True)

        self.details_panel = DetailsPanel(right_panel_frame, self.image_loader)
        self.details_panel.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Event Handlers ---

    def on_search_result_select(self, card):
        if card.get('is_stub'):
            # Show loading in details
            # self.details_panel.display_loading() # TODO: Add this method
            if not card.get('fetching'):
                card['fetching'] = True
                self.fetch_queue.put(card)
        else:
            self.details_panel.display_card(card)

    def on_deck_select(self, card):
        self.details_panel.display_card(card)

    def on_commander_click(self):
        if self.commander:
            self.details_panel.display_card(self.commander)

    def add_card_to_deck(self):
        cards = self.search_panel.get_selected_cards()
        if not cards:
            return
        
        added_count = 0
        errors = []

        for card in cards:
            success, msg = self._add_single_card(card)
            if success:
                added_count += 1
            elif msg:
                errors.append(msg)
        
        if errors and added_count == 0:
             messagebox.showwarning("Add Card", errors[0])

    def _add_single_card(self, card):
        # If stub, ensure fetching
        if card.get('is_stub'):
            if not card.get('fetching'):
                card['fetching'] = True
                self.fetch_queue.put(card)
        
        card_name = card.get('name')
        type_line = card.get('type_line', '')

        # Check if already commander
        if self.commander and self.commander.get('name') == card_name:
             return False, "This card is already your Commander."

        # Check Singleton Rule
        basics = ["Plains", "Island", "Swamp", "Mountain", "Forest", 
                  "Snow-Covered Plains", "Snow-Covered Island", "Snow-Covered Swamp", 
                  "Snow-Covered Mountain", "Snow-Covered Forest", "Wastes"]
        
        if not type_line and card_name in basics:
            is_basic = True
        else:
            is_basic = "Basic" in type_line and "Land" in type_line

        is_unlimited = card_name in UNLIMITED_CARDS or \
                       "A deck can have any number of cards named" in card.get('oracle_text', '')

        current_count = sum(1 for c in self.deck if c.get('name') == card_name)
        
        if not is_basic and not is_unlimited and current_count >= 1:
            return False, f"You can only have one copy of {card_name} in your deck."
            
        self.deck.append(card)
        self.deck_panel.add_card(card)
        return True, None

    def remove_card(self):
        indices = self.deck_panel.get_selected_indices()
        if not indices:
            return
            
        # Remove from logic deck in reverse order
        # Note: DeckPanel removes from its own list, but we need to sync
        # Actually DeckPanel.remove_selected() removes from UI.
        # We need to remove from self.deck too.
        # The indices should match if we keep them in sync.
        
        # Let's do it carefully.
        # We should probably let DeckPanel handle the UI removal and return the indices removed?
        # Or just remove here and tell DeckPanel to refresh?
        # DeckPanel.remove_selected() removes from UI listbox.
        
        # Let's assume indices match.
        for index in reversed(indices):
            if index < len(self.deck):
                self.deck.pop(index)
        
        self.deck_panel.remove_selected()

    def set_commander(self):
        cards = self.search_panel.get_selected_cards()
        if not cards:
            return
            
        card = cards[0] # Take first
        
        # Check for Legendary Creature type
        type_line = card.get('type_line')
        if not type_line and 'card_faces' in card:
            type_line = card['card_faces'][0].get('type_line', '')
            
        if type_line and 'Legendary' in type_line and 'Creature' in type_line:
            self.commander = card
            self.deck_panel.update_commander(card, self.image_loader)
        else:
            messagebox.showerror("Invalid Commander", "Only Legendary Creatures can be set as Commander.")

    def get_recommendations(self):
        if not self.commander:
            messagebox.showwarning("No Commander", "Please set a commander first.")
            return
        
        # Show loading in search panel
        self.search_panel.set_results([{'name': "Loading recommendations...", 'is_stub': True}]) # Hacky
        
        self.edhrec_service.get_recommendations(self.commander.get('name'), self._on_recs_received)

    def _on_recs_received(self, recs, error):
        if error:
            self.after(0, lambda: self.search_panel.set_results([{'name': error, 'is_stub': True}]))
        else:
            self.after(0, lambda: self.search_panel.set_results(recs))

    def open_preview(self):
        DeckPreviewWindow(self, self.deck, self.commander, self.image_loader)

    def check_deck_legality(self):
        errors, warnings = self.legality_service.check_deck(self.deck, self.commander)
        
        if not errors and not warnings:
            messagebox.showinfo("Deck Check", "Deck is legal!")
            return

        msg = ""
        if errors:
            msg += "ERRORS:\n" + "\n".join(errors) + "\n\n"
        if warnings:
            msg += "WARNINGS:\n" + "\n".join(warnings)
            
        # Show in a scrollable text dialog if too long
        dialog = tk.Toplevel(self)
        dialog.title("Deck Check Results")
        dialog.geometry("500x400")
        
        text_area = tk.Text(dialog, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, msg)
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)

    def open_search_settings(self):
        # This logic was in main_window. It's UI.
        # We can move it to a dialog class or keep it here if simple.
        # Since we moved search prefs to SearchPanel, we should probably ask SearchPanel to open it?
        # Or pass the prefs to a dialog.
        # The SearchPanel has the prefs.
        # Let's implement a simple dialog here or in SearchPanel.
        # Actually, SearchPanel has open_settings_callback.
        # Let's move the logic to SearchPanel or a new Dialog class.
        # For now, let's keep it simple and implement it here but accessing SearchPanel's prefs.
        
        settings_win = tk.Toplevel(self)
        settings_win.title("Search Settings")
        settings_win.geometry("400x600")
        
        main_frame = ttk.Frame(settings_win, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="General Exclusions:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        prefs = self.search_panel.search_prefs
        
        ttk.Checkbutton(main_frame, text="Include Digital-Only Cards (Alchemy)", 
                       variable=prefs['include_alchemy']).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Checkbutton(main_frame, text="Include Silver-Bordered Cards (Un-sets)", 
                       variable=prefs['include_silver']).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Checkbutton(main_frame, text="Include Playtest Cards", 
                       variable=prefs['include_playtest']).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Checkbutton(main_frame, text="Include Oversized Cards", 
                       variable=prefs['include_oversized']).pack(anchor=tk.W, padx=20, pady=2)
        ttk.Checkbutton(main_frame, text="Include Funny / Joke Cards", 
                       variable=prefs['include_funny']).pack(anchor=tk.W, padx=20, pady=2)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        ttk.Label(main_frame, text="Universes Beyond (Crossovers):", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        def toggle_ub_group():
            val = prefs['include_ub_group'].get()
            for _, key, _ in self.ub_sets_config:
                prefs[key].set(val)
            prefs['ub_other'].set(val)

        ttk.Checkbutton(main_frame, text="Include All Universes Beyond", 
                       variable=prefs['include_ub_group'],
                       command=toggle_ub_group).pack(anchor=tk.W, padx=5, pady=2)
        
        ub_frame = ttk.Frame(main_frame)
        ub_frame.pack(anchor=tk.W, padx=20)
        
        for name, key, _ in self.ub_sets_config:
            ttk.Checkbutton(ub_frame, text=name, variable=prefs[key]).pack(anchor=tk.W, pady=1)
            
        ttk.Checkbutton(ub_frame, text="Other / Secret Lair", variable=prefs['ub_other']).pack(anchor=tk.W, pady=1)

        ttk.Button(settings_win, text="Close", command=settings_win.destroy).pack(pady=20)

    # --- Data Fetching Logic (Stubs) ---

    def _process_fetch_queue(self):
        while True:
            card_stub = self.fetch_queue.get()
            try:
                used_api = self._fetch_and_display_stub(card_stub)
                if used_api:
                    time.sleep(0.1) 
            except Exception as e:
                print(f"Queue error: {e}")
            finally:
                self.fetch_queue.task_done()

    def _fetch_and_display_stub(self, card_stub):
        name = card_stub['name']
        
        # Try local DB first
        local_card = self.db.get_card(name)
        if local_card:
            self.after(0, lambda: self._replace_stub_in_results(card_stub, local_card))
            return False

        try:
            response = self.session.get("https://api.scryfall.com/cards/named", params={'exact': name})
            if response.status_code == 200:
                full_card = response.json()
                self.db.save_card(full_card)
                self.after(0, lambda: self._replace_stub_in_results(card_stub, full_card))
                return True
            elif response.status_code == 404:
                response = self.session.get("https://api.scryfall.com/cards/named", params={'fuzzy': name})
                if response.status_code == 200:
                    full_card = response.json()
                    self.db.save_card(full_card)
                    self.after(0, lambda: self._replace_stub_in_results(card_stub, full_card))
                    return True
                    
        except Exception as e:
            print(f"Error fetching stub: {e}")
        return False

    def _replace_stub_in_results(self, stub, full_card):
        try:
            stub.update(full_card)
            if 'is_stub' in stub:
                del stub['is_stub']
            if 'fetching' in stub:
                del stub['fetching']
            
            # Refresh display if selected
            # We need to check if this card is currently selected in SearchPanel
            # SearchPanel doesn't expose selection easily, but we can check if DetailsPanel is showing it?
            # Actually, if we update the object in place, and then call display_card again if it matches...
            
            # Let's just refresh details panel if it's showing this card
            # But DetailsPanel doesn't know which card it's showing (it just shows data).
            # We can check if the name matches.
            # Or we can just re-trigger selection logic if we knew what was selected.
            
            # For now, let's just rely on user re-clicking or if we can trigger a refresh.
            # If we are currently viewing this card:
            # We can't easily know.
            pass 
        except Exception as e:
            print(f"Error replacing stub: {e}")

    # --- Bulk Operations ---

    def update_database(self):
        if messagebox.askyesno("Update Database", "This will download ~100MB of card data. It may take a few minutes. Continue?"):
            self.progress_window = tk.Toplevel(self)
            self.progress_window.title("Updating Database")
            self.progress_window.geometry("400x150")
            
            ttk.Label(self.progress_window, text="Downloading data...").pack(pady=10)
            
            self.progress_bar = ttk.Progressbar(self.progress_window, orient=tk.HORIZONTAL, length=300, mode='determinate')
            self.progress_bar.pack(pady=10)
            
            self.progress_label = ttk.Label(self.progress_window, text="Starting...")
            self.progress_label.pack(pady=5)
            
            self.data_updater.update_database(self._update_progress_ui, self._on_db_update_complete)

    def _update_progress_ui(self, percent, current, total, status_text):
        self.after(0, lambda: self._do_update_progress(percent, status_text))

    def _do_update_progress(self, percent, status_text):
        if hasattr(self, 'progress_bar'):
             self.progress_bar['value'] = percent
        if hasattr(self, 'progress_label'):
             self.progress_label.config(text=status_text)

    def _on_db_update_complete(self, success, message):
        self.after(0, lambda: self._do_db_complete(success, message))

    def _do_db_complete(self, success, message):
        if hasattr(self, 'progress_window'):
            self.progress_window.destroy()
        messagebox.showinfo("Update", message)

    def download_all_images(self):
        # This logic is still a bit complex to move entirely to service without UI feedback.
        # We can keep it here or move to a Dialog class.
        # For now, let's keep it here but use ImageService.
        count = self.db.count()
        if count == 0:
             messagebox.showinfo("Info", "Database is empty. Please update database first.")
             return

        if not messagebox.askyesno("Bulk-Download all Images", 
            f"This will download images for ALL {count} cards in the database.\n\n"
            "WARNING: This process will take a VERY long time (hours) and use significant disk space.\n\n"
            "Are you sure you want to continue?"):
            return

        self.progress_window = tk.Toplevel(self)
        self.progress_window.title("Downloading All Images")
        self.progress_window.geometry("400x200")
        
        self.progress_label = ttk.Label(self.progress_window, text="Starting...")
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_window, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        self.stop_download = False
        stop_btn = ttk.Button(self.progress_window, text="Stop Download", command=self.stop_download_process)
        stop_btn.pack(pady=10)
        
        self.progress_window.protocol("WM_DELETE_WINDOW", self.stop_download_process)
        
        threading.Thread(target=self._run_download_all_images, args=(count,), daemon=True).start()

    def stop_download_process(self):
        self.stop_download = True
        if hasattr(self, 'progress_label'):
            self.progress_label.config(text="Stopping...")

    def _run_download_all_images(self, total_count):
        cache_dir = "image_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        generator = self.db.get_all_cards_generator()
        
        for i, card in enumerate(generator):
            if self.stop_download:
                break
                
            if i % 50 == 0:
                self.after(0, lambda c=i, t=total_count, n=card.get('name'): self._update_dl_progress(c, t, n))
            
            urls = self.image_loader.get_card_image_urls(card)
            for url in urls:
                self.image_loader.download_image_to_cache(url)
            
        self.after(0, self.progress_window.destroy)
        if self.stop_download:
             self.after(0, lambda: messagebox.showinfo("Stopped", f"Download stopped.\nProcessed: {i} cards"))
        else:
             self.after(0, lambda: messagebox.showinfo("Complete", "All images downloaded."))

    def download_deck_images(self):
        if not self.deck and not self.commander:
            messagebox.showinfo("Info", "Deck is empty.")
            return

        if not messagebox.askyesno("Download Images", f"Download images for {len(self.deck) + (1 if self.commander else 0)} cards?"):
            return

        self.progress_window = tk.Toplevel(self)
        self.progress_window.title("Downloading Images")
        self.progress_window.geometry("300x150")
        
        self.progress_label = ttk.Label(self.progress_window, text="Starting...")
        self.progress_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_window, orient=tk.HORIZONTAL, length=250, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        threading.Thread(target=self._run_download_images, daemon=True).start()

    def _run_download_images(self):
        cards = self.deck[:]
        if self.commander:
            cards.append(self.commander)
            
        total = len(cards)
        
        for i, card in enumerate(cards):
            self.after(0, lambda i=i, name=card.get('name'): self._update_dl_progress(i, total, name))
            urls = self.image_loader.get_card_image_urls(card)
            for url in urls:
                self.image_loader.download_image_to_cache(url)
            
        self.after(0, self.progress_window.destroy)
        self.after(0, lambda: messagebox.showinfo("Complete", "Image download complete."))

    def _update_dl_progress(self, current, total, name):
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = (current / total) * 100
        if hasattr(self, 'progress_label'):
            self.progress_label.config(text=f"Downloading: {name}")

    def on_closing(self):
        if self.deck or self.commander:
            response = messagebox.askyesnocancel("Quit", "Do you want to save your deck before quitting?")
            if response is None: # Cancel
                return
            if response: # Yes
                if not self.save_deck():
                    return
        self.destroy()

    def save_deck(self):
        if not self.deck and not self.commander:
            messagebox.showinfo("Info", "Deck is empty.")
            return False

        # Ensure decks directory exists
        decks_dir = os.path.join(os.getcwd(), "decks")
        if not os.path.exists(decks_dir):
            os.makedirs(decks_dir)

        initial_file = "deck.txt"
        if self.commander:
            name = self.commander.get('name', 'deck')
            name = re.sub(r'[<>:"/\\|?*]', '', name)
            initial_file = f"{name}.txt"

        file_path = filedialog.asksaveasfilename(
            initialdir=decks_dir,
            initialfile=initial_file,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return False
            
        try:
            self.deck_service.save_deck(file_path, self.deck, self.commander)
            messagebox.showinfo("Success", "Deck saved successfully.")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save deck: {e}")
            return False

    def load_deck(self):
        if self.deck or self.commander:
            if not messagebox.askyesno("Load Deck", "This will clear the current deck. Continue?"):
                return

        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Clear current deck
            self.deck = []
            self.commander = None
            self.deck_panel.clear_deck()
            self.deck_panel.update_commander(None, self.image_loader)

            card_names = self.deck_service.load_deck(file_path)
            self._process_imported_list(card_names)
            
            # Prompt for commander if deck is not empty
            if self.deck:
                self.after(500, self.prompt_commander_selection)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load deck: {e}")

    def prompt_commander_selection(self):
        dialog = tk.Toplevel(self)
        dialog.title("Select Commander")
        dialog.geometry("400x500")
        
        ttk.Label(dialog, text="Select your Commander from the loaded deck:").pack(pady=10)
        
        listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Sort alphabetically
        sorted_deck = sorted(self.deck, key=lambda c: c.get('name'))
        
        for card in sorted_deck:
            listbox.insert(tk.END, card.get('name'))
            
        def on_select():
            selection = listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            card_name = listbox.get(index)
            
            # Find card object in deck
            selected_card = next((c for c in self.deck if c.get('name') == card_name), None)
            
            if selected_card:
                # Set as commander
                self.commander = selected_card
                self.deck_panel.update_commander(selected_card, self.image_loader)
                
                # Remove from deck
                self.deck.remove(selected_card)
                self.deck_panel.refresh_deck(self.deck)
                
                dialog.destroy()
                messagebox.showinfo("Commander Set", f"{card_name} set as Commander.")

        ttk.Button(dialog, text="Set as Commander", command=on_select).pack(pady=10)
        ttk.Button(dialog, text="Skip", command=dialog.destroy).pack(pady=5)

    def import_card_list(self):
        # Create a dialog
        dialog = tk.Toplevel(self)
        dialog.title("Import Card List")
        dialog.geometry("400x500")

        ttk.Label(dialog, text="Paste card names (one per line):").pack(pady=5)
        
        text_area = tk.Text(dialog, width=40, height=20)
        text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        def do_import():
            content = text_area.get("1.0", tk.END)
            lines = content.split('\n')
            card_names = self.deck_service.parse_card_list(lines)
            self._process_imported_list(card_names)
            dialog.destroy()

        ttk.Button(dialog, text="Import", command=do_import).pack(pady=10)

    def _process_imported_list(self, card_names):
        # Clear current deck if calling from load_deck? 
        # Actually load_deck clears it before calling this if we want.
        # But import_card_list appends.
        # Let's make this just add cards.
        # load_deck logic needs to clear first.
        
        # Wait, load_deck in previous implementation cleared the deck.
        # I should probably clear it in load_deck before calling this.
        # Yes, I did that in the previous implementation of load_deck.
        # But here I am calling _process_imported_list which just adds.
        # So I need to clear in load_deck.
        
        # Let's refine load_deck to clear first.
        
        added_count = 0
        errors = []
        
        for card_name in card_names:
            card_stub = {'name': card_name, 'is_stub': True}
            success, msg = self._add_single_card(card_stub)
            if success:
                added_count += 1
            elif msg:
                errors.append(f"{card_name}: {msg}")
        
        messagebox.showinfo("Import Complete", f"Processed {added_count} cards.\nErrors: {len(errors)}")
        if errors:
            print("\n".join(errors))
