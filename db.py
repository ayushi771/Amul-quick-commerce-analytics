"""
PostgreSQL connection helper + upsert utilities for the
Amul Digital Shelf Intelligence project.

Handles:
- Products
- Catalogue snapshots
- Categories
- Platforms
- Locations
- Live platform observations

Uses psycopg2 directly (no ORM).
"""

import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from config import DB_CONFIG


# ============================================================
# DATABASE CONNECTION
# ============================================================

@contextmanager
def get_connection():
    """
    Yields a psycopg2 connection.

    Commits on success and rolls back on error.
    """
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# PRODUCT
# ============================================================

def upsert_product(conn, product: dict) -> int:
    """
    Insert a new product or update an existing product.

    Returns:
        product_id
    """

    sql = """
        INSERT INTO public.dim_product (
            product_slug,
            product_name,
            category,
            subcategory,
            pack_qty_value,
            pack_qty_unit,
            pack_multiplier,
            mrp,
            normalized_qty_value,
            normalized_qty_unit,
            price_per_100g,
            price_per_100ml,
            price_per_unit,
            is_new,
            product_url,
            image_url,
            first_seen_date,
            last_seen_date,
            is_active
        )
        VALUES (
            %(product_slug)s,
            %(product_name)s,
            %(category)s,
            %(subcategory)s,
            %(pack_qty_value)s,
            %(pack_qty_unit)s,
            %(pack_multiplier)s,
            %(mrp)s,
            %(normalized_qty_value)s,
            %(normalized_qty_unit)s,
            %(price_per_100g)s,
            %(price_per_100ml)s,
            %(price_per_unit)s,
            %(is_new)s,
            %(product_url)s,
            %(image_url)s,
            CURRENT_DATE,
            CURRENT_DATE,
            TRUE
        )

        ON CONFLICT (product_slug)
        DO UPDATE SET
            product_name = EXCLUDED.product_name,
            category = EXCLUDED.category,
            subcategory = EXCLUDED.subcategory,
            pack_qty_value = EXCLUDED.pack_qty_value,
            pack_qty_unit = EXCLUDED.pack_qty_unit,
            pack_multiplier = EXCLUDED.pack_multiplier,
            mrp = EXCLUDED.mrp,
            normalized_qty_value = EXCLUDED.normalized_qty_value,
            normalized_qty_unit = EXCLUDED.normalized_qty_unit,
            price_per_100g = EXCLUDED.price_per_100g,
            price_per_100ml = EXCLUDED.price_per_100ml,
            price_per_unit = EXCLUDED.price_per_unit,
            is_new = EXCLUDED.is_new,
            product_url = EXCLUDED.product_url,
            image_url = EXCLUDED.image_url,
            last_seen_date = CURRENT_DATE,
            is_active = TRUE

        RETURNING product_id;
    """

    with conn.cursor() as cur:
        cur.execute(sql, product)
        return cur.fetchone()[0]


# ============================================================
# CATALOGUE SNAPSHOT
# ============================================================

def insert_catalogue_snapshot(
    conn,
    product_id: int,
    snapshot: dict
) -> None:
    """
    Insert/update the daily catalogue snapshot for a product.
    """

    sql = """
        INSERT INTO public.fact_catalogue_snapshot (
            product_id,
            snapshot_date,
            is_available,
            mrp,
            is_new,
            source_url,
            collection_timestamp
        )
        VALUES (
            %(product_id)s,
            CURRENT_DATE,
            %(is_available)s,
            %(mrp)s,
            %(is_new)s,
            %(source_url)s,
            NOW()
        )

        ON CONFLICT (product_id, snapshot_date)
        DO UPDATE SET
            is_available = EXCLUDED.is_available,
            mrp = EXCLUDED.mrp,
            is_new = EXCLUDED.is_new,
            source_url = EXCLUDED.source_url,
            collection_timestamp = NOW();
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "product_id": product_id,
                **snapshot
            }
        )


# ============================================================
# MARK MISSING PRODUCTS
# ============================================================

def mark_missing_products_inactive(
    conn,
    seen_slugs: list
) -> int:
    """
    Mark products that were not found in the latest catalogue
    as inactive.

    Returns:
        Number of products marked inactive.
    """

    sql = """
        UPDATE public.dim_product
        SET is_active = FALSE
        WHERE is_active = TRUE
          AND product_slug != ALL(%(seen_slugs)s);
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            {"seen_slugs": seen_slugs}
        )

        return cur.rowcount


# ============================================================
# CATEGORY
# ============================================================

def get_or_create_category(
    conn,
    category_name: str,
    parent_group: str = None
) -> int:
    """
    Insert a category if it does not exist.

    Returns:
        category_id
    """

    sql = """
        INSERT INTO public.dim_category (
            category_name,
            parent_group
        )
        VALUES (
            %(category_name)s,
            %(parent_group)s
        )

        ON CONFLICT (category_name)
        DO UPDATE SET
            category_name = EXCLUDED.category_name

        RETURNING category_id;
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "category_name": category_name,
                "parent_group": parent_group
            }
        )

        return cur.fetchone()[0]


# ============================================================
# PLATFORM
# ============================================================

def get_or_create_platform(
    conn,
    platform_name: str,
    platform_type: str = None
) -> int:
    """
    Insert a platform if it does not exist.

    Returns:
        platform_id
    """

    sql = """
        INSERT INTO public.dim_platform (
            platform_name,
            platform_type
        )
        VALUES (
            %(platform_name)s,
            %(platform_type)s
        )

        ON CONFLICT (platform_name)
        DO UPDATE SET
            platform_type = COALESCE(
                EXCLUDED.platform_type,
                public.dim_platform.platform_type
            )

        RETURNING platform_id;
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "platform_name": platform_name,
                "platform_type": platform_type
            }
        )

        return cur.fetchone()[0]


# ============================================================
# LOCATION
# ============================================================

def get_or_create_location(
    conn,
    city: str,
    state: str,
    pincode: str,
    latitude: float = None,
    longitude: float = None
) -> int:
    """
    Insert a location if it does not exist.

    Returns:
        location_id
    """

    sql = """
        INSERT INTO public.dim_location (
            city,
            state,
            pincode,
            latitude,
            longitude
        )
        VALUES (
            %(city)s,
            %(state)s,
            %(pincode)s,
            %(latitude)s,
            %(longitude)s
        )

        ON CONFLICT (city, state, pincode)
        DO UPDATE SET
            latitude = COALESCE(
                EXCLUDED.latitude,
                public.dim_location.latitude
            ),
            longitude = COALESCE(
                EXCLUDED.longitude,
                public.dim_location.longitude
            ),
            is_active = TRUE

        RETURNING location_id;
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "city": city,
                "state": state,
                "pincode": pincode,
                "latitude": latitude,
                "longitude": longitude
            }
        )

        return cur.fetchone()[0]


# ============================================================
# LIVE PLATFORM OBSERVATION
# ============================================================

def insert_platform_observation(
    conn,
    observation: dict
) -> int:
    """
    Insert one live platform observation.

    Each execution creates a new timestamped observation,
    allowing us to maintain historical price/availability data.

    Required observation fields:

        product_id
        platform_id
        location_id
        is_listed

    Optional fields:

        listed_price
        mrp
        discount_pct
        stock_status
        delivery_eta_minutes
        source_url

    Returns:
        observation_id
    """

    sql = """
        INSERT INTO public.fact_platform_observation (
            product_id,
            platform_id,
            location_id,
            collected_date,
            is_listed,
            listed_price,
            mrp,
            discount_pct,
            stock_status,
            delivery_eta_minutes,
            source_url,
            collection_timestamp
        )
        VALUES (
            %(product_id)s,
            %(platform_id)s,
            %(location_id)s,
            CURRENT_DATE,
            %(is_listed)s,
            %(listed_price)s,
            %(mrp)s,
            %(discount_pct)s,
            %(stock_status)s,
            %(delivery_eta_minutes)s,
            %(source_url)s,
            NOW()
        )

        RETURNING observation_id;
    """

    with conn.cursor() as cur:
        cur.execute(sql, observation)

        return cur.fetchone()[0]