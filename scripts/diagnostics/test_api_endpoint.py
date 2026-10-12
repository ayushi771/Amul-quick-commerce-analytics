"""
Tests the real product-data API found via DevTools, directly with
`requests` — no browser automation needed if this works.

Run: python -m scripts.diagnostics.test_api_endpoint
"""

import json
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "output" / "api_response_sample.json"
API_URL = "https://shop.amul.com/api/1/entity/ms.products"

PARAMS = {
    "fields[name]": 1,
    "fields[brand]": 1,
    "fields[categories]": 1,
    "fields[alias]": 1,
    "fields[sku]": 1,
    "fields[price]": 1,
    "fields[compare_price]": 1,
    "fields[images]": 1,
    "fields[available]": 1,
    "fields[inventory_quantity]": 1,
    "fields[default_variant]": 1,
    "fields[variants]": 1,
    "filters[0][field]": "brand",
    "filters[0][value][0]": "Amul",
    "filters[0][operator]": "in",
    "filters[0][original]": 1,
    "limit": 16,
    "total": 1,
    "start": 0,
    "v": 6,
    "device_type": "mobile",
    "substore": "66505ff06510ee3d5903fd42",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://shop.amul.com/en/brand/amul",
}

resp = requests.get(API_URL, params=PARAMS, headers=HEADERS, timeout=20)

print("Status code:", resp.status_code)
print("Content-Type:", resp.headers.get("Content-Type"))

try:
    data = resp.json()
except Exception as e:
    print("Response was NOT valid JSON:", e)
    print(resp.text[:500])
    raise SystemExit(1)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Top-level keys:", list(data.keys()))

# Try to find the product list — StoreHippo usually returns it under a
# key like 'data', 'result', or 'items'. Print whichever is a list.
for key, value in data.items():
    if isinstance(value, list):
        print(f"\nKey '{key}' is a list with {len(value)} items.")
        if value:
            print("First item sample:")
            print(json.dumps(value[0], indent=2, ensure_ascii=False)[:1500])

print(f"\nFull response saved to {OUTPUT_PATH} — open it to inspect the full structure.")