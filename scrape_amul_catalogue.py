import time
import re
import sys
from datetime import date
import requests
from bs4 import BeautifulSoup
from config import AMUL_BRAND_URL, REQUEST_HEADERS, REQUEST_DELAY_SECONDS
from pack_parser import parse_pack_info
from db import get_connection, upsert_product, insert_catalogue_snapshot, mark_missing_products_inactive
PAGE_SIZE = 15         
PAGE_PARAM = "start"   
MAX_PAGES = 30    

def fetch_page(start_offset: int) -> BeautifulSoup:
    params = {PAGE_PARAM: start_offset} if start_offset else {}
    resp = requests.get(AMUL_BRAND_URL, headers=REQUEST_HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def extract_total_count(soup: BeautifulSoup) -> int:
    """Parses the 'Showing 15 of 160 products' text into the total count."""
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Showing\s+\d+\s+of\s+(\d+)\s+products", text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def parse_products(soup: BeautifulSoup) -> list:
    """
    Parses one listing page into a list of raw product dicts.
    NOTE: the exact CSS selectors below reflect the site's HTML
    structure at the time this was written. Inspect the live page
    (view-source or browser dev tools) and adjust selectors if the
    site's markup changes.
    """
    products = []

    # Product links follow the pattern /en/product/<slug>
    product_links = soup.select('a[href*="/en/product/"]')

    seen_slugs_on_page = set()
    for link in product_links:
        href = link.get("href", "")
        slug_match = re.search(r"/en/product/([^/?#]+)", href)
        if not slug_match:
            continue
        slug = slug_match.group(1)
        if slug in seen_slugs_on_page:
            continue  # the product name+image+title usually all link to the same product
        seen_slugs_on_page.add(slug)

        # Walk up to the product "card" container to find name/price/new-badge together
        card = link.find_parent(["div", "li", "article"]) or link.parent
        card_text = card.get_text(" ", strip=True) if card else link.get_text(" ", strip=True)

        name = link.get("title") or link.get_text(strip=True)
        if not name:
            continue

        mrp_match = re.search(r"MRP[₹Rs.\s]*([\d,]+(?:\.\d+)?)", card_text)
        mrp = float(mrp_match.group(1).replace(",", "")) if mrp_match else None

        is_new = bool(re.search(r"\bNew\b", card_text))
        is_sold_out = bool(re.search(r"Sold Out", card_text, re.IGNORECASE))

        img_tag = link.find("img") if link.find("img") else (card.find("img") if card else None)
        image_url = img_tag.get("src") if img_tag else None

        products.append({
            "product_slug": slug,
            "product_name": name,
            "product_url": href if href.startswith("http") else f"https://shop.amul.com{href}",
            "image_url": image_url,
            "mrp": mrp,
            "is_new": is_new,
            "is_available": not is_sold_out,
        })

    return products


def run_scrape():
    print(f"[{date.today()}] Starting Amul catalogue scrape...")

    all_products = []
    first_page_soup = fetch_page(0)
    total_count = extract_total_count(first_page_soup)
    print(f"Catalogue reports {total_count} total products (read dynamically, not hard-coded).")

    all_products.extend(parse_products(first_page_soup))

    offset = PAGE_SIZE
    page_num = 1
    while len(all_products) < total_count and page_num < MAX_PAGES:
        time.sleep(REQUEST_DELAY_SECONDS)
        soup = fetch_page(offset)
        page_products = parse_products(soup)
        if not page_products:
            break  # no more pages returned
        all_products.extend(page_products)
        offset += PAGE_SIZE
        page_num += 1

    # de-duplicate by slug in case of overlapping pages
    deduped = {p["product_slug"]: p for p in all_products}.values()
    print(f"Parsed {len(deduped)} unique products across {page_num} page(s).")

    if not deduped:
        print("No products parsed — check selectors in parse_products() against the live site.")
        sys.exit(1)

    seen_slugs = []
    with get_connection() as conn:
        for raw in deduped:
            pack_info = parse_pack_info(raw["product_name"], raw["mrp"])

            product_row = {
                "product_slug": raw["product_slug"],
                "product_name": raw["product_name"],
                "category": None,       # category comes from which /en/browse/<cat> page you scrape;
                "subcategory": None,    # extend run_scrape() to loop over category pages if you need this
                "mrp": raw["mrp"],
                "is_new": raw["is_new"],
                "product_url": raw["product_url"],
                "image_url": raw["image_url"],
                **pack_info,
            }

            product_id = upsert_product(conn, product_row)
            seen_slugs.append(raw["product_slug"])

            insert_catalogue_snapshot(conn, product_id, {
                "is_available": raw["is_available"],
                "mrp": raw["mrp"],
                "is_new": raw["is_new"],
                "source_url": raw["product_url"],
            })

        deactivated = mark_missing_products_inactive(conn, seen_slugs)
        if deactivated:
            print(f"Marked {deactivated} previously-seen product(s) as inactive (not found in this run).")

    print(f"[{date.today()}] Scrape complete. {len(seen_slugs)} products upserted + snapshotted.")


if __name__ == "__main__":
    run_scrape()
