# Amul Quick-Commerce Analytics

### Digital Shelf Intelligence | Python · PostgreSQL · Power BI

An end-to-end business intelligence project for analyzing Amul product availability, pricing, delivery estimates, and digital shelf performance across quick-commerce platforms.

---

## 📊 Project Overview

**Amul Quick-Commerce Analytics** is a data analytics and business intelligence project designed to understand how Amul products perform across online grocery and quick-commerce platforms.

The project combines Python-based data processing, PostgreSQL data management, SQL analysis, and interactive Power BI dashboards to turn platform-level product observations into meaningful business insights.

It also includes a **Power BI alert visual** designed to display important status messages and highlight potential digital shelf issues directly within the dashboard.

The goal is to support better visibility into product performance, identify areas requiring attention, and enable data-driven business decisions.

## 🎯 Business Objectives

- Analyze Amul product availability across quick-commerce platforms.
- Compare observed prices for matching products across platforms.
- Understand delivery ETA differences across cities and platforms.
- Evaluate category-level and platform-level digital shelf performance.
- Identify potential issues through dashboard alert indicators.
- Present analytical results through clear, business-oriented visualizations.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing, product matching, and ingestion |
| PostgreSQL | Relational database and structured data storage |
| SQL | Data validation, querying, and analysis |
| Power BI | Interactive dashboard and business reporting |
| DAX | KPI calculations and analytical measures |
| TypeScript | Custom Power BI alert visual development |
| CSV | Structured input data and platform observations |
| Git & GitHub | Version control and project documentation |

## 🛒 Platforms Covered

The project analyzes observations from four quick-commerce platforms:

- Blinkit
- Zepto
- Swiggy Instamart
- BigBasket

## 📍 Geographic Coverage

The dataset includes observations from four Indian cities:

- Ahmedabad
- Bengaluru
- Delhi
- Mumbai

## ✨ Key Features

### 1. Product Catalogue Analysis

- Organizes product information into structured database tables.
- Supports consistent product identification and matching.
- Provides a foundation for cross-platform product comparisons.

### 2. Cross-Platform Price Comparison

- Compares observed prices for matching products.
- Helps identify price differences between platforms.
- Supports platform-level pricing analysis using recorded observations.

### 3. Product Availability Monitoring

- Examines product availability across platforms and cities.
- Helps identify potentially unavailable products.
- Supports comparisons of digital shelf availability.

### 4. Delivery ETA Analysis

- Analyzes recorded delivery-time estimates.
- Compares estimated delivery times across platforms and locations.
- Supports identification of delivery estimates that exceed defined business thresholds.

### 5. Category Digital Shelf Health

- Supports category-level performance comparisons.
- Helps identify categories that may require further investigation.
- Provides a business-oriented view beyond individual product availability.

### 6. Platform Performance Analysis

- Compares platform-level performance using selected business KPIs.
- Helps identify differences in availability, pricing, and delivery estimates.
- Supports operational analysis across the covered cities.

### 7. Custom Power BI Alert Visual 🚨

The project includes a custom alert visual developed for Power BI to communicate important information directly within the dashboard.

**Key capabilities:**

- Displays alert titles and descriptive messages.
- Uses visual styling to make important status information easy to notice.
- Helps communicate potential issues identified through dashboard measures or configured conditions.
- Supports a more focused dashboard experience by bringing attention to relevant business exceptions.

**Potential business alert scenarios include:**

| Alert Scenario | Purpose |
|---|---|
| Product Availability | Highlight products recorded as unavailable |
| Price Variation | Identify price differences that require review |
| Delivery ETA | Flag estimates that exceed a defined threshold |
| Category Performance | Bring attention to weaker category-level KPIs |
| Platform Performance | Highlight platform-level issues for investigation |

The scenarios above describe possible alert conditions. Their actual behavior depends on the measures, thresholds, and conditions implemented in the report.

The alert visual displays information within Power BI; automated email or push notifications are not implied.

## 📈 Power BI Dashboard

The Power BI report presents digital shelf performance through business-focused KPIs, comparisons, and analytical visualizations.

### Dashboard Screenshots

<img width="1152" height="856" alt="image" src="https://github.com/user-attachments/assets/d82331ab-1a55-4d8e-a3d8-be18ed4021e1" />

The report is designed to help users explore:

- Platform-level performance.
- City-level product availability.
- Category digital shelf health.
- Observed price differences.
- Average delivery ETA.
- Important status messages through the custom alert visual.

The dashboard connects the data preparation and database layers to a visual reporting experience intended for business analysis.

## 🗄️ Database Design

The project uses PostgreSQL to organize product catalogue information and platform observations.

The database includes dimension tables and fact tables to support structured querying and analytical reporting.

### Key Tables

| Table | Purpose |
|---|---|
| `dim_product` | Product information |
| `dim_category` | Product category details |
| `dim_platform` | Quick-commerce platform information |
| `dim_location` | City and location details |
| `dim_date` | Date dimension for analysis |
| `fact_catalogue_snapshot` | Catalogue snapshot records |
| `fact_platform_observation` | Platform-level product observations |
| `product_platform_mapping` | Product matching across platforms |

This structure supports consistent product identification and analysis across multiple platforms and locations.

## 🔄 Data Pipeline

The project includes Python scripts for catalogue processing, product matching, and loading platform observations into PostgreSQL.

### Workflow

1. Prepare product catalogue and platform observation data.
2. Process and match products across platform records.
3. Validate the input data and required fields.
4. Load observations into PostgreSQL.
5. Connect the database to Power BI.
6. Create DAX measures and business KPIs.
7. Build dashboard visualizations and the alert visual.

### Main Project Scripts

| File | Responsibility |
|---|---|
| `config.py` | Project configuration |
| `db.py` | Database connectivity |
| `schema.sql` | Database schema definition |
| `match_products.py` | Product matching workflow |
| `load_catalogue_from_csv.py` | Catalogue data loading |
| `load_platform_observations.py` | Platform observation ingestion |
| `scrape_amul_catalogue.py` | Catalogue extraction |
| `pack_parser.py` | Product pack information parsing |

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or later
- PostgreSQL
- Power BI Desktop
- Git

### 1. Clone the repository

```bash
git clone https://github.com/ayushi771/Amul-quick-commerce-analytics.git
cd Amul-quick-commerce-analytics
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Create a PostgreSQL database and configure the database connection settings using environment variables.

Use `.env.example` as a reference for the required environment variables.

Apply the schema using the project's SQL file:

```bash
psql -U postgres -d your_database -f schema.sql
```

Replace `your_database` with the actual PostgreSQL database name.

### 5. Prepare and load data

Use the appropriate CSV files available in the repository.

For example:

```bash
python match_products.py "your_observations.csv"
python load_platform_observations.py "your_observations.csv"
```

Replace the example filename with the actual input file. Configure the database connection before running the scripts.

### 6. Open the Power BI report

Open the project's `.pbix` file in Power BI Desktop.

Configure the PostgreSQL connection if required, refresh the data, and review the dashboard and alert visual.

## 🔍 Data Quality and Limitations

- Price and availability results reflect the recorded observations and collection dates.
- Product matching is important for accurate cross-platform comparisons.
- Delivery ETA is an estimate and should not be interpreted as a guaranteed delivery time.
- Historical observations may differ from current platform listings.
- Alert results depend on the conditions and thresholds configured in the report.
- Conclusions should be interpreted within the dataset's geographic and temporal coverage.

## 🔮 Future Enhancements

- Scheduled data collection and refresh workflows.
- Historical pricing and availability trend analysis.
- Expanded city and platform coverage.
- Additional data quality validation.
- More advanced alert conditions and exception monitoring.
- Automated notifications, where supported and implemented.
- Additional category and product-level performance indicators.

## 💼 Business Value

This project demonstrates how product-level observations can be transformed into structured data, analyzed across multiple platforms, and presented through a business intelligence dashboard.

It combines data engineering, relational database design, analytical calculations, dashboard development, and custom visual development in a single analytics workflow.

## 👩‍💻 Author

**Ayushi Somani**

Data Analytics · Python · SQL · PostgreSQL · Power BI

---

*Amul Quick-Commerce Analytics — turning digital shelf observations into actionable business insights.*
