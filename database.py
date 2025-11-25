import sqlite3
import json

class CardDatabase:
    def __init__(self, db_path="cards.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS cards
                     (name TEXT PRIMARY KEY, 
                      json_data TEXT)''')
        
        # Check for type_line column and add if missing
        c.execute("PRAGMA table_info(cards)")
        columns = [info[1] for info in c.fetchall()]
        if 'type_line' not in columns:
            print("Migrating database: Adding type_line column...")
            c.execute("ALTER TABLE cards ADD COLUMN type_line TEXT")
            
        conn.commit()
        conn.close()

    def save_card(self, card_data):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Extract type_line for filtering
        type_line = card_data.get('type_line', '')
        if not type_line and 'card_faces' in card_data:
            type_line = card_data['card_faces'][0].get('type_line', '')

        c.execute("INSERT OR REPLACE INTO cards (name, json_data, type_line) VALUES (?, ?, ?)", 
                  (card_data.get('name'), json.dumps(card_data), type_line))
        conn.commit()
        conn.close()
    
    def get_card(self, name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Try exact match first
        c.execute("SELECT json_data FROM cards WHERE name = ?", (name,))
        row = c.fetchone()
        
        # If not found, try case-insensitive match
        if not row:
            c.execute("SELECT json_data FROM cards WHERE name LIKE ? LIMIT 1", (name,))
            row = c.fetchone()
            
        conn.close()
        if row:
            return json.loads(row[0])
        return None

    def search_cards(self, query, limit=100, filter_func=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Replace spaces with % for fuzzy-ish search
        formatted_query = query.replace(' ', '%')
        
        # Filter tokens in SQL directly using type_line column
        # Prioritize:
        # 1. Exact match (case-insensitive via LIKE without wildcards)
        # 2. Starts with
        # 3. Contains
        sql = """
            SELECT json_data FROM cards 
            WHERE name LIKE ? 
            AND (type_line IS NULL OR type_line NOT LIKE '%Token%')
            ORDER BY 
                CASE 
                    WHEN name LIKE ? THEN 0 
                    WHEN name LIKE ? THEN 1 
                    ELSE 2 
                END,
                name
        """
        
        # Params: 
        # 1. WHERE name LIKE %query%
        # 2. Exact match: query
        # 3. Starts with: query%
        
        c.execute(sql, (f"%{formatted_query}%", query, f"{formatted_query}%"))
        
        results = []
        # Iterate cursor directly to avoid loading all results
        for row in c:
            try:
                card = json.loads(row[0])
                
                # Apply Python-side filtering if provided
                if filter_func and not filter_func(card):
                    continue
                    
                results.append(card)
                if len(results) >= limit:
                    break
            except Exception as e:
                print(f"Error parsing card in search: {e}")
                continue
                
        conn.close()
        return results
    
    def bulk_import(self, cards_list, progress_callback=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION")
        total = len(cards_list)
        for i, card in enumerate(cards_list):
            type_line = card.get('type_line', '')
            if not type_line and 'card_faces' in card:
                type_line = card['card_faces'][0].get('type_line', '')

            c.execute("INSERT OR REPLACE INTO cards (name, json_data, type_line) VALUES (?, ?, ?)", 
                      (card.get('name'), json.dumps(card), type_line))
            if progress_callback and i % 250 == 0:
                progress_callback(i, total, card.get('name'))
        conn.commit()
        conn.close()

    def count(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT Count(*) FROM cards")
        count = c.fetchone()[0]
        conn.close()
        return count

    def get_all_cards_generator(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT json_data FROM cards")
        while True:
            rows = c.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                yield json.loads(row[0])
        conn.close()
