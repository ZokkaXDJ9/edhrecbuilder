import requests
import re

class EDHRecService:
    def __init__(self, session=None):
        self.session = session if session else requests.Session()

    def get_recommendations(self, commander_name, callback):
        """
        Fetches recommendations for a commander.
        callback: function(results, error_message)
        """
        # Slugify for EDHRec
        # Remove // for split cards, take first part
        slug_name = commander_name.split(' // ')[0]
        slug = slug_name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)

        url = f"https://json.edhrec.com/pages/commanders/{slug}.json"
        print(f"Fetching {url}")
        
        try:
            r = self.session.get(url)
            if r.status_code != 200:
                callback(None, f"Could not find recommendations for {commander_name}")
                return
            
            data = r.json()
            cardlists = data.get('container', {}).get('json_dict', {}).get('cardlists', [])
            
            recs = []
            # Categories to include
            target_headers = ['High Synergy Cards', 'Top Cards', 'Creatures', 'Instants', 'Sorceries', 'Artifacts', 'Enchantments', 'Planeswalkers', 'Lands']
            
            for cl in cardlists:
                if cl.get('header') in target_headers:
                    for card in cl.get('cardviews', []):
                        recs.append({
                            'name': card.get('name'),
                            'is_stub': True
                        })
            
            # Remove duplicates while preserving order
            unique_recs = []
            seen = set()
            for r in recs:
                if r['name'] not in seen:
                    seen.add(r['name'])
                    unique_recs.append(r)

            callback(unique_recs, None)
            
        except Exception as e:
            print(f"EDHRec Error: {e}")
            callback(None, "Error fetching recommendations")
