import json
import os
import threading

class LegalityService:
    def __init__(self, session):
        self.session = session
        self.banned_cards = set()
        self.banlist_file = "banned_cards.json"
        self.load_banlist()

    def load_banlist(self):
        if os.path.exists(self.banlist_file):
            try:
                with open(self.banlist_file, 'r', encoding='utf-8') as f:
                    self.banned_cards = set(json.load(f))
            except Exception as e:
                print(f"Error loading banlist: {e}")

    def update_banlist(self):
        print("Updating banlist...")
        banned = set()
        # Scryfall query for cards banned in commander
        url = "https://api.scryfall.com/cards/search?q=banned:commander&unique=cards"
        try:
            while url:
                r = self.session.get(url)
                if r.status_code != 200:
                    print(f"Failed to fetch banlist: {r.status_code}")
                    break
                data = r.json()
                for card in data.get('data', []):
                    banned.add(card['name'])
                
                if data.get('has_more'):
                    url = data.get('next_page')
                else:
                    url = None
            
            if banned:
                self.banned_cards = banned
                with open(self.banlist_file, 'w', encoding='utf-8') as f:
                    json.dump(list(banned), f)
                print(f"Banlist updated. {len(banned)} cards.")
            
        except Exception as e:
            print(f"Error updating banlist: {e}")

    def check_deck(self, deck, commander):
        errors = []
        warnings = []
        
        if not commander:
            errors.append("No Commander set.")
            return errors, warnings

        # 1. Deck Size
        total_cards = len(deck) + 1
        if total_cards != 100:
            warnings.append(f"Deck size is {total_cards} (Standard is 100).")

        # 2. Color Identity
        cmd_identity = set(commander.get('color_identity', []))
        
        for card in deck:
            card_identity = set(card.get('color_identity', []))
            if not card_identity.issubset(cmd_identity):
                errors.append(f"Color Identity Error: {card['name']} ({''.join(sorted(card_identity))}) is not allowed in {commander['name']} ({''.join(sorted(cmd_identity))}) deck.")

        # 3. Banned Cards
        # Check Commander
        if commander['name'] in self.banned_cards:
             errors.append(f"BANNED: Commander {commander['name']} is banned in Commander.")
        elif 'legalities' in commander and commander['legalities'].get('commander') == 'banned':
             errors.append(f"BANNED: Commander {commander['name']} is marked as banned.")

        # Check Deck
        for card in deck:
            if card['name'] in self.banned_cards:
                errors.append(f"BANNED: {card['name']} is banned in Commander.")
            # Also check local legality if available (fallback or double check)
            elif 'legalities' in card and card['legalities'].get('commander') == 'banned':
                 errors.append(f"BANNED (Card Data): {card['name']} is marked as banned.")

        return errors, warnings
