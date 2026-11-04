#!/usr/bin/env python3
"""Download Cambodia craft photos into backend/media for the demo seed.

Sources are Wikimedia Commons / CC0-friendly CDN URLs (silk, pottery, markets, wood).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "media" / "products"
SHOPS = ROOT / "media" / "shops"

# Direct image URLs themed to Khmer crafts / Cambodia markets (Wikimedia + Unsplash).
PRODUCT_URLS = {
    "P01": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Wood_carving_Cambodia.jpg/1280px-Wood_carving_Cambodia.jpg",
    "P02": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=1200&q=80",  # carved wood craft
    "P03": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=80",  # floral accessory
    "P04": "https://upload.wikimedia.org/wikipedia/commons/8/8a/Khmersilk.JPG",
    "P05": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Ikat_technique_in_Cambodia.jpg/1280px-Ikat_technique_in_Cambodia.jpg",
    "P06": "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=1200&q=80",  # tools
    "P07": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Khmersampothol.JPG/800px-Khmersampothol.JPG",
    "P08": "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?auto=format&fit=crop&w=1200&q=80",  # brass/metal tools
    "P09": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?auto=format&fit=crop&w=1200&q=80",  # wood kitchen board
    "P10": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Pidan_textile.jpg/800px-Pidan_textile.jpg",
    "P11": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?auto=format&fit=crop&w=1200&q=80",  # textile craft
    "P12": "https://images.unsplash.com/photo-1590736969955-71cc94901144?auto=format&fit=crop&w=1200&q=80",  # fabric bags
    "P13": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=80",  # market tote
    "P14": "https://images.unsplash.com/photo-1622560480605-d87610583959?auto=format&fit=crop&w=1200&q=80",  # leather goods
    "P15": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=1200&q=80",  # leather journal
    "P16": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Cambodian_pottery.jpg/1280px-Cambodian_pottery.jpg",
    "P17": "https://images.unsplash.com/photo-1610701596007-11502861dcfa?auto=format&fit=crop&w=1200&q=80",  # ceramic-ish craft fallback; overwritten if pottery works
    "P18": "https://images.unsplash.com/photo-1456513080880-7d36d7d0a5ea?auto=format&fit=crop&w=1200&q=80",  # paper/bookmark
    "P19": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Hol%2C_silk%2C_Kamer%2C_East-West_Center.JPG/1280px-Hol%2C_silk%2C_Kamer%2C_East-West_Center.JPG",
}

# Prefer Cambodia-specific pottery for cups if available via Unsplash SE Asia ceramics
PRODUCT_URLS["P17"] = "https://images.unsplash.com/photo-1493106641515-6b5631de4bb9?auto=format&fit=crop&w=1200&q=80"

SHOP_URLS = {
    "V01": "https://images.unsplash.com/photo-1452860606245-08befc0ff44b?auto=format&fit=crop&w=1200&q=80",  # wood workshop
    "V02": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=80",
    "V03": "https://upload.wikimedia.org/wikipedia/commons/8/8a/Khmersilk.JPG",
    "V04": "https://images.unsplash.com/photo-1504148455328-c376907d081c?auto=format&fit=crop&w=1200&q=80",
    "V05": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?auto=format&fit=crop&w=1200&q=80",
    "V06": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Ikat_technique_in_Cambodia.jpg/1280px-Ikat_technique_in_Cambodia.jpg",
    "V07": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=80",
    "V08": "https://images.unsplash.com/photo-1622560480605-d87610583959?auto=format&fit=crop&w=1200&q=80",
    "V09": "https://images.unsplash.com/photo-1493106641515-6b5631de4bb9?auto=format&fit=crop&w=1200&q=80",
    "V10": "https://images.unsplash.com/photo-1456513080880-7d36d7d0a5ea?auto=format&fit=crop&w=1200&q=80",
}

# Extra Cambodia craft fallbacks if a primary URL 404s
FALLBACKS = [
    "https://upload.wikimedia.org/wikipedia/commons/8/8a/Khmersilk.JPG",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Ikat_technique_in_Cambodia.jpg/1280px-Ikat_technique_in_Cambodia.jpg",
    "https://images.unsplash.com/photo-1528698827591-e19ccd7bc23d?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?auto=format&fit=crop&w=1200&q=80",
]


def fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": "BazaarSeed/1.0 (demo media)"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = response.read()
            if len(data) < 2000:
                return None
            return data
    except Exception as exc:  # noqa: BLE001
        print(f"  fail {url}: {exc}")
        return None


def save(path: Path, urls: list[str]) -> bool:
    for url in urls:
        data = fetch(url)
        if data:
            path.write_bytes(data)
            print(f"  ok {path.name} ({len(data) // 1024} KB)")
            return True
    print(f"  MISS {path.name}")
    return False


def main() -> None:
    PRODUCTS.mkdir(parents=True, exist_ok=True)
    SHOPS.mkdir(parents=True, exist_ok=True)
    print("Products")
    for pid, url in PRODUCT_URLS.items():
        save(PRODUCTS / f"{pid}.jpg", [url, *FALLBACKS])
    print("Shops")
    for vid, url in SHOP_URLS.items():
        save(SHOPS / f"{vid}.jpg", [url, *FALLBACKS])


if __name__ == "__main__":
    main()
