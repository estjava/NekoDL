import requests
import random
import time

BASE_URL = "https://google.com/"

# Random Session Generator
def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "id-ID,id;q=0.9",
    })
    return session

def get_urls(urls):
    session = get_session()
    for url in urls:
        try:
            response = session.get(url)
            if response.status_code == 200:
                print(f"Successfully accessed: {url}")
            else:
                print(f"Failed to access: {url} with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error accessing {url}: {e}")
        time.sleep(random.uniform(3, 7))  # Random delay between requests