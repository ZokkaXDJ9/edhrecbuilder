import os
import hashlib
import threading
from io import BytesIO
from PIL import Image, ImageTk
import requests

class ImageService:
    def __init__(self, session, cache_dir="image_cache"):
        self.session = session
        self.cache_dir = cache_dir
        self.image_cache = {} # Memory cache
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_image(self, url, callback, height=400):
        """
        Asynchronously loads an image from URL (or cache) and calls callback with ImageTk.PhotoImage.
        """
        if not url:
            return

        if url in self.image_cache:
            # Call callback immediately (but use after_idle or similar if in main thread? 
            # Caller usually handles thread safety or this runs in thread)
            # Since this might be called from UI thread, we should probably just return it 
            # or call callback. But callback expects to be called later?
            # Let's just call it.
            callback(self.image_cache[url])
            return

        threading.Thread(target=self._load_image_thread, args=(url, callback, height), daemon=True).start()

    def _get_cache_path(self, url):
        file_extension = os.path.splitext(url)[1]
        if not file_extension:
            file_extension = ".jpg"
        if '?' in file_extension:
            file_extension = file_extension.split('?')[0]
            
        filename = hashlib.md5(url.encode('utf-8')).hexdigest() + file_extension
        return os.path.join(self.cache_dir, filename)

    def _load_image_thread(self, url, callback, height):
        file_path = self._get_cache_path(url)

        try:
            img = None
            if os.path.exists(file_path):
                try:
                    img = Image.open(file_path)
                    img.load()
                except:
                    img = None # Corrupt

            if img is None:
                response = self.session.get(url)
                if response.status_code == 200:
                    img_data = response.content
                    img = Image.open(BytesIO(img_data))
                    with open(file_path, "wb") as f:
                        f.write(img_data)
            
            if img:
                if height:
                    base_height = height
                    h_percent = (base_height / float(img.size[1]))
                    w_size = int((float(img.size[0]) * float(h_percent)))
                    img = img.resize((w_size, base_height), Image.Resampling.BICUBIC)
                
                photo = ImageTk.PhotoImage(img)
                self.image_cache[url] = photo
                callback(photo)
        except Exception as e:
            print(f"Error loading image {url}: {e}")

    def download_image_to_cache(self, url):
        """
        Synchronously download image to cache if not exists.
        """
        file_path = self._get_cache_path(url)
        
        if not os.path.exists(file_path):
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
            except Exception as e:
                print(f"Failed to download {url}: {e}")

    def get_card_image_urls(self, card):
        """
        Extract all image URLs from a card object.
        """
        urls = []
        if 'image_uris' in card:
            if 'normal' in card['image_uris']: urls.append(card['image_uris']['normal'])
            if 'small' in card['image_uris']: urls.append(card['image_uris']['small'])
        elif 'card_faces' in card:
            for face in card['card_faces']:
                if 'image_uris' in face:
                    if 'normal' in face['image_uris']: urls.append(face['image_uris']['normal'])
                    if 'small' in face['image_uris']: urls.append(face['image_uris']['small'])
        return urls
