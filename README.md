# Amul Quick-Commerce Analytics

Python scripts for collecting Amul catalogue data, loading it into PostgreSQL,
matching quick-commerce listings to catalogue products, and analyzing platform
observations.

## Project layout

```text
data/
  catalogue/       Catalogue CSV input
  observations/    Platform observation CSV inputs
  samples/         Example API response
  output/          Local diagnostic output (not committed)
pipeline/          Database and catalogue pipeline modules
scripts/diagnostics/  Optional API and scraper diagnostics
sql/               Database schema, migrations, and analytics queries
```

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set the PostgreSQL connection values.
4. Create the database and apply `sql/schema.sql`.

## Common commands

Run these from the repository root:

```powershell
python -m pipeline.check_db
python -m pipeline.scrape_amul_catalogue
python -m pipeline.load_catalogue_from_csv
python -m pipeline.match_products
python -m pipeline.load_platform_observations
```

The CSV loaders accept an optional path argument to use a different input file.
The default catalogue and observations inputs are under `data/`.

## Diagnostics

The optional scripts in `scripts/diagnostics/` check the live catalogue page
and its product API. They may require network access; the Playwright diagnostic
also requires a Playwright browser installation. Generated responses are
written to `data/output/`, which is intentionally excluded from version
control.