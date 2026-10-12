"""
Diagnostic: shows exactly what scrape_amul_catalogue.py's request actually
receives, so we can tell whether the site is blocking the scraper (bot
protection / Cloudflare challenge) vs. a selector mismatch.

Run: python debug_fetch.py
Then open debug_response.html in a text editor / browser and look at it.
"""

import requests
from config import AMUL_BRAND_URL, REQUEST_HEADERS

resp = requests.get(AMUL_BRAND_URL, headers=REQUEST_HEADERS, timeout=20)

print("Status code:", resp.status_code)
print("Response length (chars):", len(resp.text))
print("Contains 'Showing':", "Showing" in resp.text)
print("Contains 'Amul Milk Shake':", "Amul Milk Shake" in resp.text)
print("Contains 'Just a moment' (Cloudflare challenge):", "Just a moment" in resp.text)
print("Contains 'captcha':", "captcha" in resp.text.lower())
print("Contains '/en/product/':", "/en/product/" in resp.text)

with open("debug_response.html", "w", encoding="utf-8") as f:
    f.write(resp.text)

print("\nFull response saved to debug_response.html — open it and compare to the real site.")
print("\n--- First 1000 characters of response ---")
print(resp.text[:1000])