import pandas as pd
import numpy as np
import os
import shutil


def ensure_data(data_dir="data"):
    """
    Auto-download the Seattle Airbnb dataset from Kaggle using kagglehub
    if the CSV files are not already present locally.
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables to be set.
    """
    listings_path = os.path.join(data_dir, "listings.csv")
    calendar_path = os.path.join(data_dir, "calendar.csv")

    if os.path.exists(listings_path) and os.path.exists(calendar_path):
        return  # already downloaded

    try:
        import kagglehub
        print("📥 Downloading Seattle Airbnb dataset from Kaggle...")
        path = kagglehub.dataset_download("airbnb/seattle")
        os.makedirs(data_dir, exist_ok=True)
        # Copy CSVs from the kagglehub cache into our data/ folder
        for fname in ["listings.csv", "calendar.csv", "reviews.csv"]:
            src = os.path.join(path, fname)
            dst = os.path.join(data_dir, fname)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
                print(f"  ✅ Copied {fname}")
        print("📦 Dataset ready.")
    except Exception as e:
        print(f"⚠️  Could not auto-download data: {e}")
        print("    Set KAGGLE_USERNAME and KAGGLE_KEY env vars, or place CSVs in data/ manually.")

def load_listings_data(file_path):
    """Load and clean the listings CSV data."""
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)

    # Clean price columns
    price_cols = ['price', 'cleaning_fee', 'security_deposit', 'extra_people']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Clean percentage columns
    pct_cols = ['host_response_rate', 'host_acceptance_rate']
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[\%,]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert boolean columns
    bool_cols = ['host_is_superhost', 'host_has_profile_pic', 'host_identity_verified',
                 'instant_bookable', 'is_location_exact']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({'t': True, 'f': False})

    # Ensure numeric ratings
    rating_cols = [
        'review_scores_rating', 'review_scores_accuracy', 'review_scores_cleanliness',
        'review_scores_checkin', 'review_scores_communication', 'review_scores_location',
        'review_scores_value'
    ]
    for col in rating_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def load_calendar_data(file_path):
    """Load and clean the calendar CSV data."""
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)

    # Clean price column
    if 'price' in df.columns:
        df['price'] = df['price'].astype(str).str.replace(r'[\$,]', '', regex=True)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # Convert date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Convert available to boolean
    if 'available' in df.columns:
        df['available'] = df['available'].map({'t': True, 'f': False})
        df['booked'] = ~df['available']

    return df


# ─────────────────────────────────────────────
#  Q1 – HOST QUALITY
# ─────────────────────────────────────────────

def get_host_quality_metrics(df):
    """Calculate top-level host quality KPIs."""
    return {
        'total_hosts': df['host_id'].nunique() if 'host_id' in df.columns else 0,
        'superhost_pct': (df['host_is_superhost'].sum() / len(df) * 100) if 'host_is_superhost' in df.columns else 0,
        'avg_response_rate': df['host_response_rate'].mean() if 'host_response_rate' in df.columns else 0,
        'avg_acceptance_rate': df['host_acceptance_rate'].mean() if 'host_acceptance_rate' in df.columns else 0,
        'avg_host_rating': df['review_scores_rating'].mean() if 'review_scores_rating' in df.columns else 0,
    }


# ─────────────────────────────────────────────
#  Q2 – AREA RATINGS & DIAGNOSTICS
# ─────────────────────────────────────────────

def get_area_ratings(df):
    """Get average rating, listing count, and avg price by neighbourhood."""
    if 'neighbourhood_cleansed' not in df.columns:
        return pd.DataFrame()

    area_ratings = df.groupby('neighbourhood_cleansed').agg(
        review_scores_rating=('review_scores_rating', 'mean'),
        listing_count=('id', 'count'),
        avg_price=('price', 'mean')
    ).sort_values('review_scores_rating', ascending=True)

    return area_ratings


def get_area_deficiencies(df, min_listings=5):
    """
    For each neighbourhood identify its weakest sub-rating category.
    Returns a sorted table with the Primary Deficiency column.
    """
    sub_rating_map = {
        'review_scores_cleanliness': 'Cleanliness',
        'review_scores_accuracy': 'Accuracy',
        'review_scores_checkin': 'Check-in',
        'review_scores_communication': 'Communication',
        'review_scores_location': 'Location',
        'review_scores_value': 'Value',
    }

    sub_cols = [c for c in sub_rating_map if c in df.columns]
    if 'neighbourhood_cleansed' not in df.columns or len(sub_cols) < 2:
        return pd.DataFrame()

    agg = {'id': 'count', 'review_scores_rating': 'mean'}
    agg.update({c: 'mean' for c in sub_cols})

    grouped = df.groupby('neighbourhood_cleansed').agg(agg)
    grouped = grouped[grouped['id'] >= min_listings]

    rows = []
    for idx, row in grouped.iterrows():
        scores = {sub_rating_map[c]: row[c] for c in sub_cols if not pd.isna(row[c])}
        if scores:
            worst = min(scores, key=scores.get)
            rows.append({
                'Neighbourhood': idx,
                'Total Listings': int(row['id']),
                'Avg Rating (100)': round(row['review_scores_rating'], 1),
                'Primary Deficiency': worst,
                'Deficiency Score (/10)': round(scores[worst], 2),
            })

    result = pd.DataFrame(rows)
    return result.sort_values('Avg Rating (100)') if not result.empty else result


# ─────────────────────────────────────────────
#  Q3 – REVENUE ANALYSIS  (calendar-powered)
# ─────────────────────────────────────────────

def get_calendar_occupancy(calendar_df, listings_df):
    """
    Compute real occupancy rate per neighbourhood using calendar availability data.
    Occupancy = booked nights / total nights tracked per listing.
    """
    if calendar_df is None or listings_df is None:
        return pd.DataFrame()
    if 'neighbourhood_cleansed' not in listings_df.columns:
        return pd.DataFrame()

    # Map listing_id → neighbourhood
    nb_map = listings_df.set_index('id')['neighbourhood_cleansed'].to_dict()
    cal = calendar_df.copy()
    cal['neighbourhood'] = cal['listing_id'].map(nb_map)
    cal = cal.dropna(subset=['neighbourhood'])

    occ = cal.groupby('neighbourhood').agg(
        total_nights=('booked', 'count'),
        booked_nights=('booked', 'sum')
    )
    occ['occupancy_rate_pct'] = (occ['booked_nights'] / occ['total_nights'] * 100).round(1)
    return occ.sort_values('occupancy_rate_pct', ascending=False)


def get_real_revenue_by_neighbourhood(calendar_df, listings_df):
    """
    Real revenue estimate per neighbourhood:
      revenue = sum of calendar price on booked (available=False) nights.
    """
    if calendar_df is None or listings_df is None:
        return pd.DataFrame()
    if 'neighbourhood_cleansed' not in listings_df.columns:
        return pd.DataFrame()

    nb_map = listings_df.set_index('id')['neighbourhood_cleansed'].to_dict()
    cal = calendar_df.copy()
    cal['neighbourhood'] = cal['listing_id'].map(nb_map)
    cal = cal.dropna(subset=['neighbourhood', 'price'])

    booked = cal[cal['booked'] == True]
    if booked.empty:
        return pd.DataFrame()

    rev = booked.groupby('neighbourhood').agg(
        total_revenue=('price', 'sum'),
        booked_nights=('price', 'count'),
        avg_nightly_price=('price', 'mean')
    ).sort_values('total_revenue', ascending=False)

    rev['total_revenue'] = rev['total_revenue'].round(0)
    rev['avg_nightly_price'] = rev['avg_nightly_price'].round(2)
    return rev


def get_seasonal_trends(calendar_df):
    """Monthly occupancy rate and average nightly price trend from calendar data."""
    if calendar_df is None or calendar_df.empty:
        return pd.DataFrame()
    if 'date' not in calendar_df.columns:
        return pd.DataFrame()

    cal = calendar_df.copy()
    cal['month'] = cal['date'].dt.to_period('M').astype(str)

    monthly = cal.groupby('month').agg(
        total_nights=('booked', 'count'),
        booked_nights=('booked', 'sum'),
        avg_price=('price', 'mean')
    )
    monthly['occupancy_rate_pct'] = (monthly['booked_nights'] / monthly['total_nights'] * 100).round(1)
    monthly = monthly.sort_index()
    return monthly


def get_revenue_data(df):
    """Proxy revenue estimate using listings data (fallback when no calendar)."""
    if 'neighbourhood_cleansed' not in df.columns or 'price' not in df.columns:
        return pd.DataFrame()

    revenue = df.groupby('neighbourhood_cleansed').agg(
        avg_price=('price', 'mean'),
        median_price=('price', 'median'),
        listing_count=('price', 'count'),
        total_reviews=('number_of_reviews', 'sum'),
        monthly_reviews=('reviews_per_month', 'sum')
    )
    revenue['estimated_monthly_revenue'] = revenue['avg_price'] * revenue['monthly_reviews']
    return revenue.sort_values('estimated_monthly_revenue', ascending=False)


def get_regional_revenue_data(df):
    """Proxy revenue by macro region (neighbourhood_group_cleansed)."""
    group_col = 'neighbourhood_group_cleansed' if 'neighbourhood_group_cleansed' in df.columns else 'neighbourhood_cleansed'
    if group_col not in df.columns or 'price' not in df.columns:
        return pd.DataFrame()

    revenue = df.groupby(group_col).agg(
        avg_price=('price', 'mean'),
        median_price=('price', 'median'),
        listing_count=('price', 'count'),
        monthly_reviews=('reviews_per_month', 'sum')
    )
    revenue['estimated_monthly_revenue'] = revenue['avg_price'] * revenue['monthly_reviews']
    return revenue.sort_values('estimated_monthly_revenue', ascending=False)


def get_price_vs_listings(df):
    """Avg price vs listing count scatter data by neighbourhood."""
    if 'neighbourhood_cleansed' not in df.columns:
        return pd.DataFrame()

    scatter = df.groupby('neighbourhood_cleansed').agg(
        avg_price=('price', 'mean'),
        listing_count=('id', 'count'),
        avg_rating=('review_scores_rating', 'mean')
    ).dropna()
    return scatter.reset_index()


# ─────────────────────────────────────────────
#  Q4 – PROPERTY LEVEL ANALYSIS
# ─────────────────────────────────────────────

def get_property_analysis(df):
    """Get property-level aggregations by type, room type, bedrooms, bathrooms."""
    prop = {}

    if 'property_type' in df.columns:
        prop['by_type'] = df.groupby('property_type').agg(
            price=('price', 'mean'),
            review_scores_rating=('review_scores_rating', 'mean'),
            count=('id', 'count')
        ).sort_values('count', ascending=False)

    if 'room_type' in df.columns:
        prop['by_room'] = df.groupby('room_type').agg(
            price=('price', 'mean'),
            review_scores_rating=('review_scores_rating', 'mean'),
            count=('id', 'count')
        )

    if 'bedrooms' in df.columns:
        bed = df.groupby('bedrooms').agg(
            price=('price', 'mean'),
            review_scores_rating=('review_scores_rating', 'mean'),
            count=('id', 'count')
        ).drop(0, errors='ignore')
        prop['by_bedrooms'] = bed

    if 'bathrooms' in df.columns:
        bath = df.groupby('bathrooms').agg(
            price=('price', 'mean'),
            review_scores_rating=('review_scores_rating', 'mean'),
            count=('id', 'count')
        ).drop(0, errors='ignore')
        prop['by_bathrooms'] = bath

    return prop


def parse_amenities(df):
    """Return value counts of top 20 most common amenities."""
    if 'amenities' not in df.columns:
        return pd.Series(dtype=float)

    all_amenities = []
    for amenities in df['amenities'].dropna():
        clean = amenities.replace('{', '').replace('}', '').replace('"', '')
        items = [a.strip() for a in clean.split(',') if a.strip()]
        all_amenities.extend(items)

    return pd.Series(all_amenities).value_counts().head(20)


def get_amenity_premiums(df, top_amenities=None):
    """Price and rating delta for listings that have vs. don't have each amenity."""
    if 'amenities' not in df.columns or 'price' not in df.columns:
        return pd.DataFrame()

    if top_amenities is None:
        top_amenities = [
            'Wireless Internet', 'Heating', 'Air Conditioning', 'Kitchen',
            'Free Parking on Premises', 'Pets Allowed', 'Hot Tub', 'Pool',
            'Cable TV', 'Washer', 'Dryer', 'Gym',
        ]

    rows = []
    for amenity in top_amenities:
        has = df['amenities'].fillna('').str.contains(amenity, case=False, regex=False)
        if has.sum() > 10 and (~has).sum() > 10:
            price_w = df.loc[has, 'price'].mean()
            price_wo = df.loc[~has, 'price'].mean()
            rating_w = df.loc[has, 'review_scores_rating'].mean()
            rating_wo = df.loc[~has, 'review_scores_rating'].mean()
            rows.append({
                'Amenity': amenity,
                'Avg Price With ($)': round(price_w, 2),
                'Avg Price Without ($)': round(price_wo, 2),
                'Price Premium ($)': round(price_w - price_wo, 2),
                'Rating Premium': round(rating_w - rating_wo, 2),
            })

    return pd.DataFrame(rows).sort_values('Price Premium ($)', ascending=False)
