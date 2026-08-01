import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import (
    load_listings_data,
    load_calendar_data,
    get_host_quality_metrics,
    get_area_ratings,
    get_revenue_data,
    get_property_analysis,
    parse_amenities
)

st.set_page_config(
    page_title="Airbnb Analytics Dashboard",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Airbnb Analytics Dashboard")
st.markdown("### Seattle Airbnb Open Data Analysis")

# Sidebar for data loading
st.sidebar.header("Data Source")
listings_file = st.sidebar.text_input("Listings CSV path", "data/listings.csv")
calendar_file = st.sidebar.text_input("Calendar CSV path", "data/calendar.csv")

# Load data
listings_df = load_listings_data(listings_file)
calendar_df = load_calendar_data(calendar_file)

if listings_df is None:
    st.error("Could not load listings data. Please ensure the CSV file exists at the specified path.")
    st.info("Download the dataset from: https://www.kaggle.com/datasets/airbnb/seattle")
    st.stop()

st.sidebar.success(f"Loaded {len(listings_df):,} listings")

# KPI Cards at the top
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Listings", f"{len(listings_df):,}")
with col2:
    st.metric("Avg Price", f"${listings_df['price'].mean():.0f}" if 'price' in listings_df.columns else "N/A")
with col3:
    st.metric("Avg Rating", f"{listings_df['review_scores_rating'].mean():.1f}" if 'review_scores_rating' in listings_df.columns else "N/A")
with col4:
    superhost_pct = (listings_df['host_is_superhost'].sum() / len(listings_df) * 100) if 'host_is_superhost' in listings_df.columns else 0
    st.metric("Superhost %", f"{superhost_pct:.1f}%")
with col5:
    st.metric("Neighbourhoods", f"{listings_df['neighbourhood_cleansed'].nunique()}" if 'neighbourhood_cleansed' in listings_df.columns else "N/A")

st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Host Quality",
    "📍 Area Ratings",
    "💰 Revenue Analysis",
    "🏘️ Property Analysis"
])

# Tab 1: Host Quality
with tab1:
    st.header("Host Quality Analysis")

    metrics = get_host_quality_metrics(listings_df)

    col1, col2 = st.columns(2)

    with col1:
        # Superhost distribution
        if 'host_is_superhost' in listings_df.columns:
            superhost_data = listings_df['host_is_superhost'].value_counts().reset_index()
            superhost_data.columns = ['is_superhost', 'count']
            superhost_data['is_superhost'] = superhost_data['is_superhost'].map({True: 'Superhost', False: 'Regular Host'})

            fig = px.pie(superhost_data, values='count', names='is_superhost',
                        title='Superhost vs Regular Host Distribution',
                        color_discrete_sequence=['#FF5A5F', '#00A699'])
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Response rate distribution
        if 'host_response_rate' in listings_df.columns:
            fig = px.histogram(listings_df.dropna(subset=['host_response_rate']),
                             x='host_response_rate',
                             nbins=20,
                             title='Host Response Rate Distribution',
                             labels={'host_response_rate': 'Response Rate (%)'},
                             color_discrete_sequence=['#FF5A5F'])
            fig.update_layout(xaxis_title="Response Rate (%)", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Rating by superhost status
        if 'host_is_superhost' in listings_df.columns and 'review_scores_rating' in listings_df.columns:
            fig = px.box(listings_df.dropna(subset=['review_scores_rating']),
                        x='host_is_superhost', y='review_scores_rating',
                        title='Rating Distribution by Superhost Status',
                        labels={'host_is_superhost': 'Superhost', 'review_scores_rating': 'Rating'})
            fig.update_xaxis(tickvals=[0, 1], ticktext=['Regular', 'Superhost'])
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Acceptance rate distribution
        if 'host_acceptance_rate' in listings_df.columns:
            fig = px.histogram(listings_df.dropna(subset=['host_acceptance_rate']),
                             x='host_acceptance_rate',
                             nbins=20,
                             title='Host Acceptance Rate Distribution',
                             labels={'host_acceptance_rate': 'Acceptance Rate (%)'},
                             color_discrete_sequence=['#00A699'])
            fig.update_layout(xaxis_title="Acceptance Rate (%)", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

    # Host quality summary
    st.subheader("Host Quality Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Response Rate", f"{metrics['avg_response_rate']:.1f}%")
    with col2:
        st.metric("Avg Acceptance Rate", f"{metrics['avg_acceptance_rate']:.1f}%")
    with col3:
        st.metric("Superhost Percentage", f"{metrics['superhost_pct']:.1f}%")
    with col4:
        st.metric("Avg Host Rating", f"{metrics['avg_host_rating']:.1f}")

# Tab 2: Area Ratings
with tab2:
    st.header("Area Ratings Analysis")

    area_ratings = get_area_ratings(listings_df)

    if not area_ratings.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            # Top and bottom neighborhoods by rating
            top_n = st.slider("Show top/bottom N neighborhoods", 5, 20, 10)

            top_areas = area_ratings.nlargest(top_n, 'review_scores_rating')
            bottom_areas = area_ratings.nsmallest(top_n, 'review_scores_rating')

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=top_areas.index[::-1],
                x=top_areas['review_scores_rating'][::-1],
                name=f'Top {top_n}',
                orientation='h',
                marker_color='#00A699'
            ))
            fig.add_trace(go.Bar(
                y=bottom_areas.index[::-1],
                x=bottom_areas['review_scores_rating'][::-1],
                name=f'Bottom {top_n}',
                orientation='h',
                marker_color='#FF5A5F'
            ))

            fig.update_layout(
                title=f'Top vs Bottom {top_n} Neighbourhoods by Rating',
                xaxis_title='Average Rating',
                barmode='group',
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Areas Needing Improvement")
            st.dataframe(
                bottom_areas[['review_scores_rating', 'listing_count', 'avg_price']].round(2),
                use_container_width=True
            )

        # Geographic scatter plot
        if 'latitude' in listings_df.columns and 'longitude' in listings_df.columns:
            st.subheader("Geographic Rating Distribution")
            sample_df = listings_df.dropna(subset=['latitude', 'longitude', 'review_scores_rating']).sample(
                min(1000, len(listings_df)), random_state=42
            )

            fig = px.scatter_mapbox(
                sample_df,
                lat='latitude',
                lon='longitude',
                color='review_scores_rating',
                size='price' if 'price' in sample_df.columns else None,
                color_continuous_scale='RdYlGn',
                size_max=15,
                zoom=11,
                mapbox_style='open-street-map',
                title='Listing Ratings by Location',
                hover_data=['neighbourhood_cleansed', 'price', 'review_scores_rating']
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

# Tab 3: Revenue Analysis
with tab3:
    st.header("Revenue Analysis")

    revenue_data = get_revenue_data(listings_df)

    if not revenue_data.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Top neighborhoods by estimated revenue
            top_revenue = revenue_data.head(15)

            fig = px.bar(
                top_revenue.reset_index(),
                y='neighbourhood_cleansed',
                x='estimated_monthly_revenue',
                orientation='h',
                title='Top 15 Neighbourhoods by Estimated Monthly Revenue',
                labels={'estimated_monthly_revenue': 'Est. Monthly Revenue ($)', 'neighbourhood_cleansed': 'Neighbourhood'},
                color='estimated_monthly_revenue',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Price distribution by top neighborhoods
            fig = px.box(
                listings_df[listings_df['neighbourhood_cleansed'].isin(top_revenue.index[:10])].dropna(subset=['price']),
                y='neighbourhood_cleansed',
                x='price',
                title='Price Distribution in Top Revenue Neighbourhoods',
                labels={'price': 'Price ($)', 'neighbourhood_cleansed': 'Neighbourhood'}
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

        # Revenue metrics
        st.subheader("Revenue Metrics by Neighbourhood")
        display_cols = ['avg_price', 'median_price', 'listing_count', 'total_reviews', 'estimated_monthly_revenue']
        st.dataframe(
            revenue_data[display_cols].head(20).round(2).style.format({
                'avg_price': '${:.0f}',
                'median_price': '${:.0f}',
                'estimated_monthly_revenue': '${:,.0f}'
            }),
            use_container_width=True
        )

        # Price vs Reviews scatter
        if 'number_of_reviews' in listings_df.columns:
            st.subheader("Price vs Number of Reviews")
            sample_df = listings_df.dropna(subset=['price', 'number_of_reviews', 'neighbourhood_cleansed']).sample(
                min(1000, len(listings_df)), random_state=42
            )

            fig = px.scatter(
                sample_df,
                x='price',
                y='number_of_reviews',
                color='neighbourhood_cleansed',
                hover_data=['review_scores_rating'],
                title='Price vs Number of Reviews by Neighbourhood',
                labels={'price': 'Price ($)', 'number_of_reviews': 'Number of Reviews'},
                opacity=0.6
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

# Tab 4: Property Analysis
with tab4:
    st.header("Property Level Analysis")

    property_data = get_property_analysis(listings_df)

    col1, col2 = st.columns(2)

    with col1:
        # Property type distribution
        if 'by_type' in property_data:
            type_data = property_data['by_type'].head(10)

            fig = px.bar(
                type_data.reset_index(),
                y='property_type',
                x='count',
                orientation='h',
                title='Top 10 Property Types',
                labels={'count': 'Number of Listings', 'property_type': 'Property Type'},
                color='price',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Room type distribution
        if 'by_room' in property_data:
            room_data = property_data['by_room']

            fig = px.pie(
                room_data.reset_index(),
                values='count',
                names='room_type',
                title='Room Type Distribution',
                color_discrete_sequence=['#FF5A5F', '#00A699', '#FC642D']
            )
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Price by property type
        if 'by_type' in property_data:
            type_data = property_data['by_type'].head(10)

            fig = px.bar(
                type_data.reset_index(),
                y='property_type',
                x='price',
                orientation='h',
                title='Average Price by Property Type',
                labels={'price': 'Average Price ($)', 'property_type': 'Property Type'},
                color='price',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Price by bedrooms
        if 'by_bedrooms' in property_data:
            bedroom_data = property_data['by_bedrooms']

            fig = px.bar(
                bedroom_data.reset_index(),
                x='bedrooms',
                y='price',
                title='Average Price by Number of Bedrooms',
                labels={'price': 'Average Price ($)', 'bedrooms': 'Bedrooms'},
                color='price',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig, use_container_width=True)

    # Amenities analysis
    st.subheader("Top Amenities")
    amenity_counts = parse_amenities(listings_df)

    if not amenity_counts.empty:
        fig = px.bar(
            y=amenity_counts.index[:15],
            x=amenity_counts.values[:15],
            orientation='h',
            title='Top 15 Most Common Amenities',
            labels={'x': 'Number of Listings', 'y': 'Amenity'},
            color=amenity_counts.values[:15],
            color_continuous_scale='Teal'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Property type vs rating
    if 'property_type' in listings_df.columns and 'review_scores_rating' in listings_df.columns:
        st.subheader("Rating by Property Type")
        top_types = listings_df['property_type'].value_counts().head(8).index

        fig = px.box(
            listings_df[listings_df['property_type'].isin(top_types)].dropna(subset=['review_scores_rating']),
            x='property_type',
            y='review_scores_rating',
            title='Rating Distribution by Property Type',
            labels={'property_type': 'Property Type', 'review_scores_rating': 'Rating'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Data Source: [Seattle Airbnb Open Data - Kaggle](https://www.kaggle.com/datasets/airbnb/seattle)")
