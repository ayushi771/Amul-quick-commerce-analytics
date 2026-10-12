BEGIN;

-- ============================================================
-- 1. LOCATION DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS public.dim_location (
    location_id       SERIAL PRIMARY KEY,
    city               TEXT NOT NULL,
    state              TEXT NOT NULL,
    pincode             TEXT NOT NULL,
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (city, state, pincode)
);

CREATE INDEX IF NOT EXISTS idx_dim_location_city
ON public.dim_location (city);

CREATE INDEX IF NOT EXISTS idx_dim_location_pincode
ON public.dim_location (pincode);


-- ============================================================
-- 2. ADD LOCATION + LIVE FIELDS
-- ============================================================

ALTER TABLE public.fact_platform_observation
ADD COLUMN IF NOT EXISTS location_id INT
REFERENCES public.dim_location(location_id);

ALTER TABLE public.fact_platform_observation
ADD COLUMN IF NOT EXISTS mrp NUMERIC;

ALTER TABLE public.fact_platform_observation
ADD COLUMN IF NOT EXISTS delivery_eta_minutes INT;


-- ============================================================
-- 3. REMOVE OLD DAILY UNIQUENESS
-- ============================================================

ALTER TABLE public.fact_platform_observation
DROP CONSTRAINT IF EXISTS
fact_platform_observation_product_id_platform_id_collected_date_key;


-- ============================================================
-- 4. INDEXES FOR LOCATION + LIVE QUERIES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_obs_platform_location
ON public.fact_platform_observation (
    platform_id,
    location_id,
    collected_date
);

CREATE INDEX IF NOT EXISTS idx_obs_product_location
ON public.fact_platform_observation (
    product_id,
    location_id
);

CREATE INDEX IF NOT EXISTS idx_obs_timestamp
ON public.fact_platform_observation (
    collection_timestamp
);


-- ============================================================
-- 5. SEED LOCATIONS
-- ============================================================

INSERT INTO public.dim_location
    (city, state, pincode, latitude, longitude)
VALUES
    ('Ahmedabad', 'Gujarat', '380001', 23.0225, 72.5714),
    ('Ahmedabad', 'Gujarat', '380015', 23.0216, 72.5277),
    ('Ahmedabad', 'Gujarat', '380054', 23.0395, 72.5060)
ON CONFLICT (city, state, pincode)
DO NOTHING;

COMMIT;