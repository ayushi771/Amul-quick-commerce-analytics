import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "herodb"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

REFERENCE_LOCATION = os.getenv("REFERENCE_LOCATION", "Ahmedabad")
REFERENCE_PINCODE = os.getenv("REFERENCE_PINCODE", "")

AMUL_BRAND_URL = "https://shop.amul.com/en/brand/amul"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
REQUEST_DELAY_SECONDS = 1.5  # be polite between requests
