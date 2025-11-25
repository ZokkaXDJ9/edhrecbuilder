import re

class DeckService:
    def save_deck(self, file_path, deck, commander):
        """Saves the deck and commander to a text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            if commander:
                f.write(f"1x {commander.get('name')}\n")
            
            for card in deck:
                f.write(f"1x {card.get('name')}\n")

    def load_deck(self, file_path):
        """Loads a deck from a text file and returns a list of card names."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return self.parse_card_list(lines)

    def parse_card_list(self, lines):
        """Parses a list of strings into card names."""
        card_names = []
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Basic parsing: remove leading numbers and 'x' (e.g. "1x Sol Ring" -> "Sol Ring")
            card_name = re.sub(r'^\d+\s*x?\s*', '', line)
            card_names.append(card_name)
        return card_names
