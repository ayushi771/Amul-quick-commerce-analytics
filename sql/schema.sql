CREATE TABLE IF NOT EXISTS dim_category (
    category_id     SERIAL PRIMARY KEY,
    category_name   TEXT NOT NULL UNIQUE,
    parent_group    TEXT                 -- e.g. Dairy, Beverages
);

CREATE TABLE IF NOT EXISTS dim_platform (
    platform_id     SERIAL PRIMARY KEY,
    platform_name   TEXT NOT NULL UNIQUE,   -- Blinkit, Zepto, Instamart, BigBasket
    platform_type   TEXT                    -- Quick-commerce / E-grocery
);
CREATE TABLE IF NOT EXISTS dim_date (
    date_key        DATE PRIMARY KEY,
    year            INT NOT NULL,
    month           INT NOT NULL,
    month_name      TEXT NOT NULL,
    quarter         INT NOT NULL,
    week_of_year    INT NOT NULL,
    day_of_week     INT NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id            SERIAL PRIMARY KEY,
    product_slug          TEXT NOT NULL UNIQUE,     -- natural key, from the Amul product URL
    product_name          TEXT NOT NULL,
    category              TEXT,
    subcategory           TEXT,
    pack_qty_value         NUMERIC,
    pack_qty_unit          TEXT,                     -- g / ml / kg / L / sachet
    pack_multiplier        INT DEFAULT 1,            -- e.g. 8 for "180 ml x 8"
    mrp                    NUMERIC,
    normalized_qty_value   NUMERIC,                  -- pack_qty_value * pack_multiplier, base unit
    normalized_qty_unit    TEXT,                     -- g / ml / unit
    price_per_100g         NUMERIC,
    price_per_100ml        NUMERIC,
    price_per_unit         NUMERIC,
    is_new                 BOOLEAN DEFAULT FALSE,
    product_url            TEXT,
    image_url              TEXT,
    first_seen_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    last_seen_date         DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active              BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_dim_product_category ON dim_product (category);
CREATE INDEX IF NOT EXISTS idx_dim_product_active ON dim_product (is_active);

-- ---------- FACTS ----------

-- One row per product per scrape run: the dated "photo" of the whole catalogue
CREATE TABLE IF NOT EXISTS fact_catalogue_snapshot (
    snapshot_id           BIGSERIAL PRIMARY KEY,
    product_id            INT NOT NULL REFERENCES dim_product (product_id),
    snapshot_date          DATE NOT NULL REFERENCES dim_date (date_key),
    is_available           BOOLEAN NOT NULL,
    mrp                    NUMERIC,
    is_new                 BOOLEAN,
    source_url             TEXT,
    collection_timestamp   TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_snapshot_date ON fact_catalogue_snapshot (snapshot_date);

-- One row per product x platform x collection date
CREATE TABLE IF NOT EXISTS fact_platform_observation (
    observation_id         BIGSERIAL PRIMARY KEY,
    product_id             INT NOT NULL REFERENCES dim_product (product_id),
    platform_id            INT NOT NULL REFERENCES dim_platform (platform_id),
    collected_date          DATE NOT NULL REFERENCES dim_date (date_key),
    is_listed               BOOLEAN NOT NULL,
    listed_price            NUMERIC,
    discount_pct            NUMERIC,              -- computed: (mrp - listed_price) / mrp
    stock_status            TEXT,                 -- In Stock / Out of Stock / Not Listed
    source_url              TEXT,
    collection_timestamp    TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, platform_id, collected_date)
);

CREATE INDEX IF NOT EXISTS idx_obs_platform_date ON fact_platform_observation (platform_id, collected_date);

-- ---------- MAPPING ----------

CREATE TABLE IF NOT EXISTS product_platform_mapping (
    mapping_id              SERIAL PRIMARY KEY,
    product_id              INT NOT NULL REFERENCES dim_product (product_id),
    platform_id             INT NOT NULL REFERENCES dim_platform (platform_id),
    platform_product_name   TEXT NOT NULL,
    platform_product_url    TEXT,
    match_method            TEXT,                 -- exact / fuzzy / manual
    confidence              NUMERIC(4,3),          -- 0.000 - 1.000
    UNIQUE (product_id, platform_id)
);

-- ---------- SEED DATA ----------

INSERT INTO dim_platform (platform_name, platform_type) VALUES
    ('Blinkit', 'Quick-commerce'),
    ('Zepto', 'Quick-commerce'),
    ('Instamart', 'Quick-commerce'),
    ('BigBasket', 'E-grocery')
ON CONFLICT (platform_name) DO NOTHING;

-- Populate dim_date for the next few years (run once; extend the range as needed)
INSERT INTO dim_date (date_key, year, month, month_name, quarter, week_of_year, day_of_week, is_weekend)
SELECT
    d::date,
    EXTRACT(YEAR FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    TO_CHAR(d, 'Month'),
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(WEEK FROM d)::INT,
    EXTRACT(ISODOW FROM d)::INT,
    EXTRACT(ISODOW FROM d) IN (6, 7)
FROM generate_series('2025-01-01'::date, '2027-12-31'::date, interval '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;

