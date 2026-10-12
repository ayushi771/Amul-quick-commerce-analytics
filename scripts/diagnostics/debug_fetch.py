"""
Diagnostic: shows exactly what scrape_amul_catalogue.py's request actually
receives, so we can tell whether the site is blocking the scraper (bot
protection / Cloudflare challenge) vs. a selector mismatch.

Run: python -m scripts.diagnostics.debug_fetch
Then open data/output/debug_response.html in a text editor / browser.
"""

from pathlib import Path

import requests
from pipeline.config import AMUL_BRAND_URL, REQUEST_HEADERS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "debug_response.html"

resp = requests.get(AMUL_BRAND_URL, headers=REQUEST_HEADERS, timeout=20)

print("Status code:", resp.status_code)
print("Response length (chars):", len(resp.text))
print("Contains 'Showing':", "Showing" in resp.text)
print("Contains 'Amul Milk Shake':", "Amul Milk Shake" in resp.text)
print("Contains 'Just a moment' (Cloudflare challenge):", "Just a moment" in resp.text)
print("Contains 'captcha':", "captcha" in resp.text.lower())
print("Contains '/en/product/':", "/en/product/" in resp.text)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_PATH.open("w", encoding="utf-8") as f:
    f.write(resp.text)

print(f"\nFull response saved to {OUTPUT_PATH} — open it and compare to the real site.")
print("\n--- First 1000 characters of response ---")
print(resp.text[:1000])