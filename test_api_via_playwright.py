"""
Loads the Amul catalogue page in a real headless browser (so Cloudflare's
bot checks and the site's own `tid` token generation happen naturally,
exactly like a real visitor), and listens for the ms.products API
response instead of parsing rendered HTML. This gives us clean JSON
with none of the fragility of clicking "Load More" and re-scraping HTML.

Run: python test_api_via_playwright.py
"""

import json
from playwright.sync_api import sync_playwright

captured_responses = []


def handle_response(response):
    if "ms.products" in response.url and response.status == 200:
        try:
            data = response.json()
            captured_responses.append({"url": response.url, "data": data})
            data_len = len(data.get("data", [])) if isinstance(data, dict) else "?"
            print(f"Captured response #{len(captured_responses)}: {data_len} item(s) in 'data' "
                  f"| start={_get_param(response.url, 'start')} limit={_get_param(response.url, 'limit')}")
        except Exception as e:
            print(f"Response matched but wasn't JSON: {e}")


def _get_param(url, name):
    import re
    m = re.search(rf"[?&]{name}=([^&]+)", url)
    return m.group(1) if m else "?"


AHMEDABAD_COORDS = {"latitude": 23.0225, "longitude": 72.5714}  # matches REFERENCE_LOCATION
KNOWN_SUBSTORE = "66505ff06510ee3d5903fd42"  # captured from a real browser session's cURL


def force_substore(route):
    """Our fresh session never gets a `substore` assigned, which seems to
    be why `data` came back empty while `paging.total` was still correct.
    This rewrites outgoing ms.products requests to include the known-good
    substore value — the site's own real storefront ID, not a per-user
    secret — before letting the request continue."""
    url = route.request.url
    if "ms.products" in url and "substore=" not in url:
        separator = "&" if "?" in url else "?"
        new_url = f"{url}{separator}substore={KNOWN_SUBSTORE}"
        route.continue_(url=new_url)
    else:
        route.continue_()


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            permissions=["geolocation"],
            geolocation=AHMEDABAD_COORDS,
            locale="en-IN",
        )
        context.route("**/api/1/entity/ms.products**", force_substore)
        page = context.new_page()
        page.on("response", handle_response)

        print("Loading page with geolocation granted (Ahmedabad)...")
        page.goto("https://shop.amul.com/en/brand/amul", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # Actively trigger the site's own location-resolution flow —
        # granting permission isn't enough; the site needs to actually
        # call navigator.geolocation itself, usually tied to a button click.
        clicked_location = False
        for label in ["Get my location", "Select Delivery Pincode", "Select Pincode"]:
            try:
                el = page.get_by_text(label, exact=False)
                if el.count() > 0:
                    el.first.click()
                    print(f"Clicked '{label}'")
                    clicked_location = True
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                continue
        if not clicked_location:
            print("Couldn't find a location-selection control to click.")

        try:
            page.wait_for_selector('a[href*="/en/product/"]', timeout=20000)
            print("Product links appeared in the DOM.")
        except Exception:
            print("Product links never appeared in the DOM within 20s.")

        page.wait_for_timeout(4000)  # catch any trailing/retry requests

        try:
            load_more = page.get_by_text("Load More", exact=False)
            if load_more.count() > 0:
                load_more.first.click()
                page.wait_for_timeout(3000)
        except Exception:
            pass

        browser.close()

    if not captured_responses:
        print("No ms.products response captured. Try re-running — Cloudflare sometimes needs "
              "a first 'warm-up' request. If it still fails, we may need headless=False.")
        return

    with open("api_response_sample.json", "w", encoding="utf-8") as f:
        json.dump(captured_responses, f, indent=2, ensure_ascii=False)

    # Find the response with the most items — that's almost certainly the real listing
    best = max(captured_responses, key=lambda r: len(r["data"].get("data", [])) if isinstance(r["data"], dict) else 0)
    data = best["data"]

    print(f"\n--- Best candidate (substore={_get_param(best['url'], 'substore')}): {best['url'][:150]}... ---")
    print("Top-level keys:", list(data.keys()) if isinstance(data, dict) else type(data))

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                print(f"\nKey '{key}' is a list with {len(value)} items.")
                if value:
                    print("First item sample:")
                    print(json.dumps(value[0], indent=2, ensure_ascii=False)[:2000])
            elif isinstance(value, dict):
                print(f"\nKey '{key}' is a dict:")
                print(json.dumps(value, indent=2, ensure_ascii=False)[:500])
            elif isinstance(value, (int, float, str, bool)):
                print(f"Key '{key}' = {value}")

    print(f"\nAll {len(captured_responses)} captured responses saved to api_response_sample.json")


if __name__ == "__main__":
    run()