"""
Loads Amul catalogue data from CSV into PostgreSQL.

Expects columns: product_name, category, subcategory, pack_qty_value,
pack_qty_unit, pack_multiplier, mrp, product_url, image_url, is_new,
snapshot_date, is_available

Run:
    python load_catalogue_from_csv.py manual_catalogue_full.csv
"""

import sys
import csv
import re
from datetime import date

from db import get_connection, upsert_product, insert_catalogue_snapshot, mark_missing_products_inactive

UNIT_TO_GRAMS = {"g": 1, "gm": 1, "gms": 1, "kg": 1000}
UNIT_TO_ML = {"ml": 1, "l": 1000, "ltr": 1000, "litre": 1000, "liter": 1000}


def slug_from_url(product_url: str) -> str:
    match = re.search(r"/en/product/([^/?#]+)", product_url)
    if match:
        return match.group(1)
    return re.sub(r"[^a-z0-9]+", "-", product_url.lower()).strip("-")


def parse_bool(value: str) -> bool:
    return str(value).strip().upper() in ("TRUE", "1", "YES", "Y")


def compute_normalized_fields(qty_value: float, qty_unit: str, multiplier: int, mrp: float) -> dict:
    result = {
        "normalized_qty_value": None,
        "normalized_qty_unit": None,
        "price_per_100g": None,
        "price_per_100ml": None,
        "price_per_unit": None,
    }
    unit_lower = (qty_unit or "").strip().lower()

    if unit_lower in UNIT_TO_GRAMS:
        total_grams = qty_value * UNIT_TO_GRAMS[unit_lower] * multiplier
        result["normalized_qty_value"] = total_grams
        result["normalized_qty_unit"] = "g"
        if mrp and total_grams:
            result["price_per_100g"] = round(mrp / total_grams * 100, 2)
    elif unit_lower in UNIT_TO_ML:
        total_ml = qty_value * UNIT_TO_ML[unit_lower] * multiplier
        result["normalized_qty_value"] = total_ml
        result["normalized_qty_unit"] = "ml"
        if mrp and total_ml:
            result["price_per_100ml"] = round(mrp / total_ml * 100, 2)
    else:
        result["normalized_qty_value"] = multiplier
        result["normalized_qty_unit"] = "unit"
        if mrp and multiplier:
            result["price_per_unit"] = round(mrp / multiplier, 2)

    return result


def load_csv(csv_path: str):
    seen_slugs = []
    loaded, skipped = 0, 0

    with get_connection() as conn:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                product_name = row["product_name"].strip()
                product_url = row.get("product_url", "").strip()
                if not product_name:
                    print(f"SKIP: missing product_name in row: {row}")
                    skipped += 1
                    continue
                if not product_url:
                    print(f"WARNING: '{product_name}' has no product_url — loading anyway, "
                          f"but this breaks source traceability.")

                mrp = float(row["mrp"]) if row.get("mrp", "").strip() else None
                qty_value = float(row["pack_qty_value"]) if row.get("pack_qty_value", "").strip() else None
                qty_unit = row.get("pack_qty_unit", "").strip()
                multiplier = int(row["pack_multiplier"]) if row.get("pack_multiplier", "").strip() else 1

                normalized = compute_normalized_fields(qty_value or 0, qty_unit, multiplier, mrp) \
                    if qty_value else {k: None for k in
                                        ("normalized_qty_value", "normalized_qty_unit",
                                         "price_per_100g", "price_per_100ml", "price_per_unit")}

                slug = slug_from_url(product_url) if product_url else re.sub(
                    r"[^a-z0-9]+", "-", product_name.lower()).strip("-")

                is_new = parse_bool(row.get("is_new", "FALSE"))
                is_available = parse_bool(row.get("is_available", "TRUE"))

                product_row = {
                    "product_slug": slug,
                    "product_name": product_name,
                    "category": row.get("category", "").strip() or None,
                    "subcategory": row.get("subcategory", "").strip() or None,
                    "pack_qty_value": qty_value,
                    "pack_qty_unit": qty_unit or None,
                    "pack_multiplier": multiplier,
                    "mrp": mrp,
                    "is_new": is_new,
                    "product_url": product_url or None,
                    "image_url": row.get("image_url", "").strip() or None,
                    **normalized,
                }

                product_id = upsert_product(conn, product_row)
                seen_slugs.append(slug)

                insert_catalogue_snapshot(conn, product_id, {
                    "is_available": is_available,
                    "mrp": mrp,
                    "is_new": is_new,
                    "source_url": product_url or None,
                })
                loaded += 1

        deactivated = mark_missing_products_inactive(conn, seen_slugs)

    print(f"Loaded {loaded} product(s), skipped {skipped}.")
    if deactivated:
        print(f"Marked {deactivated} previously-seen product(s) as inactive.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "manual_catalogue_full.csv"
    load_csv(path)