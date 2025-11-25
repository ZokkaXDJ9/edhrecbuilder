import requests
import json
import threading

class DataUpdater:
    def __init__(self, db, session=None):
        self.db = db
        self.session = session if session else requests.Session()

    def update_database(self, progress_callback, completion_callback):
        """
        Updates the database in a background thread.
        progress_callback: function(percent, current, total, status_text)
        completion_callback: function(success, message)
        """
        threading.Thread(target=self._run_update_db, args=(progress_callback, completion_callback), daemon=True).start()

    def _run_update_db(self, progress_callback, completion_callback):
        try:
            progress_callback(0, 0, 0, "Fetching bulk data info...")
            r = self.session.get("https://api.scryfall.com/bulk-data")
            data = r.json()
            oracle_cards = next(item for item in data['data'] if item['type'] == 'oracle_cards')
            download_uri = oracle_cards['download_uri']
            
            progress_callback(0, 0, 0, "Downloading card data...")
            
            r = self.session.get(download_uri, stream=True)
            total_length = int(r.headers.get('content-length', 0))
            
            content = b""
            if total_length == 0:
                content = r.content
                progress_callback(50, 0, 0, "Downloading...")
            else:
                dl = 0
                for data in r.iter_content(chunk_size=8192):
                    dl += len(data)
                    content += data
                    percent = int(50 * dl / total_length)
                    progress_callback(percent, 0, 0, "Downloading...")
            
            progress_callback(50, 0, 0, "Parsing JSON...")
            cards = json.loads(content)
            
            progress_callback(50, 0, len(cards), f"Importing {len(cards)} cards...")
            
            def db_progress(current, total, name):
                # Calculate percentage for the second 50% (import phase)
                percent = 50 + ((current / total) * 50)
                progress_callback(percent, current, total, f"Importing: {name}")

            self.db.bulk_import(cards, db_progress)
            
            completion_callback(True, "Database updated successfully.")
            
        except Exception as e:
            print(f"Update failed: {e}")
            completion_callback(False, f"Update failed: {e}")
