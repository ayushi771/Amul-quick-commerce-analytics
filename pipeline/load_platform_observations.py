
"""
Loads quick-commerce observations (from data/observations/manual_observation_template.csv,
or from a platform-specific scraper's output in the same column format)
into fact_platform_observation, resolving each row to a product_id via
product_platform_mapping (so run match_products.py on this CSV FIRST).

Run:
    python -m pipeline.match_products
    python -m pipeline.load_platform_observations
"""

import sys
import csv
from datetime import date
import re
from pathlib import Path

from pipeline.db import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = PROJECT_ROOT / "data" / "observations" / "manual_observation_template.csv"


def get_location_id(conn, location_name: str):
    if not location_name or not location_name.strip():
        raise ValueError("location_name is missing in CSV")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT location_id
            FROM dim_location
            WHERE LOWER(TRIM(city)) = LOWER(TRIM(%s))
              AND is_active = TRUE
            LIMIT 1;
            """,
            (location_name.strip(),),
        )

        row = cur.fetchone()

        if not row:
            raise ValueError(
                f"Location '{location_name}' not found in dim_location"
            )

        return row[0]

def get_mapped_product_id(
    conn,
    platform_id: int,
    platform_product_name: str
):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT product_id
            FROM product_platform_mapping
            WHERE platform_id = %s
              AND platform_product_name = %s;
            """,
            (
                platform_id,
                platform_product_name
            ),
        )

        row = cur.fetchone()

        return row[0] if row else None


def get_platform_id(conn, platform_name: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT platform_id
            FROM dim_platform
            WHERE platform_name = %s;
            """,
            (platform_name,),
        )

        row = cur.fetchone()

        return row[0] if row else None


def get_mrp(conn, product_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT mrp
            FROM dim_product
            WHERE product_id = %s;
            """,
            (product_id,),
        )

        row = cur.fetchone()

        return (
            float(row[0])
            if row and row[0] is not None
            else None
        )


def ensure_date_exists(conn, the_date: date):
    """fact_platform_observation FKs to dim_date — make sure the row exists."""

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dim_date
                (
                    date_key,
                    year,
                    month,
                    month_name,
                    quarter,
                    week_of_year,
                    day_of_week,
                    is_weekend
                )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date_key)
            DO NOTHING;
            """,
            (
                the_date,
                the_date.year,
                the_date.month,
                the_date.strftime("%B"),
                (the_date.month - 1) // 3 + 1,
                the_date.isocalendar()[1],
                the_date.isoweekday(),
                the_date.isoweekday() in (6, 7),
            ),
        )


def upsert_observation(
    conn,
    product_id,
    platform_id,
    location_id,
    collected_date,
    is_listed,
    listed_price,
    discount_pct,
    stock_status,
    source_url,
    delivery_eta_minutes,
):
    """
    Insert or update one platform/location observation.

    Uniqueness is now:
        product_id + platform_id + location_id + collected_date

    This allows the same product/platform to have separate
    observations for Ahmedabad, Mumbai, Delhi, Bengaluru, etc.
    """

    sql = """
        INSERT INTO fact_platform_observation (
            product_id,
            platform_id,
            location_id,
            collected_date,
            is_listed,
            listed_price,
            discount_pct,
            stock_status,
            source_url,
            delivery_eta_minutes,
            collection_timestamp
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW()
        )

        ON CONFLICT (
            product_id,
            platform_id,
            location_id,
            collected_date
        )
        DO UPDATE SET
            is_listed = EXCLUDED.is_listed,
            listed_price = EXCLUDED.listed_price,
            discount_pct = EXCLUDED.discount_pct,
            stock_status = EXCLUDED.stock_status,
            source_url = EXCLUDED.source_url,
            delivery_eta_minutes = EXCLUDED.delivery_eta_minutes,
            collection_timestamp = NOW();
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                product_id,
                platform_id,
                location_id,
                collected_date,
                is_listed,
                listed_price,
                discount_pct,
                stock_status,
                source_url,
                delivery_eta_minutes,
            ),
        )


def load_csv(csv_path: str):
    loaded, skipped = 0, 0

    with get_connection() as conn:

        with open(
            csv_path,
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            # Check required columns
            required_columns = [
                "platform_name",
                "platform_product_name",
                "listed_price",
                "stock_status",
                "collected_date",
                "location_name",
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in reader.fieldnames
            ]

            if missing_columns:
                raise ValueError(
                    "CSV is missing required column(s): "
                    + ", ".join(missing_columns)
                )

            for row in reader:

                # --------------------------------------------------
                # Basic CSV values
                # --------------------------------------------------

                platform_name = row[
                    "platform_name"
                ].strip()

                platform_product_name = row[
                    "platform_product_name"
                ].strip()

                location_name = row[
                    "location_name"
                ].strip()

                platform_url = row.get(
                    "platform_product_url",
                    ""
                ).strip()

                stock_status = row.get(
                    "stock_status",
                    ""
                ).strip()

                collected_date = date.fromisoformat(
                    row["collected_date"].strip()
                )

                # --------------------------------------------------
                # Location
                # --------------------------------------------------

                try:
                    location_id = get_location_id(
                        conn,
                        location_name
                    )

                except ValueError as e:
                    print(
                        f"SKIP: {e}"
                    )
                    skipped += 1
                    continue

                # --------------------------------------------------
                # Listed price
                # --------------------------------------------------

                price_raw = row.get(
                    "listed_price",
                    ""
                ).strip()

                listed_price = (
                    float(price_raw)
                    if price_raw
                    else None
                )

                # --------------------------------------------------
                # Delivery ETA
                # --------------------------------------------------

                eta_raw = row.get(
                    "delivery_eta_minutes",
                    ""
                ).strip()

                delivery_eta_minutes = (
                    int(eta_raw)
                    if eta_raw
                    else None
                )

                # --------------------------------------------------
                # Find platform
                # --------------------------------------------------

                platform_id = get_platform_id(
                    conn,
                    platform_name
                )

                if not platform_id:
                    print(
                        f"SKIP: unknown platform "
                        f"'{platform_name}'"
                    )

                    skipped += 1
                    continue

                # --------------------------------------------------
                # Find product mapping
                # --------------------------------------------------

                product_id = get_mapped_product_id(
                    conn,
                    platform_id,
                    platform_product_name
                )

                if not product_id:
                    print(
                        f"SKIP: no mapping for "
                        f"'{platform_product_name}' "
                        f"on {platform_name} "
                        f"— run match_products.py "
                        f"on this file first."
                    )

                    skipped += 1
                    continue

                # --------------------------------------------------
                # Determine listing status
                # --------------------------------------------------

                is_listed = (
                    stock_status.lower() != "not listed"
                    and listed_price is not None
                )

                # --------------------------------------------------
                # Get MRP
                # --------------------------------------------------

                mrp = get_mrp(
                    conn,
                    product_id
                )

                # --------------------------------------------------
                # Calculate discount
                # --------------------------------------------------

                discount_pct = (
                    round(
                        (mrp - listed_price)
                        / mrp
                        * 100,
                        2
                    )
                    if (
                        mrp
                        and listed_price
                    )
                    else None
                )

                # --------------------------------------------------
                # Make sure date exists
                # --------------------------------------------------

                ensure_date_exists(
                    conn,
                    collected_date
                )

                # --------------------------------------------------
                # Insert / update observation
                # --------------------------------------------------

                upsert_observation(
                    conn,
                    product_id,
                    platform_id,
                    location_id,
                    collected_date,
                    is_listed,
                    listed_price,
                    discount_pct,
                    stock_status
                    or (
                        "In Stock"
                        if is_listed
                        else "Not Listed"
                    ),
                    platform_url,
                    delivery_eta_minutes,
                )

                loaded += 1

        # Commit all loaded observations
        conn.commit()

    print(
        f"Loaded {loaded} observation(s), "
        f"skipped {skipped}."
    )


if __name__ == "__main__":

    path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_CSV
    )

    load_csv(path)
