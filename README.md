# 🛖 Airbnb Intelligence Dashboard

An interactive **business intelligence dashboard** built with **Streamlit + Plotly** that analyzes the **Seattle Airbnb Open Data** (Kaggle) to answer four key business questions about host quality, area ratings, revenue generation, and property performance.

![Stack](https://img.shields.io/badge/Streamlit-1.60-FF4B4B) ![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB) ![Plotly](https://img.shields.io/badge/Plotly-6.0-3F4F75) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Business Questions Answered](#business-questions-answered)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Install Dependencies](#2-install-dependencies)
  - [3. Download the Dataset](#3-download-the-dataset)
  - [4. Run the App](#4-run-the-app)
- [Dashboard Guide](#dashboard-guide)
  - [Sidebar Filters](#sidebar-filters)
  - [KPI Cards](#kpi-cards)
  - [Tab 1 · Host Quality](#tab-1--host-quality)
  - [Tab 2 · Area Ratings](#tab-2--area-ratings)
  - [Tab 3 · Revenue Insights](#tab-3--revenue-insights)
  - [Tab 4 · Property Analysis](#tab-4--property-analysis)
- [Data Processing Details](#data-processing-details)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

This dashboard transforms a **raw 92-column listings CSV + 1.4M-row calendar CSV** into a modern, dark-themed analytics experience. It shows **host quality metrics**, **geographic rating gaps**, **real revenue estimates computed from calendar bookings**, and **property-level performance** — all filterable in real time from the sidebar.

> **What makes it special:** Revenue and occupancy are *not* guessed. They are derived from the `calendar.csv` file, which records each listing's daily price and whether each night was booked — giving a realistic revenue picture per neighbourhood.

---

## Business Questions Answered

| # | Question | Where answered |
|---|----------|----------------|
| 1 | **How is our host quality looking?** | Tab 1 · Host Quality |
| 2 | **Which areas get bad ratings — what should they improve?** | Tab 2 · Area Ratings |
| 3 | **Which regions generate good revenue?** | Tab 3 · Revenue Insights |
| 4 | **Property level analysis** | Tab 4 · Property Analysis |

---

## Features

- 🎛️ **Global sidebar filters** — neighbourhood group, room type, property type, price range. Every chart and KPI updates instantly.
- 🧮 **Live KPI cards** — listings, avg price, guest rating, estimated monthly revenue, occupancy, superhost share.
- 👤 **Host Quality tab** — superhost split, response/acceptance rate distributions, host tenure, rating by superhost status, response-rate vs rating trend (OLS).
- 📍 **Area Ratings tab** — lowest & highest rated neighbourhoods, a **radar chart** comparing the weakest area against the market average across cleanliness / communication / value / location / check-in / accuracy.
- 💰 **Revenue Insights tab** — monthly revenue leaderboard, revenue treemap, occupancy vs price scatter, price vs rating bubbles.
- 🏘️ **Property Analysis tab** — property type mix, room type pie, price by bedrooms, rating by property type, **amenities** that carry a price premium.
- 🎨 **Custom design system** — dark glassmorphism UI, Google Fonts (Plus Jakarta Sans / Inter), gradient accents, hover-lift cards, custom scrollbar.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | [Streamlit](https://streamlit.io) (web UI framework) |
| Visualisation | [Plotly Express](https://plotly.com/python/) + Plotly Graph Objects |
| Data processing | [pandas](https://pandas.pydata.org) / [NumPy](https://numpy.org) |
| Trend analysis | [statsmodels](https://www.statsmodels.org) (OLS trendline) |
| Data download | [kagglehub](https://github.com/Kaggle/kagglehub) |
| Language | Python 3.10+ |

---

## Dataset

Source: **Seattle Airbnb Open Data** on Kaggle — [`airbnb/seattle`](https://www.kaggle.com/datasets/airbnb/seattle)

| File | Rows | Description |
|------|------|-------------|
| `listings.csv` | 3,818 | One row per listing · 92 columns: host info, location, property, pricing, reviews, availability |
| `calendar.csv` | 1,393,570 | One row per **listing × day**: date, price, availability (t/f) |
| `reviews.csv` | 84,849 | Free-text guest reviews (not used in this dashboard) |

**Key columns used:**

- **Host:** `host_response_rate`, `host_acceptance_rate`, `host_is_superhost`, `host_since`, `host_total_listings_count`, `host_identity_verified`, `host_has_profile_pic`
- **Location:** `neighbourhood_group_cleansed`, `neighbourhood_cleansed`, `latitude`, `longitude`
- **Property:** `property_type`, `room_type`, `bedrooms`, `bathrooms`, `accommodates`, `amenities`
- **Pricing:** `price`, `cleaning_fee`, `security_deposit`, `extra_people`
- **Reviews:** `review_scores_rating`, `review_scores_cleanliness`, `review_scores_communication`, `review_scores_value`, `review_scores_location`, `review_scores_checkin`, `review_scores_accuracy`, `number_of_reviews`, `reviews_per_month`
- **Calendar:** `listing_id`, `date`, `available`, `price`

---

## Project Structure

```
airbnb_dashboard/
├── app.py                # Main Streamlit application (UI + all tabs)
├── data_prep.py          # Data loading, cleaning & derived metrics
├── requirements.txt      # Python dependencies
├── .gitignore            # Ignores __pycache__, *.pyc, data/*.csv
├── README.md             # This documentation
└── data/                 # Your CSV files live here (git-ignored)
```

---

## How It Works

### Architecture / Data Flow

```
Kaggle (airbnb/seattle)
        │  kagglehub.dataset_download()
        ▼
  data/listings.csv ───────────┐
  data/calendar.csv ───────────┤
        │                       │
        ▼                       ▼
   data_prep.py           data_prep.py
  load_listings()        compute_revenue_summary()
  (clean 92 cols)        (aggregate daily calendar)
        │                       │
        └──────────┬────────────┘
                   ▼
            full_join()
   listings merged with revenue on listing_id
                   │
                   ▼
              app.py  (Streamlit)
   ├── global filters (sidebar)
   ├── KPI cards
   ├── 4 tabs of Plotly charts
   └── every visual reacts to the filters
```

### `data_prep.py` — the engine room

| Function | Purpose |
|----------|---------|
| `load_listings()` | Reads `listings.csv`, strips `$`/`,` from money columns, `%` from rate columns, converts `t`/`f` to booleans, parses dates, computes `host_tenure_years`. |
| `load_calendar()` | Reads `calendar.csv` efficiently (4 columns only), parses dates & prices, derives a `booked` flag (`available == 'f'`). |
| `compute_revenue_summary()` | Per listing: total nights, **booked nights**, avg daily price (from nights that have a price), occupancy %, `estimated_total_revenue = avg_price × booked_nights`, `monthly_revenue` normalised to 30-day months. |
| `full_join()` | Merges listings with revenue on `listing_id → id`. **This is the main DataFrame every chart reads.** |
| `revenue_by_group()` | Aggregates revenue/price/occupancy/rating by neighbourhood group. |
| `ratings_by_group()` | Aggregates the six review-score dimensions per neighbourhood group. |
| `parse_amenities()` | Flattens the JSON-style `amenities` strings into a per-amenity count. |

> **⚠️ Revenue nuance:** In `calendar.csv`, prices are only recorded on *available* nights; booked nights have `NaN`. We therefore use the **average nightly price of a listing** (from its available nights) and multiply by **booked-night count**. This is the most defensible estimate available from the dataset.

### `app.py` — the presentation layer

- **Design system:** injected as a `<style>` block (`CUSTOM_CSS`) with CSS variables, Google Fonts import, glassmorphism KPI cards, styled tabs, hover animations.
- **Caching:** `@st.cache_data` on `get_df()` and all data-prep functions means the heavy 1.4M-row calendar processing runs **once**, then instant on every rerun.
- **Filtering:** one central filtered frame `fdf` is computed after the sidebar, and **all** tabs render from it — so filters stay in sync everywhere.
- **Plotly theming:** a shared `THEME` dict (dark transparent background, muted grid, spike lines) is applied via `chart_config(fig)`.

---

## Getting Started

### 1. Prerequisites

- Python **3.10 or newer** (tested on 3.12)
- ~700 MB free disk for the dataset

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the Dataset

**Option A — automatic (recommended, no Kaggle login):**

```bash
python -c "import kagglehub; print(kagglehub.dataset_download('airbnb/seattle'))"
```

Then copy the three CSVs into the project's `data/` folder:

```bash
# on Windows PowerShell:
Copy-Item "$env:USERPROFILE\.cache\kagglehub\datasets\airbnb\seattle\*\*.csv" .\data\
```

**Option B — manual:** download from the [Kaggle dataset page](https://www.kaggle.com/datasets/airbnb/seattle) and save `listings.csv` + `calendar.csv` (reviews optional) into `airbnb_dashboard/data/`.

### 4. Run the App

```bash
streamlit run app.py
```

Your browser opens automatically at **http://localhost:8501**.

> 💡 If `streamlit` isn't on your PATH (common on Windows), use the full Python path:
> `python -m streamlit run app.py`

---

## Dashboard Guide

### Sidebar Filters

| Filter | Options |
|--------|---------|
| **Neighbourhood Group** | 17 areas (Capitol Hill, Downtown, Queen Anne, West Seattle, …) |
| **Room Type** | Entire home/apt · Private room · Shared room |
| **Property Type** | Apartment, House, Condominium, Townhouse, … |
| **Price / night** | Range slider (min → 98th percentile) |

All four filters combine with **AND** logic. The sidebar footer shows how many of the 3,818 listings currently match.

### KPI Cards

| Card | What it tells you |
|------|-------------------|
| 🏠 Active Listings | Count matching filters |
| 💰 Avg Nightly Rate | Mean + median price per night |
| ⭐ Avg Guest Rating | Mean `review_scores_rating` (0–100) |
| 📈 Est. Monthly Rev | Sum of per-listing monthly revenue |
| 🛎️ Occupancy Rate | Mean % of nights booked |
| 👑 Superhosts | Share of superhost listings + avg response rate |

### Tab 1 · Host Quality

- **Superhost Split** — donut with % in the centre.
- **Response / Acceptance Rate Distributions** — histograms; a healthy market clusters near 100%.
- **Host Tenure** — years on Airbnb.
- **Rating by Superhost Status** — box plot; superhosts should out-rate standard hosts.
- **Response Rate vs Guest Rating** — scatter with an OLS trendline (requires `statsmodels`).

### Tab 2 · Area Ratings

- **Lowest / Highest Rated Neighbourhoods** — horizontal bars (only areas with ≥5 listings to avoid noisy extremes).
- **Radar chart** — the single weakest area vs the market average across the six review dimensions. **This directly answers "what improvement do they need?"** — e.g. a deep dip on `value` or `cleanliness` tells that area exactly what to fix.

### Tab 3 · Revenue Insights

- **Monthly Revenue by Neighbourhood** — bar chart, top 12.
- **Revenue Share Treemap** — visual weight of each area.
- **Occupancy vs Price** — bubble scatter (bubble size = monthly revenue); the sweet spot is high occupancy **and** high price.
- **Price vs Rating** — colour-coded by occupancy.

### Tab 4 · Property Analysis

- **Top Property Types** & **Room Type Mix**.
- **Avg Price by Bedrooms**.
- **Rating Distribution by Property Type**.
- **Most Common Amenities** + **price premium** for listings offering Wifi, Kitchen, Parking, Washer, Heating, Breakfast.

---

## Data Processing Details

### Cleaning (`load_listings`)

- `price`, `cleaning_fee`, `security_deposit`, `extra_people` → strip `$` and `,`, cast to float.
- `host_response_rate`, `host_acceptance_rate` → strip `%`, cast to float.
- `host_is_superhost`, `instant_bookable`, `is_location_exact`, … → `t`/`f` → `True`/`False`.
- `host_since`, `first_review`, `last_review` → `datetime`; `host_tenure_years` derived.

### Revenue & Occupancy (`compute_revenue_summary`)

```
total_nights      = count of days in calendar for a listing
booked_nights     = count of days where available == 'f'
occupancy_rate    = booked_nights / total_nights × 100
avg_daily_price   = mean of prices on available nights
est_total_revenue = avg_daily_price × booked_nights
monthly_revenue   = est_total_revenue / (days_covered / 30)
```

---

## Customization

| What | Where to edit |
|------|---------------|
| Brand colours | `PRIMARY`, `SECONDARY`, `DARK`, `CARD_BG` constants at top of `app.py` + CSS `:root` variables |
| Fonts | `@import url('...')` in `CUSTOM_CSS` |
| KPI cards | `kpi_data` list in `app.py` |
| Chart colours | `color_discrete_map` / `color_continuous_scale` on each `px` call |
| Min listings per area | `>= 5` filters in Area Ratings / Revenue tabs |
| Filters | Sidebar `multiselect` / `slider` blocks |
| Revenue window | `monthly_revenue` normalisation in `data_prep.py` |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'statsmodels'` | `pip install statsmodels` (needed for the OLS trendline) |
| App shows "Data files not found" | Ensure `listings.csv` & `calendar.csv` are inside `data/` |
| `streamlit: command not found` | Run `python -m streamlit run app.py` instead |
| SSL / build errors during `pip install` | Use an official Python 3.10+ from python.org, not MSYS2/MinGW |
| Dashboard is slow on first load | First run aggregates 1.4M calendar rows once; it is cached afterwards |
| KPI shows `0` revenue | Calendar may be empty for those listings — check `data/calendar.csv` is the full file |

---

## Roadmap

- [ ] Add a **map view** (scatter-mapbox of listings coloured by rating / price)
- [ ] Add **calendar/seasonality** analysis (revenue by month)
- [ ] **Machine learning** price prediction from property attributes
- [ ] Reviews **sentiment analysis** from `reviews.csv`
- [ ] Export filtered data to CSV / PDF report
- [ ] Multi-city support (other Airbnb datasets)

---

## License

MIT. Data belongs to Airbnb and is provided via the [Seattle Airbnb Open Data](https://www.kaggle.com/datasets/airbnb/seattle) Kaggle dataset.
