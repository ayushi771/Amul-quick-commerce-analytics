-- 1. Total products
SELECT COUNT(*) AS total_products
FROM public.dim_product;


-- 2. Active products
SELECT COUNT(*) AS active_products
FROM public.dim_product
WHERE is_active = TRUE;


-- 3. Available vs unavailable
SELECT
    is_available,
    COUNT(*) AS product_count
FROM public.fact_catalogue_snapshot
GROUP BY is_available;


-- 4. Category-wise assortment
SELECT
    category,
    COUNT(*) AS product_count
FROM public.dim_product
WHERE is_active = TRUE
GROUP BY category
ORDER BY product_count DESC;


-- 5. Average MRP by category
SELECT
    category,
    ROUND(AVG(mrp), 2) AS avg_mrp
FROM public.dim_product
WHERE is_active = TRUE
  AND mrp IS NOT NULL
GROUP BY category
ORDER BY avg_mrp DESC;


-- 6. Products with highest MRP
SELECT
    product_name,
    category,
    mrp
FROM public.dim_product
WHERE is_active = TRUE
ORDER BY mrp DESC
LIMIT 10;


-- 7. Products with lowest MRP
SELECT
    product_name,
    category,
    mrp
FROM public.dim_product
WHERE is_active = TRUE
  AND mrp IS NOT NULL
ORDER BY mrp
LIMIT 10;


-- 8. New products
SELECT
    product_name,
    category,
    mrp
FROM public.dim_product
WHERE is_new = TRUE
ORDER BY product_name;


-- 9. Availability percentage
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN is_available THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS availability_percentage
FROM public.fact_catalogue_snapshot;


-- 10. Price per 100g
SELECT
    product_name,
    category,
    mrp,
    price_per_100g
FROM public.dim_product
WHERE price_per_100g IS NOT NULL
ORDER BY price_per_100g DESC;