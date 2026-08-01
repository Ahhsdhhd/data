import pandas as pd
import numpy as np
import os

def load_listings_data(file_path):
    """Load and clean the listings CSV data."""
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)

    # Clean price columns
    price_cols = ['price', 'cleaning_fee', 'security_deposit', 'extra_people']
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].replace(r'[\$,]', '', regex=True).astype(float)

    # Clean percentage columns
    pct_cols = ['host_response_rate', 'host_acceptance_rate']
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].replace(r'[\%,]', '', regex=True).astype(float)

    # Convert boolean columns
    bool_cols = ['host_is_superhost', 'host_has_profile_pic', 'host_identity_verified',
                 'instant_bookable', 'is_location_exact']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({'t': True, 'f': False})

    return df

def load_calendar_data(file_path):
    """Load and clean the calendar CSV data."""
    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)

    # Clean price column
    if 'price' in df.columns:
        df['price'] = df['price'].replace(r'[\$,]', '', regex=True).astype(float)

    # Convert date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    return df

def get_host_quality_metrics(df):
    """Calculate host quality metrics."""
    metrics = {
        'total_hosts': df['host_id'].nunique(),
        'superhost_pct': (df['host_is_superhost'].sum() / len(df) * 100) if 'host_is_superhost' in df.columns else 0,
        'avg_response_rate': df['host_response_rate'].mean() if 'host_response_rate' in df.columns else 0,
        'avg_acceptance_rate': df['host_acceptance_rate'].mean() if 'host_acceptance_rate' in df.columns else 0,
        'avg_host_rating': df['review_scores_rating'].mean() if 'review_scores_rating' in df.columns else 0,
    }
    return metrics

def get_area_ratings(df):
    """Get ratings by neighborhood."""
    if 'neighbourhood_cleansed' not in df.columns:
        return pd.DataFrame()

    area_ratings = df.groupby('neighbourhood_cleansed').agg({
        'review_scores_rating': 'mean',
        'id': 'count',
        'price': 'mean'
    }).rename(columns={'id': 'listing_count', 'price': 'avg_price'})

    area_ratings = area_ratings.sort_values('review_scores_rating', ascending=True)
    return area_ratings

def get_revenue_data(df):
    """Calculate revenue metrics by neighborhood."""
    if 'neighbourhood_cleansed' not in df.columns or 'price' not in df.columns:
        return pd.DataFrame()

    revenue = df.groupby('neighbourhood_cleansed').agg({
        'price': ['mean', 'median', 'count'],
        'number_of_reviews': 'sum',
        'reviews_per_month': 'sum'
    })

    revenue.columns = ['avg_price', 'median_price', 'listing_count', 'total_reviews', 'monthly_reviews']
    revenue['estimated_monthly_revenue'] = revenue['avg_price'] * revenue['monthly_reviews']

    return revenue.sort_values('estimated_monthly_revenue', ascending=False)

def get_property_analysis(df):
    """Get property level analysis data."""
    property_data = {}

    if 'property_type' in df.columns:
        property_data['by_type'] = df.groupby('property_type').agg({
            'price': 'mean',
            'review_scores_rating': 'mean',
            'id': 'count'
        }).rename(columns={'id': 'count'}).sort_values('count', ascending=False)

    if 'room_type' in df.columns:
        property_data['by_room'] = df.groupby('room_type').agg({
            'price': 'mean',
            'review_scores_rating': 'mean',
            'id': 'count'
        }).rename(columns={'id': 'count'})

    if 'bedrooms' in df.columns:
        property_data['by_bedrooms'] = df.groupby('bedrooms').agg({
            'price': 'mean',
            'review_scores_rating': 'mean',
            'id': 'count'
        }).rename(columns={'id': 'count'}).drop(0, errors='ignore')

    return property_data

def parse_amenities(df):
    """Parse amenities column and return amenity counts."""
    if 'amenities' not in df.columns:
        return pd.Series()

    all_amenities = []
    for amenities in df['amenities'].dropna():
        # Remove braces and quotes, split by comma
        clean = amenities.replace('{', '').replace('}', '').replace('"', '')
        items = [a.strip() for a in clean.split(',') if a.strip()]
        all_amenities.extend(items)

    return pd.Series(all_amenities).value_counts().head(20)
