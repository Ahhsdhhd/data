import re
import os
import numpy as np
import pandas as pd

# ──────────────────────────────────────────────
# LOADING & CLEANING
# ──────────────────────────────────────────────

def load_listings_data(file_path="data/listings.csv"):
    """Load and clean the listings CSV data."""
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path, low_memory=False)

    # Clean money columns
    for col in ["price", "cleaning_fee", "security_deposit", "extra_people", "weekly_price", "monthly_price"]:
        if col in df.columns:
            df[col] = df[col].replace(r"[\$,]", "", regex=True).astype(float)

    # Clean percentage columns
    for col in ["host_response_rate", "host_acceptance_rate"]:
        if col in df.columns:
            df[col] = df[col].replace(r"[%,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert boolean columns
    for col in ["host_is_superhost", "host_has_profile_pic", "host_identity_verified",
                "instant_bookable", "is_location_exact", "has_availability", "requires_license"]:
        if col in df.columns:
            df[col] = df[col].map({"t": True, "f": False})

    # Parse dates and derive host tenure
    for col in ["host_since", "first_review", "last_review", "last_scraped", "calendar_last_scraped"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "host_since" in df.columns:
        df["host_tenure_years"] = (pd.Timestamp.now() - df["host_since"]).dt.days / 365.25

    # Estimated monthly revenue proxy (from listings only):
    # booked nights ~ (365 - availability_365), monthly revenue = price * booked/30
    if "price" in df.columns and "availability_365" in df.columns:
        booked_365 = (365 - df["availability_365"]).clip(lower=0)
        df["estimated_monthly_revenue"] = df["price"] * booked_365 / 30.0

    return df


def load_calendar_data(file_path="data/calendar.csv"):
    """Load and clean the calendar CSV data."""
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path, low_memory=False)

    if "price" in df.columns:
        df["price"] = df["price"].replace(r"[\$,]", "", regex=True).astype(float)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    return df


# ──────────────────────────────────────────────
# TAB 1 · HOST QUALITY
# ──────────────────────────────────────────────

def get_host_quality_metrics(df):
    """Return a summary dict of host quality metrics."""
    metrics = {
        "total_hosts": int(df["host_id"].nunique()) if "host_id" in df.columns else 0,
        "superhost_pct": (df["host_is_superhost"].sum() / len(df) * 100) if "host_is_superhost" in df.columns else 0,
        "avg_response_rate": df["host_response_rate"].mean() if "host_response_rate" in df.columns else 0,
        "avg_acceptance_rate": df["host_acceptance_rate"].mean() if "host_acceptance_rate" in df.columns else 0,
        "avg_host_rating": df["review_scores_rating"].mean() if "review_scores_rating" in df.columns else 0,
    }
    return metrics


def get_area_ratings(df):
    """Ratings summary per neighbourhood."""
    if "neighbourhood_cleansed" not in df.columns:
        return pd.DataFrame()

    out = df.groupby("neighbourhood_cleansed").agg(
        avg_rating=("review_scores_rating", "mean"),
        listing_count=("id", "count"),
        avg_price=("price", "mean"),
    ).sort_values("avg_rating", ascending=True)

    return out


# ──────────────────────────────────────────────
# TAB 2 · AREA RATINGS & IMPROVEMENTS
# ──────────────────────────────────────────────

SUB_RATING_COLS = {
    "review_scores_accuracy": "Accuracy",
    "review_scores_cleanliness": "Cleanliness",
    "review_scores_checkin": "Check-in",
    "review_scores_communication": "Communication",
    "review_scores_location": "Location",
    "review_scores_value": "Value",
}


def get_area_deficiencies(df, min_listings=5):
    """Identify underperforming neighbourhoods and their weakest review domain."""
    if "neighbourhood_cleansed" not in df.columns:
        return pd.DataFrame()

    available_sub = [c for c in SUB_RATING_COLS if c in df.columns]
    if not available_sub:
        return pd.DataFrame()

    groups = df.dropna(subset=["review_scores_rating", *available_sub]).groupby("neighbourhood_cleansed")

    rows = []
    for nb, g in groups:
        if len(g) < min_listings:
            continue
        avg_rating = g["review_scores_rating"].mean()
        sub_means = {SUB_RATING_COLS[c]: g[c].mean() for c in available_sub}
        lowest_domain = min(sub_means, key=sub_means.get)
        rows.append({
            "Neighbourhood": nb,
            "Number of Listings": len(g),
            "Average Rating": round(avg_rating, 2),
            "Lowest Score Category": lowest_domain,
            "Lowest Score Value": round(sub_means[lowest_domain], 2),
        })

    out = pd.DataFrame(rows).sort_values("Average Rating", ascending=True)
    return out


# ──────────────────────────────────────────────
# TAB 3 · REVENUE
# ──────────────────────────────────────────────

def get_revenue_data(df):
    """Per-neighbourhood revenue summary (indexed by neighbourhood_cleansed)."""
    if "neighbourhood_cleansed" not in df.columns or "estimated_monthly_revenue" not in df.columns:
        return pd.DataFrame()

    out = df.groupby("neighbourhood_cleansed").agg(
        listing_count=("id", "count"),
        avg_price=("price", "mean"),
        total_reviews=("number_of_reviews", "sum") if "number_of_reviews" in df.columns else ("id", "count"),
        estimated_monthly_revenue=("estimated_monthly_revenue", "sum"),
    ).sort_values("estimated_monthly_revenue", ascending=False)

    return out


def get_regional_revenue_data(df):
    """Macro-region revenue summary (indexed by neighbourhood_group_cleansed)."""
    if "neighbourhood_group_cleansed" not in df.columns or "estimated_monthly_revenue" not in df.columns:
        return pd.DataFrame()

    out = df.groupby("neighbourhood_group_cleansed").agg(
        listing_count=("id", "count"),
        avg_price=("price", "mean"),
        avg_rating=("review_scores_rating", "mean") if "review_scores_rating" in df.columns else ("id", "count"),
        estimated_monthly_revenue=("estimated_monthly_revenue", "sum"),
    ).sort_values("estimated_monthly_revenue", ascending=False)

    return out


# ──────────────────────────────────────────────
# TAB 4 · PROPERTY ANALYSIS
# ──────────────────────────────────────────────

def get_property_analysis(df):
    """Property-level aggregates keyed by 'by_type' and 'by_room'."""
    data = {}

    if "property_type" in df.columns:
        data["by_type"] = df.groupby("property_type").agg(
            count=("id", "count"),
            price=("price", "mean"),
            rating=("review_scores_rating", "mean") if "review_scores_rating" in df.columns else ("id", "count"),
        ).sort_values("count", ascending=False)

    if "room_type" in df.columns:
        data["by_room"] = df.groupby("room_type").agg(
            count=("id", "count"),
            price=("price", "mean"),
            rating=("review_scores_rating", "mean") if "review_scores_rating" in df.columns else ("id", "count"),
        )

    if "bedrooms" in df.columns:
        data["by_bedrooms"] = df.groupby("bedrooms").agg(
            count=("id", "count"),
            price=("price", "mean"),
        ).drop(0, errors="ignore")

    return data


def parse_amenities(df, top_n=30):
    """Flatten the JSON-style amenities strings into a per-amenity count."""
    if "amenities" not in df.columns:
        return pd.Series(dtype=int)

    all_items = []
    for am in df["amenities"].dropna():
        clean = am.replace("{", "").replace("}", "").replace('"', "")
        items = [a.strip() for a in clean.split(",") if a.strip()]
        all_items.extend(items)

    return pd.Series(all_items).value_counts().head(top_n)


def get_amenity_premiums(df, min_listings=10):
    """Compute the price & rating premium for having each common amenity."""
    if "amenities" not in df.columns or "price" not in df.columns:
        return pd.DataFrame()

    baseline_price = df["price"].mean()
    baseline_rating = df["review_scores_rating"].mean() if "review_scores_rating" in df.columns else np.nan
    parsed = df["amenities"].fillna("")

    rows = []
    for amenity, count in parse_amenities(df, top_n=30).items():
        if count < min_listings:
            continue
        mask = parsed.str.contains(re.escape(amenity), case=False, regex=True)
        if mask.sum() < min_listings:
            continue
        with_price = df.loc[mask, "price"]
        with_rating = df.loc[mask, "review_scores_rating"].dropna()

        price_premium = with_price.mean() - baseline_price
        rating_premium = with_rating.mean() - baseline_rating if not with_rating.empty else 0.0

        rows.append({
            "Amenity": amenity,
            "Listings": int(mask.sum()),
            "Price Premium ($)": round(price_premium, 2),
            "Rating Premium": round(rating_premium, 2),
        })

    out = pd.DataFrame(rows).sort_values("Price Premium ($)", ascending=False)
    return out
