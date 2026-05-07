import requests
from collections import defaultdict

BASE_API = "https://nhentai.net/api/v2/galleries/{}"

CDN_POOL = ["i1", "i2", "i3", "i4"]
CDN_FALLBACK_ORDER = ["i1", "i2", "i3", "i4"]
CDN_CACHE = {}

def fetch_gallery(gal_id: str) -> dict:
    url = BASE_API.format(gal_id)

    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        raise Exception(f"Gallery {gal_id} not found")

    return res.json()

def extract_id(url: str) -> str:
    return url.split("/g/")[1].strip("/")

def group_tags(tags: list[dict]) -> dict:
    grouped = defaultdict(list)

    for t in tags:
        grouped[t["type"]].append(t["name"])

    return grouped

def get_best_cdn() -> str:
    # bisa diganti health-check nanti
    return CDN_FALLBACK_ORDER[0]

def build_image_url(path: str, media_id: str, page: int) -> str:
    """
    fallback chain: i1 -> i4
    cache key per page
    """

    cache_key = f"{media_id}:{page}"

    if cache_key in CDN_CACHE:
        return CDN_CACHE[cache_key]

    for sub in CDN_FALLBACK_ORDER:
        url = f"https://{sub}.nhentai.net/{path}"

        # optional: lazy validation (bisa dimatikan kalau mau cepat)
        try:
            r = requests.head(url, timeout=3)
            if r.status_code == 200:
                CDN_CACHE[cache_key] = url
                return url
        except:
            continue

    # fallback terakhir
    url = f"https://i1.nhentai.net/{path}"
    CDN_CACHE[cache_key] = url
    return 

def parse_gallery(gal_id: str) -> dict:
    data = fetch_gallery(gal_id)
    tags = group_tags(data.get("tags", []))

    media_id = data["media_id"]

    images = [
        build_image_url(page["path"], media_id, i + 1)
        for i, page in enumerate(data["pages"])
    ]

    return {
        "id": data["id"],
        "title": data["title"]["pretty"],
        "media_id": media_id,
        "pages": data["num_pages"],

        "images": images,

        "categories": tags.get("category", []),
        "parodies": tags.get("parody", []),
        "artists": tags.get("artist", []),
        "groups": tags.get("group", []),
        "languages": tags.get("language", []),
        "tags": tags.get("tag", []),
    }

def fmt(v):
    return ", ".join(v) if v else "-"


if __name__ == "":
    url = "https://nhentai.net/g/571652"

    gid = extract_id(url)
    result = parse_gallery(gid)

    print("TITLE      :", result["title"])
    print("PARODIES   :", fmt(result["parodies"]))
    print("TAGS       :", fmt(result["title"]))
    print("ARTISTS    :", fmt(result["artists"]))
    print("GROUP      :", fmt(result["groups"]))
    print("LANGUAGES  :", fmt(result["languages"]))
    print("CATEGORIES :", fmt(result["categories"]))
    print("PAGES      :", result["pages"])