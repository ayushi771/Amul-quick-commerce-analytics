"""
Product-matching layer.

Platforms rarely use Amul's exact product name (e.g. Amul's
"Amul Milk Shake Premix Strawberry, 500 g" might appear on a platform
as "Amul Strawberry Milkshake Premix 500g"). This script fuzzy-matches
an observation CSV's `platform_product_name` column against every
active product_name in dim_product, and writes the best match into
product_platform_mapping with a confidence score.

Matches with confidence below CONFIDENCE_REVIEW_THRESHOLD are written
anyway but flagged for manual review (match_method='fuzzy_low') —
never silently trust a low-confidence match in fact_platform_observation
numbers without a human checking it at least once per product.

Run:
    python -m pipeline.match_products
"""

import sys
import csv
from pathlib import Path
from rapidfuzz import process, fuzz

from pipeline.db import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = PROJECT_ROOT / "data" / "observations" / "manual_observation_template.csv"

CONFIDENCE_REVIEW_THRESHOLD = 0.85  # below this, flag for manual review


def load_active_products(conn):
    """Returns {product_id: product_name} for every active product."""
    with conn.cursor() as cur:
        cur.execute("SELECT product_id, product_name FROM dim_product WHERE is_active = TRUE;")
        return {row[0]: row[1] for row in cur.fetchall()}


def get_platform_id(conn, platform_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT platform_id FROM dim_platform WHERE platform_name = %s;", (platform_name,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Unknown platform '{platform_name}' — add it to dim_platform first.")
        return row[0]


def upsert_mapping(conn, product_id, platform_id, platform_name_text, platform_url, method, confidence):
    sql = """
        INSERT INTO product_platform_mapping (
            product_id, platform_id, platform_product_name, platform_product_url,
            match_method, confidence
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id, platform_id) DO UPDATE SET
            platform_product_name = EXCLUDED.platform_product_name,
            platform_product_url = EXCLUDED.platform_product_url,
            match_method = EXCLUDED.match_method,
            confidence = EXCLUDED.confidence;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (product_id, platform_id, platform_name_text, platform_url, method, confidence))


def match_csv(csv_path: str):
    with get_connection() as conn:
        products = load_active_products(conn)  # {product_id: name}
        choices = {name: pid for pid, name in products.items()}  # name -> product_id for rapidfuzz

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                platform_name = row["platform_name"].strip()
                platform_product_name = row["platform_product_name"].strip()
                platform_url = row.get("platform_product_url", "").strip()

                if not platform_product_name:
                    continue

                best = process.extractOne(
                    platform_product_name, choices.keys(), scorer=fuzz.token_sort_ratio
                )
                if not best:
                    print(f"NO MATCH: '{platform_product_name}' on {platform_name}")
                    continue

                matched_name, score, _ = best
                confidence = round(score / 100.0, 3)
                product_id = choices[matched_name]
                platform_id = get_platform_id(conn, platform_name)

                method = "fuzzy" if confidence >= CONFIDENCE_REVIEW_THRESHOLD else "fuzzy_low"
                upsert_mapping(conn, product_id, platform_id, platform_product_name, platform_url, method, confidence)

                flag = "" if confidence >= CONFIDENCE_REVIEW_THRESHOLD else "  <-- REVIEW MANUALLY"
                print(f"[{platform_name}] '{platform_product_name}' -> '{matched_name}' "
                      f"(confidence {confidence}){flag}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    match_csv(path)
