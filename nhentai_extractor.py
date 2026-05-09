import os
import requests
import time
from dotenv import load_dotenv
from pathlib import Path
import random


load_dotenv(dotenv_path=Path(__file__).parent / ".env")
API = os.getenv("API_KEY")
APP = os.getenv("APP_NAME")


class NHentaiClient:
    BASE_URL = "https://nhentai.net/api/v2"

    def __init__(self, api=API, apps=APP):
        self.session = requests.Session()
        headers = {
            "accept": "application/json",
            "User-Agent": apps
        }
        if api:
            headers["Authorization"] = f"Key {api}"
        self.session.headers.update(headers)

    def _get(self, path, params=None, retries=3):
        url = self.BASE_URL + path
        for i in range(retries):
            try:
                res = self.session.get(url, params=params, timeout=30)
                res.raise_for_status()
                return res.json()
            except requests.exceptions.ConnectTimeout:
                time.sleep(2 ** i)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError):
                break
        return None
    

    def get_info(self, id):
        gal = self._get(f"/galleries/{id}")
        if gal is None:
            return None
        id          = gal['id']
        id_media    = gal['media_id']
        title       = gal['title']['english']
        artists     = []
        groups      = []
        series      = []
        languages   = []
        tags        = []
        for tag in gal['tags']:
            type = tag['type']
            if type == 'artist':
                artists = tag['name']
            elif type == 'group':
                groups = tag['name']
            elif type == 'parody':
                series = tag['name']
            elif type == 'language':
                languages = tag['name']
            elif type == 'category':
                category = tag['name']
            elif type == 'tag':
                tags = tag['name']

        return {
            "id"        : id,
            "id_media"  : id_media,
            "title"     : title,
            "artists"   : artists,
            "groups"    : groups,
            "category"  : category,
            "series"    : series,
            "languages" : languages,
            "tags"      : tags
        }


    def get_imgs(self, id):
        data = self._get(f"/galleries/{id}")
        if data is None:
            return None
        
        sub     = random.choice(["i1", "i2", "i3", "i4"])
        base    = self.BASE_URL.replace("/api/v2", "")
        cdn     = base.replace("https://", f"https://{sub}.")
        imgs    = [f"{cdn}/{page['path']}" for page in data.get("pages", [])]

        return imgs




# DEBUG/LOGS
client = NHentaiClient()
gal_id = "571652"                # replace GALLERY_ID with an actual ID
result = client.get_info(gal_id) # replace GALLERY_ID with an actual ID 
if result:
    print(f"ID        : {result['id']}")
    print(f"Media ID  : {result['id_media']}")
    print(f"Title     : {result['title']}")
    print(f"Artists   : {result['artists']}")
    print(f"Groups    : {result['groups']}")
    print(f"Lang      : {result['languages']}")
    print(f"Series    : {result['series']}")
    print(f"Category  : {result['category']}")
    print(f"Tags      : {result['tags']}")

    
pages = client.get_imgs(gal_id)
if pages:
    for i, url in enumerate(pages, start=1):
        print(f"{url}")