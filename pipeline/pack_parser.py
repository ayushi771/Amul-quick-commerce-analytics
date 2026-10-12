import re
from typing import Optional, Dict, Any

UNIT_TO_GRAMS = {"g": 1, "gm": 1, "gms": 1, "kg": 1000}
UNIT_TO_ML = {"ml": 1, "l": 1000, "ltr": 1000, "litre": 1000, "liter": 1000}

QTY_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(kg|gm?s?|ml|l|ltr|litre|liter)\b", re.IGNORECASE
)
PACK_OF_RE = re.compile(r"pack of\s*(\d+)", re.IGNORECASE)
X_MULTIPLIER_RE = re.compile(r"x\s*(\d+)\b", re.IGNORECASE)
SACHET_RE = re.compile(r"(\d+)\s*sachets?", re.IGNORECASE)


def parse_pack_info(product_title: str, mrp: Optional[float]) -> Dict[str, Any]:
    """
    Returns a dict ready to merge into the `dim_product` row:
        pack_qty_value, pack_qty_unit, pack_multiplier,
        normalized_qty_value, normalized_qty_unit,
        price_per_100g, price_per_100ml, price_per_unit
    Any field that doesn't apply to this product stays None.
    """
    result: Dict[str, Any] = {
        "pack_qty_value": None,
        "pack_qty_unit": None,
        "pack_multiplier": 1,
        "normalized_qty_value": None,
        "normalized_qty_unit": None,
        "price_per_100g": None,
        "price_per_100ml": None,
        "price_per_unit": None,
    }

    qty_match = QTY_UNIT_RE.search(product_title)
    if not qty_match:
        return result  # couldn't parse — leave for manual review

    qty_value = float(qty_match.group(1))
    raw_unit = qty_match.group(2).lower()

    # multiplier: prefer explicit sachet count, then "Pack of N", then "x N"
    multiplier = 1
    sachet_match = SACHET_RE.search(product_title)
    pack_of_match = PACK_OF_RE.search(product_title)
    x_match = X_MULTIPLIER_RE.search(product_title)
    if sachet_match:
        multiplier = int(sachet_match.group(1))
    elif pack_of_match:
        multiplier = int(pack_of_match.group(1))
    elif x_match:
        multiplier = int(x_match.group(1))

    result["pack_qty_value"] = qty_value
    result["pack_qty_unit"] = raw_unit
    result["pack_multiplier"] = multiplier

    is_sachet_product = bool(sachet_match)

    if raw_unit in UNIT_TO_GRAMS and not is_sachet_product:
        grams_each = qty_value * UNIT_TO_GRAMS[raw_unit]
        total_grams = grams_each * multiplier
        result["normalized_qty_value"] = total_grams
        result["normalized_qty_unit"] = "g"
        if mrp and total_grams:
            result["price_per_100g"] = round(float(mrp) / total_grams * 100, 2)

    elif raw_unit in UNIT_TO_ML and not is_sachet_product:
        ml_each = qty_value * UNIT_TO_ML[raw_unit]
        total_ml = ml_each * multiplier
        result["normalized_qty_value"] = total_ml
        result["normalized_qty_unit"] = "ml"
        if mrp and total_ml:
            result["price_per_100ml"] = round(float(mrp) / total_ml * 100, 2)

    else:
        # sachet / piece-based product: price per individual unit
        result["normalized_qty_value"] = multiplier
        result["normalized_qty_unit"] = "unit"
        if mrp and multiplier:
            result["price_per_unit"] = round(float(mrp) / multiplier, 2)

    return result


if __name__ == "__main__":
    samples = [
        ("Amul Milk Shake Premix Strawberry, 500 g", 210),
        ("Amul Sweetened Condensed Milk, 210 g | Pack of 2", 160),
        ("Amul High Protein Wheat Flour, 65 g | Pack of 30 Sachets", 1200),
        ("Amul Kool Protein Milkshake Chocolate, 180 ml | Pack of 8", 320),
        ("Amul Organic Goan Cashews, 250 g", 500),
    ]
    for title, mrp in samples:
        print(title)
        print(parse_pack_info(title, mrp))
        print()
