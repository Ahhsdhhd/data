# 🏠 Airbnb Analytics Dashboard

> **Seattle Airbnb Case Study** — An interactive analytics dashboard built with Streamlit, Plotly, and Pandas that fully answers 4 core business questions using both `listings.csv` and `calendar.csv` real data.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=flat&logo=plotly&logoColor=white)](https://plotly.com)

---

## 📌 Case Study Overview

Airbnb is one of the world's largest online accommodation platforms with millions of listings across 220+ countries. This dashboard uses the **Seattle Airbnb Open Data** to answer 4 business questions for stakeholders:

| # | Business Question | Tab |
|---|---|---|
| 1 | How is our Host quality looking like? | 👤 Q1 · Host Quality |
| 2 | Which areas are getting bad ratings — what improvement do they need? | 📍 Q2 · Area Ratings & Improvements |
| 3 | Regions generating good revenue | 💰 Q3 · Revenue Analysis |
| 4 | Property level analysis | 🏘️ Q4 · Property Level Analysis |

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get the Dataset
Download the Seattle Airbnb Open Data from [Kaggle](https://www.kaggle.com/datasets/airbnb/seattle) and place files in the `data/` folder:

```
data/
├── listings.csv      ← host, property, pricing, and rating info (required)
├── calendar.csv      ← daily availability & real nightly prices (required for Q3)
└── reviews.csv       ← guest review text (optional)
```

### 3. Run the App
```bash
streamlit run app.py
```
Open **http://localhost:8501** in your browser.

---

## 📁 Project Structure

```
airbnb_dashboard/
├── app.py              # Streamlit UI — all pages, filters, charts
├── data_loader.py      # Data engine — loads, cleans, computes all metrics
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── data/
    ├── listings.csv
    ├── calendar.csv
    └── reviews.csv
```

---

## 🔧 Architecture

```
listings.csv  ──┐
                ├──► data_loader.py ──► computed DataFrames ──► app.py ──► Streamlit UI
calendar.csv  ──┘                                                         (charts, filters, KPIs)
```

All data transformation happens in `data_loader.py`. `app.py` only handles rendering.

---

## 🔍 Interactive Filters (Sidebar)

All 4 tabs respond dynamically to these sidebar controls. Every chart respects the active filters.

| Filter | Type | What It Does |
|---|---|---|
| 💰 Nightly Price | Range Slider | Limits to listings in the selected price band |
| 🗺️ Macro Region | Multi-select | Filters by large neighbourhood groups |
| 🏠 Property Type | Multi-select | e.g. House, Apartment, Loft, Condominium |
| 🛏️ Room Type | Multi-select | Entire home / Private room / Shared room |
| 📍 Neighbourhood | Multi-select | Specific micro-neighbourhood filter |
| 🛏 Max Bedrooms | Slider | Upper bedroom count limit |
| ⭐ Superhost Only | Toggle | Show only Superhost-verified listings |
| ⚡ Instant Bookable | Toggle | Show only instantly bookable listings |

---

## 📊 Dashboard Tabs — Full Breakdown

---

### 👤 Q1 — Host Quality
**Business Question: How is our Host quality looking like?**

#### Charts & Visualizations

| Visual | What It Shows |
|---|---|
| Overlapping Histogram | Response Rate vs Acceptance Rate distribution side-by-side |
| Pie Chart | Host response speed categories (within an hour / a few hours / a day / etc.) |
| Pie Chart | Superhost vs Regular Host listing split |
| Box Plot | Overall rating (0–100) distribution comparing Superhost vs Regular Host |
| Grouped Bar Chart | 6 sub-rating category scores (Cleanliness, Accuracy, Check-in, Communication, Location, Value) comparing Superhost vs Regular Host |
| KPI Row | Avg Response Rate · Avg Acceptance Rate · Superhost % · Avg Host Rating |

#### How it works
```
fdf.groupby('host_is_superhost')[sub_rating_cols].mean()
→ melted → grouped bar chart comparing 6 categories across host types
```

---

### 📍 Q2 — Area Ratings & Improvements
**Business Question: Which areas are getting bad ratings — what improvement do they need?**

#### Charts & Visualizations

| Visual | What It Shows |
|---|---|
| Diagnostic Table | Every neighbourhood ranked by rating + its **Primary Deficiency** (lowest sub-category) |
| Horizontal Bar (Green) | Top 10 highest-rated neighbourhoods |
| Horizontal Bar (Coral) | Bottom 10 lowest-rated neighbourhoods |
| **Heatmap** | Bottom 15 neighbourhoods × 6 sub-rating categories — instantly shows which dimension is dragging scores |
| Interactive Map | Listings plotted on Seattle map, color = rating, bubble size = price |

#### How deficiencies are identified
```
For each neighbourhood (min 5 listings):
  → Average all 6 sub-ratings
  → Find the minimum → label as "Primary Deficiency"
  → e.g. "Rainier Beach needs to improve: Value (7.4/10)"
```

The heatmap makes the pattern immediately visible — a column that's consistently darker red across neighbourhoods indicates a systemic platform-wide problem (e.g. Value perception), while isolated dark cells indicate neighbourhood-specific issues.

---

### 💰 Q3 — Revenue Analysis
**Business Question: Regions generating good revenue**

> ✅ **Powered by real `calendar.csv` data** — not just proxy estimates.

#### Data Source Comparison

| Metric | Source | Method |
|---|---|---|
| Real Occupancy Rate | `calendar.csv` | `booked_nights / total_nights` per neighbourhood |
| Real Revenue | `calendar.csv` | `SUM(price)` on all booked (`available=f`) nights |
| Seasonal Trends | `calendar.csv` | Monthly groupby of occupancy % and avg price |
| Proxy Revenue | `listings.csv` | `avg_price × reviews_per_month` (fallback) |
| Revenue Drivers | `listings.csv` | Avg price vs listing count scatter per neighbourhood |

#### Charts & Visualizations

| Visual | What It Shows |
|---|---|
| Bar Chart (Teal) | Top 20 neighbourhoods by **real occupancy rate** (%) from calendar |
| Bar Chart (Plasma) | Top 15 neighbourhoods by **total real revenue** ($) from booked nights |
| Line Chart (Coral) | Monthly occupancy rate trend — identifies peak seasons |
| Line Chart (Teal) | Monthly avg nightly price trend — shows price seasonality |
| Bar Chart (Viridis) | Macro-region proxy revenue (Avg Price × Reviews/Month) |
| Scatter Plot | Avg Price vs Listing Count per neighbourhood — bubble = avg rating |

#### Revenue Formula (Real)
```
Real Revenue = SUM(calendar.price) WHERE available = 'f' (booked nights)
Real Occupancy = booked_nights / total_nights × 100
```

#### Revenue Formula (Proxy fallback)
```
Proxy Monthly Revenue = avg_nightly_price × sum(reviews_per_month)
```
> The proxy is a widely-used industry estimate since exact booking data is not public. The calendar method is more accurate.

---

### 🏘️ Q4 — Property Level Analysis
**Business Question: Property level analysis**

#### Charts & Visualizations

| Visual | What It Shows |
|---|---|
| Horizontal Bar | Top 10 property types by listing count, color-coded by avg price |
| Pie Chart | Room type split (Entire home / Private room / Shared room) |
| Box Plot | Rating (0–100) distribution across top 8 property types |
| Box Plot | Nightly price spread for 1–6 bedroom properties |
| Bar Chart (Blues) | Average nightly price by number of bathrooms |
| Bar Chart (Teal) | Price premium per amenity — how much extra hosts can charge |
| Table | Price Premium ($) and Rating Premium per amenity |
| Horizontal Bar | Top 15 most commonly listed amenities |

#### Amenity Premium Formula
```
Price Premium ($) = avg_price(WITH amenity) − avg_price(WITHOUT amenity)
Rating Premium    = avg_rating(WITH amenity) − avg_rating(WITHOUT amenity)
```
> Example: "Pool" adds $+45/night on average. "Hot Tub" adds $+38/night.

---

## ⚙️ Data Pipeline — `data_loader.py`

### Loading & Cleaning

| Function | Purpose |
|---|---|
| `load_listings_data()` | Read CSV, strip `$`/`%` from prices/rates, convert `t/f` booleans, cast ratings to float |
| `load_calendar_data()` | Read CSV, clean prices, parse dates, map `available` → bool, compute `booked` column |

### Q1 — Host Quality Functions

| Function | Returns |
|---|---|
| `get_host_quality_metrics(df)` | Dict of KPIs: total hosts, superhost %, avg response rate, avg acceptance rate, avg rating |

### Q2 — Area Functions

| Function | Returns |
|---|---|
| `get_area_ratings(df)` | Neighbourhood × avg rating, listing count, avg price |
| `get_area_deficiencies(df, min_listings)` | Neighbourhood × avg rating + Primary Deficiency label + score |

### Q3 — Revenue Functions

| Function | Source | Returns |
|---|---|---|
| `get_calendar_occupancy(cal, lst)` | calendar.csv | Occupancy rate % per neighbourhood |
| `get_real_revenue_by_neighbourhood(cal, lst)` | calendar.csv | Total revenue, booked nights, avg price per neighbourhood |
| `get_seasonal_trends(cal)` | calendar.csv | Monthly occupancy % and avg price |
| `get_revenue_data(df)` | listings.csv | Proxy revenue (avg price × reviews/month) |
| `get_regional_revenue_data(df)` | listings.csv | Proxy revenue by macro region |
| `get_price_vs_listings(df)` | listings.csv | Avg price vs listing count scatter data |

### Q4 — Property Functions

| Function | Returns |
|---|---|
| `get_property_analysis(df)` | Grouped data by property type, room type, bedrooms, bathrooms |
| `parse_amenities(df)` | Top 20 amenity value counts |
| `get_amenity_premiums(df)` | Price and rating delta WITH vs WITHOUT each amenity |

---

## 🎨 Design System

The app uses a custom Airbnb-inspired CSS theme injected into Streamlit:

| Token | Value | Usage |
|---|---|---|
| Primary / Coral | `#FF5A5F` | KPI values, key highlights, coral bars |
| Secondary / Teal | `#00A699` | Positive metrics, teal bars |
| Dark Charcoal | `#484848` | Headings and body text |
| Muted Gray | `#767676` | Subtitles, captions |
| Background | `#F7F7F7` | Page background |
| Card Background | `#FFFFFF` | KPI cards and sidebar |
| Font | Outfit (Google Fonts) | All text |

KPI cards include hover animations (`translateY(-3px)`) and soft drop shadows for a premium feel.

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---|---|---|
| `streamlit` | 1.32+ | UI framework — layout, filters, tabs |
| `plotly` | 5.18+ | All interactive charts, maps, heatmaps |
| `pandas` | 2.2+ | Data loading, cleaning, aggregation |
| `numpy` | 1.26+ | Numerical operations |

---

## 📈 Top-Level KPI Cards

The 5 KPI cards at the top always reflect active filters:

| Card | Source | Notes |
|---|---|---|
| Total Listings | `listings.csv` | Count after all filters applied |
| Avg Nightly Price | `listings.csv` | Mean of filtered price column |
| Avg Rating | `listings.csv` | Mean of `review_scores_rating` (0–100) |
| Superhost % | `listings.csv` | Superhost listings ÷ total filtered |
| Occupancy Rate | `calendar.csv` | Real global occupancy; "N/A" if calendar not loaded |

---

## 📄 Data Source

Dataset: [Seattle Airbnb Open Data — Kaggle](https://www.kaggle.com/datasets/airbnb/seattle)

Built for educational and analytical purposes as part of an Airbnb Case Study.
