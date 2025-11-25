import threading

class SearchService:
    def __init__(self, db, session, ub_sets_config):
        self.db = db
        self.session = session
        self.ub_sets_config = ub_sets_config

    def search(self, query, filters, callback):
        """
        Initiates a search.
        callback: function(status_code, data)
        """
        threading.Thread(target=self._search_logic, args=(query, filters, callback), daemon=True).start()

    def _search_logic(self, query, filters, callback):
        # If query has syntax (:) assume advanced search and go to API
        # Otherwise try local DB first if populated
        
        use_local = ':' not in query and self.db.count() > 0
        
        if use_local:
            # Define filter function for local DB
            def local_filter(card):
                return self._check_card_against_filters(card, filters)

            # Pass filter function to DB search
            local_results = self.db.search_cards(query, limit=100, filter_func=local_filter)
            
            callback(200, {'data': local_results})
            return

        self._search_api(query, filters, callback)

    def _check_card_against_filters(self, card, filters):
        prefs = filters.get('prefs', {})
        
        # Build known sets from config
        known_ub_sets = set()
        ub_key_map = {} 
        for _, key, codes in self.ub_sets_config:
            for c in codes:
                known_ub_sets.add(c)
                ub_key_map[c] = key

        # 0. Commander Identity
        if 'commander_identity' in filters:
            card_id = set(card.get('color_identity', []))
            cmd_id = set(filters['commander_identity'])
            if not card_id.issubset(cmd_id):
                return False

        # 1. Colors
        if 'colors' in filters:
            card_id = set(card.get('color_identity', []))
            selected_id = set(filters['colors'])
            if not card_id.issubset(selected_id):
                return False

        # 2. Type
        if 'type' in filters:
            t_filter = filters['type'].lower()
            t_line = card.get('type_line', '').lower()
            if 'card_faces' in card:
                match = False
                for face in card['card_faces']:
                    if t_filter in face.get('type_line', '').lower():
                        match = True
                        break
                if not match and t_filter not in t_line: 
                    return False
            else:
                if t_filter not in t_line:
                    return False

        # 3. Preferences
        
        # Alchemy / Paper
        if not prefs.get('include_alchemy', False):
            if 'paper' not in card.get('games', []):
                return False
        
        # Silver Border
        if not prefs.get('include_silver', False):
            if card.get('border_color') == 'silver':
                return False
        
        # Playtest
        if not prefs.get('include_playtest', False):
            if card.get('set_type') == 'memorabilia' or 'playtest' in card.get('promo_types', []):
                return False

        # Oversized
        if not prefs.get('include_oversized', False):
            if card.get('oversized', False):
                return False

        # Funny
        if not prefs.get('include_funny', False):
            if card.get('set_type') == 'funny':
                return False

        # Universes Beyond
        is_ub = False
        if card.get('security_stamp') == 'triangle':
            is_ub = True
        
        card_set = card.get('set', '').lower()
        
        # Check specific sets
        excluded_ub = False
        
        if card_set in ub_key_map:
            is_ub = True
            key = ub_key_map[card_set]
            if not prefs.get(key, True):
                excluded_ub = True
        
        if excluded_ub:
            return False
            
        # Check "Other"
        if is_ub and card_set not in known_ub_sets:
            if not prefs.get('ub_other', True):
                return False

        return True

    def _search_api(self, query, filters, callback):
        try:
            # Build query parts
            query_parts = [query]
            
            # Exclude tokens
            query_parts.append("-type:token")
            
            # Apply filters
            # Handle Colors and Commander Identity together
            allowed_colors = None
            
            if 'commander_identity' in filters:
                allowed_colors = set(filters['commander_identity'])
                
            if 'colors' in filters:
                selected = set(filters['colors'])
                if allowed_colors is not None:
                    allowed_colors = allowed_colors.intersection(selected)
                else:
                    allowed_colors = selected
            
            if allowed_colors is not None:
                colors = "".join(allowed_colors).lower()
                if not colors:
                    query_parts.append("id:c") 
                else:
                    query_parts.append(f"id<={colors}")
                
            if 'type' in filters:
                query_parts.append(f"t:{filters['type']}")

            # Apply Search Preferences
            prefs = filters.get('prefs', {})
            
            if not prefs.get('include_alchemy', False):
                query_parts.append("game:paper")
            
            if not prefs.get('include_silver', False):
                query_parts.append("-border:silver")
                
            if not prefs.get('include_playtest', False):
                query_parts.append("-is:playtest")
                
            if not prefs.get('include_oversized', False):
                query_parts.append("-is:oversized")
                
            if not prefs.get('include_funny', False):
                query_parts.append("-is:funny")

            # Universes Beyond Logic
            all_ub_unchecked = True
            for _, key, _ in self.ub_sets_config:
                if prefs.get(key, True):
                    all_ub_unchecked = False
                    break
            if prefs.get('ub_other', True):
                all_ub_unchecked = False
                
            if all_ub_unchecked:
                query_parts.append("-is:ub")
            else:
                exclusions = []
                for _, key, codes in self.ub_sets_config:
                    if not prefs.get(key, True):
                        set_query = " or ".join([f"set:{c}" for c in codes])
                        exclusions.append(f"({set_query})")
                
                if exclusions:
                    query_parts.append(f"-({' or '.join(exclusions)})")
                
                if not prefs.get('ub_other', True):
                    known_sets_query = []
                    for _, _, codes in self.ub_sets_config:
                        known_sets_query.extend([f"set:{c}" for c in codes])
                    
                    known_sets_str = " or ".join(known_sets_query)
                    query_parts.append(f"-(is:ub -({known_sets_str}))")

            full_query = " ".join(query_parts)
            print(f"Search Query: {full_query}")
            
            params = {'q': full_query}
            response = self.session.get("https://api.scryfall.com/cards/search", params=params, timeout=10)
            data = response.json()

            callback(response.status_code, data)
        except Exception as e:
            print(f"Error searching: {e}")
            callback(500, {})
