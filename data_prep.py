import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

LISTINGS_FILE = DATA_DIR / "listings.csv"
CALENDAR_FILE = DATA_DIR / "calendar.csv"


@st.cache_data(show_spinner=False)
def load_listings():
    if not LISTINGS_FILE.exists():
        return None
    df = pd.read_csv(LISTINGS_FILE, low_memory=False)

    for col in ["price", "cleaning_fee", "security_deposit", "extra_people", "weekly_price", "monthly_price"]:
        if col in df.columns:
            df[col] = df[col].replace(r"[\$,]", "", regex=True).astype(float)

    for col in ["host_response_rate", "host_acceptance_rate"]:
        if col in df.columns:
            df[col] = df[col].replace(r"[%,]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["host_is_superhost", "host_has_profile_pic", "host_identity_verified",
                "instant_bookable", "is_location_exact", "has_availability", "requires_license"]:
        if col in df.columns:
            df[col] = df[col].map({"t": True, "f": False})

    for col in ["host_since", "first_review", "last_review", "last_scraped"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df["host_tenure_years"] = (pd.Timestamp.now() - df["host_since"]).dt.days / 365.25

    return df


@st.cache_data(show_spinner=False)
def load_calendar():
    if not CALENDAR_FILE.exists():
        return None
    cal = pd.read_csv(CALENDAR_FILE, usecols=["listing_id", "date", "available", "price"], low_memory=False)
    cal["date"] = pd.to_datetime(cal["date"])
    cal["price"] = cal["price"].replace(r"[\$,]", "", regex=True)
    cal["price"] = pd.to_numeric(cal["price"], errors="coerce")
    cal["booked"] = (cal["available"] == "f")
    return cal


@st.cache_data(show_spinner=False)
def compute_revenue_summary():
    cal = load_calendar()
    if cal is None:
        return None

    priced = cal.dropna(subset=["price"])

    rev = cal.groupby("listing_id").agg(
        booked_nights=("booked", "sum"),
        total_nights=("date", "count"),
        last_date=("date", "max"),
        first_date=("date", "min"),
    ).reset_index()

    avg_price = priced.groupby("listing_id")["price"].mean().rename("avg_daily_price")
    rev = rev.merge(avg_price, on="listing_id", how="left")

    rev["days_covered"] = (rev["last_date"] - rev["first_date"]).dt.days
    rev["occupancy_rate"] = (rev["booked_nights"] / rev["total_nights"] * 100).clip(0, 100)
    rev["estimated_total_revenue"] = rev["avg_daily_price"] * rev["booked_nights"]
    rev["monthly_revenue"] = rev["estimated_total_revenue"] / (rev["days_covered"] / 30).clip(lower=1)
    return rev


@st.cache_data(show_spinner=False)
def full_join():
    listings = load_listings()
    if listings is None:
        return None
    rev = compute_revenue_summary()
    if rev is None:
        return listings
    df = listings.merge(rev, left_on="id", right_on="listing_id", how="left")
    return df


def revenue_by_group(df, group_col="neighbourhood_group_cleansed"):
    if df is None or "estimated_total_revenue" not in df.columns:
        return None
    out = df.groupby(group_col).agg(
        listings=("id", "count"),
        total_revenue=("estimated_total_revenue", "sum"),
        monthly_revenue=("monthly_revenue", "sum"),
        avg_price=("price", "mean"),
        avg_rating=("review_scores_rating", "mean"),
        avg_occupancy=("occupancy_rate", "mean"),
    ).reset_index()
    out = out.sort_values("monthly_revenue", ascending=False)
    return out


def ratings_by_group(df, group_col="neighbourhood_group_cleansed"):
    if df is None:
        return None
    out = df.groupby(group_col).agg(
        listings=("id", "count"),
        avg_rating=("review_scores_rating", "mean"),
        avg_cleanliness=("review_scores_cleanliness", "mean"),
        avg_communication=("review_scores_communication", "mean"),
        avg_value=("review_scores_value", "mean"),
        avg_location=("review_scores_location", "mean"),
        avg_checkin=("review_scores_checkin", "mean"),
        avg_accuracy=("review_scores_accuracy", "mean"),
    ).reset_index()
    return out


def parse_amenities(df, top_n=20):
    if df is None or "amenities" not in df.columns:
        return pd.Series(dtype=int)

    all_items = []
    for am in df["amenities"].dropna():
        clean = am.replace("{", "").replace("}", "").replace('"', "")
        items = [a.strip() for a in clean.split(",") if a.strip()]
        all_items.extend(items)

    return pd.Series(all_items).value_counts().head(top_n)
