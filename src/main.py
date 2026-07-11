import requests
import time

BASE_URL = "https://nhentai.net/" # https://api.example.com

def get_info(id, session):
    data = session.get(f"{BASE_URL}g/{id}/")