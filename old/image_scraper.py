import argparse
import os
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}


def get_image_urls(page_url: str) -> list[str]:
    """Fetch the page and return a list of absolute image URLs."""
    response = requests.get(page_url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")

    urls = []
    for img in img_tags:
        # Handle common lazy-load attributes too, falling back to src
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            continue
        absolute_url = urljoin(page_url, src)
        if absolute_url not in urls:
            urls.append(absolute_url)
    return urls

# Download a single image to the folder. Returns the saved path or None on failure.
def download_image(url: str, folder: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # Build a filename from the URL path
        path = urlparse(url).path
        filename = os.path.basename(path) or "image"
        if "." not in filename:
            # Guess extension from content-type
            content_type = resp.headers.get("Content-Type", "")
            ext = content_type.split("/")[-1].split(";")[0] if "/" in content_type else "jpg"
            filename = f"{filename}.{ext}"

        filepath = os.path.join(folder, filename)

        # Avoid overwriting files with the same name
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{base}_{counter}{ext}"
            counter += 1

        with open(filepath, "wb") as f:
            f.write(resp.content)
        return filepath
    except Exception as e:
        print(f"  Failed: {url} ({e})")
        return None


def main():
    parser = argparse.ArgumentParser(description="Scrape and download images from a webpage.")
    parser.add_argument("url", help="URL of the page to scrape")
    parser.add_argument("-o", "--output", default="downloaded_images", help="Output folder")
    parser.add_argument("-m", "--max", type=int, default=None, help="Max number of images to download")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print(f"Fetching page: {args.url}")
    try:
        image_urls = get_image_urls(args.url)
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        sys.exit(1)

    if args.max:
        image_urls = image_urls[: args.max]

    print(f"Found {len(image_urls)} image(s). Downloading to '{args.output}'...\n")

    saved = 0
    for i, url in enumerate(image_urls, 1):
        print(f"[{i}/{len(image_urls)}] {url}")
        result = download_image(url, args.output)
        if result:
            saved += 1

    print(f"\nDone. Saved {saved}/{len(image_urls)} images to '{args.output}'.")


if __name__ == "__main__":
    main()
