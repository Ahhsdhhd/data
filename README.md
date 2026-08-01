# 🏠 Airbnb Analytics Dashboard

> **Seattle Airbnb Case Study** — An interactive analytics dashboard built with Streamlit, Plotly, and Pandas to answer 4 core business questions from real-world Airbnb data.

---

## 📌 Case Study Overview

Airbnb is one of the world's largest online accommodation platforms with millions of listings in over 220 countries. This dashboard uses the **Seattle Airbnb Open Data** to help stakeholders understand:

1. **Host Quality** — How are hosts performing across response rates, acceptance rates, and guest ratings?
2. **Area Diagnostics** — Which neighbourhoods are getting poor ratings, and what specifically needs improvement?
3. **Revenue Analysis** — Which regions generate the most revenue, and what drives those numbers?
4. **Property Analysis** — How do property configurations and amenities affect pricing and guest satisfaction?

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Seattle Airbnb dataset (see below)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Dataset
Download the dataset from [Kaggle - Seattle Airbnb Open Data](https://www.kaggle.com/datasets/airbnb/seattle) and place the files inside the `data/` folder:

```
data/
├── listings.csv      # Main dataset with host, property, and rating info
├── calendar.csv      # Nightly availability and pricing data
└── reviews.csv       # Guest review text data
```

### Run the App
```bash
streamlit run app.py
```
Then open **http://localhost:8501** in your browser.

---

## 📁 Project Structure

```
airbnb_dashboard/
├── app.py              # Main Streamlit UI — renders all pages, filters, and charts
├── data_loader.py      # Data engine — loads, cleans, and computes all metrics
├── requirements.txt    # Python package dependencies
└── data/
    ├── listings.csv
    ├── calendar.csv
    └── reviews.csv
```

---

## 🔧 How It Works

### Architecture

```
listings.csv ──► data_loader.py ──► computed metrics ──► app.py ──► Streamlit UI
calendar.csv ──►                                                      (charts + filters)
```

### Data Pipeline (`data_loader.py`)

All data cleaning and aggregation is handled here before reaching the UI layer:

| Function | What It Does |
|---|---|
| `load_listings_data()` | Reads `listings.csv`, cleans price columns (`$128` → `128.0`), converts percentages (`97%` → `97.0`), maps boolean strings (`t/f` → `True/False`) |
| `load_calendar_data()` | Reads `calendar.csv`, cleans prices, parses dates |
| `get_host_quality_metrics()` | Calculates Superhost%, avg response rate, acceptance rate, and overall rating |
| `get_area_ratings()` | Groups listings by neighbourhood and computes average rating, listing count, and price |
| `get_area_deficiencies()` | For each neighbourhood, identifies the **lowest sub-rating category** (cleanliness, check-in, etc.) as the primary improvement area |
| `get_revenue_data()` | Estimates monthly revenue per neighbourhood: `avg_price × reviews_per_month` |
| `get_regional_revenue_data()` | Same as above but grouped by macro region (`neighbourhood_group_cleansed`) |
| `get_property_analysis()` | Groups listings by property type, room type, and bedroom count |
| `get_amenity_premiums()` | Calculates price and rating difference for listings that have vs. don't have specific amenities |
| `parse_amenities()` | Counts the top 20 most frequently listed amenities |

---

## 🔍 Interactive Filters (Sidebar)

All 4 dashboard tabs respond dynamically to these sidebar controls:

| Filter | Type | Effect |
|---|---|---|
| 💰 Price Range | Slider | Limits listings to a selected nightly price band |
| 🗺️ Macro Regions | Multi-select | Filters by large neighbourhood groups |
| 🏠 Property Types | Multi-select | e.g., House, Apartment, Condominium |
| 🛏️ Room Types | Multi-select | Entire home / Private room / Shared room |
| ⭐ Superhost Only | Toggle | Shows only Superhost-verified listings |
| ⚡ Instant Bookable | Toggle | Shows only instantly bookable listings |

---

## 📊 Dashboard Tabs

### 👤 Tab 1 — Host Quality
**Business Question: How is our Host quality looking like?**

| Visualization | Description |
|---|---|
| Histogram (Overlapping) | Response Rate vs. Acceptance Rate distribution across all hosts |
| Pie Chart | Host response speed categories (within an hour / a day / etc.) |
| Grouped Bar Chart | Sub-rating comparison (Cleanliness, Communication, Check-in, etc.) between Superhosts and Regular Hosts |

### 📍 Tab 2 — Area Ratings & Diagnostics
**Business Question: Which areas are getting bad ratings — what improvement do they need?**

| Visualization | Description |
|---|---|
| Diagnostic Table | Ranks low-performing neighbourhoods and flags their exact weakest sub-rating |
| Top 10 Bar Chart | Best-rated neighbourhoods (teal bars) |
| Bottom 10 Bar Chart | Worst-rated neighbourhoods (coral bars) |
| Interactive Map | Color-coded by rating score, bubble size = nightly price |

**How deficiencies are identified:**
```
For each neighbourhood:
  → Average all 6 sub-ratings (Cleanliness, Accuracy, Check-in, 
    Communication, Location, Value)
  → Find the minimum → flag as "Primary Deficiency"
```

### 💰 Tab 3 — Revenue Analysis
**Business Question: Which regions generate good revenue?**

| Visualization | Description |
|---|---|
| Macro Region Bar Chart | Estimated monthly revenue by large neighborhood group |
| Region Summary Table | Lists avg price, listing count, and total revenue per region |
| Micro Bar Chart | Top 15 most lucrative individual neighbourhoods |

**Revenue Formula:**
```
Estimated Monthly Revenue = Average Nightly Price × Sum of Reviews Per Month
```
> *This is a widely-used proxy for occupancy since exact booking data is not public.*

### 🏘️ Tab 4 — Property Level Analysis
**Business Question: Property level analysis**

| Visualization | Description |
|---|---|
| Horizontal Bar (Popularity) | Top 10 property types by listing count, colored by average price |
| Pie Chart | Room type distribution split |
| Box Plot | Price spread for 1–5 bedroom listings |
| Amenity Premium Bar Chart | Which amenities let hosts charge higher rates |
| Amenity Premium Table | Shows exact price and rating premium per amenity |

**Amenity Premium Formula:**
```
Price Premium ($) = Avg price of listings WITH amenity 
                 − Avg price of listings WITHOUT amenity
```

---

## 🎨 Design System

The app is styled with a custom Airbnb-inspired CSS theme:

| Element | Style |
|---|---|
| Font | Outfit (Google Fonts) |
| Primary Color | `#FF5A5F` (Airbnb Coral) |
| Secondary Color | `#00A699` (Airbnb Teal) |
| Body Text | `#484848` (Airbnb Dark Charcoal) |
| Muted Text | `#767676` (Airbnb Gray) |
| Background | `#F7F7F7` (Off-white) |
| Cards | White with rounded borders + drop shadows |

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---|---|---|
| `streamlit` | 1.32+ | UI framework for the dashboard |
| `plotly` | 5.18+ | Interactive charts, maps, and graphs |
| `pandas` | 2.2+ | Data loading, cleaning, and aggregation |
| `numpy` | 1.26+ | Numerical operations |

---

## 📈 Key Metrics at a Glance

Once data is loaded, the KPI cards at the top always show:
- **Total Listings** (respects active filters)
- **Average Price** (filtered)
- **Average Rating** out of 100
- **Superhost %**
- **Number of Neighbourhoods** in filter scope

---

## 📄 License

Dataset: [Seattle Airbnb Open Data — Kaggle](https://www.kaggle.com/datasets/airbnb/seattle)  
Dashboard built for educational and analytical purposes.
