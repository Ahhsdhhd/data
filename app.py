import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import (
    load_listings_data,
    load_calendar_data,
    get_host_quality_metrics,
    get_area_ratings,
    get_area_deficiencies,
    get_revenue_data,
    get_regional_revenue_data,
    get_property_analysis,
    get_amenity_premiums,
    parse_amenities
)

# Page configuration with modern branding
st.set_page_config(
    page_title="Airbnb Analytics - Seattle Case Study",
    page_icon="🏠",
    layout="wide"
)

# Custom Airbnb-inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Background */
    .main {
        background-color: #F7F7F7;
    }
    
    /* Title and Headers */
    h1, h2, h3 {
        color: #484848 !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EBEBEB;
    }
    
    /* KPI Card styling */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #EBEBEB;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04);
        text-align: center;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        margin-bottom: 12px;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
    }
    .kpi-title {
        font-size: 13px;
        color: #767676;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 32px;
        color: #FF5A5F;
        font-weight: 700;
    }
    
    /* Custom tab headers */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    
    /* Filter Section Container */
    .filter-container {
        background-color: #FFFFFF;
        border: 1px solid #EBEBEB;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# App Header with Brand Color
st.markdown("<h1 style='color:#FF5A5F; margin-bottom: 0;'>🏠 Airbnb Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 18px; color: #767676; margin-top: 0;'>Seattle Airbnb Performance & Case Study Diagnostics</p>", unsafe_allow_html=True)

# Sidebar - Dataset Configuration
st.sidebar.markdown("<h2 style='color:#FF5A5F; font-size:22px; margin-top:0;'>📁 Data Configuration</h2>", unsafe_allow_html=True)
listings_file = st.sidebar.text_input("Listings CSV path", "data/listings.csv")
calendar_file = st.sidebar.text_input("Calendar CSV path", "data/calendar.csv")

# Load data
listings_df = load_listings_data(listings_file)
calendar_df = load_calendar_data(calendar_file)

if listings_df is None:
    st.error("Could not load listings data. Please ensure the CSV file exists at the specified path.")
    st.info("Ensure listings.csv is present in the data folder.")
    st.stop()

# --- SIDEBAR MODERN FILTERS PANEL ---
st.sidebar.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='color:#484848; font-size:20px; margin-top:0;'>🔍 Modern Filters</h2>", unsafe_allow_html=True)

# 1. Price Range Filter
min_p = float(listings_df['price'].min()) if 'price' in listings_df.columns else 0.0
max_p = float(listings_df['price'].max()) if 'price' in listings_df.columns else 1000.0
selected_price_range = st.sidebar.slider(
    "Price Range ($)",
    min_value=min_p,
    max_value=min_p + 1000.0,  # Cap max price filter for better density
    value=(min_p, min_p + 500.0),
    step=10.0
)

# 2. Neighbourhood Group Filter
if 'neighbourhood_group_cleansed' in listings_df.columns:
    unique_groups = listings_df['neighbourhood_group_cleansed'].dropna().unique().tolist()
    selected_groups = st.sidebar.multiselect(
        "Macro Regions / Neighborhood Groups",
        options=sorted(unique_groups),
        placeholder="All Regions"
    )
else:
    selected_groups = []

# 3. Property Type Filter
if 'property_type' in listings_df.columns:
    unique_properties = listings_df['property_type'].dropna().unique().tolist()
    selected_properties = st.sidebar.multiselect(
        "Property Types",
        options=sorted(unique_properties),
        placeholder="All Property Types"
    )
else:
    selected_properties = []

# 4. Room Type Filter
if 'room_type' in listings_df.columns:
    unique_rooms = listings_df['room_type'].dropna().unique().tolist()
    selected_rooms = st.sidebar.multiselect(
        "Room Types",
        options=sorted(unique_rooms),
        placeholder="All Room Types"
    )
else:
    selected_rooms = []

# 5. Quick Toggles
st.sidebar.markdown("**Listing Settings**")
superhost_only = st.sidebar.toggle("Superhost Listings Only", value=False)
instant_bookable_only = st.sidebar.toggle("Instant Bookable Only", value=False)

# Apply Filters
filtered_df = listings_df.copy()

# Price range application
if 'price' in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df['price'] >= selected_price_range[0]) & 
        (filtered_df['price'] <= selected_price_range[1])
    ]

# Neighborhood group application
if selected_groups and 'neighbourhood_group_cleansed' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['neighbourhood_group_cleansed'].isin(selected_groups)]

# Property type application
if selected_properties and 'property_type' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['property_type'].isin(selected_properties)]

# Room type application
if selected_rooms and 'room_type' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['room_type'].isin(selected_rooms)]

# Superhost status application
if superhost_only and 'host_is_superhost' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['host_is_superhost'] == True]

# Instant bookable application
if instant_bookable_only and 'instant_bookable' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['instant_bookable'] == True]


# --- KPI METRIC CARDS ---
col1, col2, col3, col4, col5 = st.columns(5)

avg_price_val = filtered_df['price'].mean() if 'price' in filtered_df.columns else 0
avg_rating_val = filtered_df['review_scores_rating'].mean() if 'review_scores_rating' in filtered_df.columns else 0
superhost_pct_val = (filtered_df['host_is_superhost'].sum() / len(filtered_df) * 100) if 'host_is_superhost' in filtered_df.columns and len(filtered_df) > 0 else 0
unique_nb_val = filtered_df['neighbourhood_cleansed'].nunique() if 'neighbourhood_cleansed' in filtered_df.columns else 0

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Listings</div>
        <div class="kpi-value">{len(filtered_df):,}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Avg Price</div>
        <div class="kpi-value">${avg_price_val:.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Avg Rating</div>
        <div class="kpi-value">{avg_rating_val:.1f}/100</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Superhost %</div>
        <div class="kpi-value">{superhost_pct_val:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Neighbourhoods</div>
        <div class="kpi-value">{unique_nb_val}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Create tabs for Business Questions
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Host Quality",
    "📍 Area Ratings & Improvements",
    "💰 Revenue Analysis",
    "🏘️ Property Level Analysis"
])

# --- Tab 1: Host Quality ---
with tab1:
    st.markdown("## Host Quality Analysis")
    st.markdown("Investigating the attributes, ratings, and response behaviors of hosts to determine quality distribution.")

    metrics = get_host_quality_metrics(filtered_df)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Host response rate vs acceptance rate
        fig = go.Figure()
        if 'host_response_rate' in filtered_df.columns:
            fig.add_trace(go.Histogram(
                x=filtered_df['host_response_rate'],
                name='Response Rate',
                marker_color='#FF5A5F',
                opacity=0.75
            ))
        if 'host_acceptance_rate' in filtered_df.columns:
            fig.add_trace(go.Histogram(
                x=filtered_df['host_acceptance_rate'],
                name='Acceptance Rate',
                marker_color='#00A699',
                opacity=0.75
            ))
        fig.update_layout(
            title_text='Host Response and Acceptance Rate Distribution',
            barmode='overlay',
            xaxis_title='Percentage (%)',
            yaxis_title='Listing Count',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Host Response Time breakdown
        if 'host_response_time' in filtered_df.columns:
            response_times = filtered_df['host_response_time'].value_counts().reset_index()
            response_times.columns = ['response_time', 'count']
            fig = px.pie(
                response_times,
                values='count',
                names='response_time',
                title='Host Response Speed Profile',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig, use_container_width=True)

    # Sub-ratings Audit: Superhosts vs Regular Hosts
    st.markdown("### Superhosts vs Regular Hosts: Sub-Ratings Deep Dive")
    sub_rating_cols = {
        'review_scores_accuracy': 'Accuracy',
        'review_scores_cleanliness': 'Cleanliness',
        'review_scores_checkin': 'Check-in',
        'review_scores_communication': 'Communication',
        'review_scores_location': 'Location',
        'review_scores_value': 'Value'
    }
    
    existing_sub_cols = [c for c in sub_rating_cols.keys() if c in filtered_df.columns]
    
    if len(existing_sub_cols) > 0 and 'host_is_superhost' in filtered_df.columns:
        # Group by superhost status and average sub-ratings
        comparison = filtered_df.groupby('host_is_superhost')[existing_sub_cols].mean().reset_index()
        comparison['host_is_superhost'] = comparison['host_is_superhost'].map({True: 'Superhost', False: 'Regular Host'})
        
        # Melt dataframe for plotly grouped bar
        melted = comparison.melt(id_vars='host_is_superhost', value_vars=existing_sub_cols,
                                 var_name='Sub-Rating Type', value_name='Average Score')
        melted['Sub-Rating Type'] = melted['Sub-Rating Type'].map(sub_rating_cols)
        
        fig = px.bar(
            melted,
            x='Sub-Rating Type',
            y='Average Score',
            color='host_is_superhost',
            barmode='group',
            title='Sub-Rating Category Scores (Scale: 1-10)',
            color_discrete_sequence=['#767676', '#FF5A5F'],
            labels={'Average Score': 'Average Rating (out of 10)', 'host_is_superhost': 'Host Status'}
        )
        fig.update_layout(yaxis_range=[8.5, 10.0])  # Focus on variance at the top end
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sub-rating columns are missing to make the comparisons.")

# --- Tab 2: Area Ratings & Improvements ---
with tab2:
    st.markdown("## Area Ratings & Diagnostics")
    st.markdown("Identify which neighborhoods are underperforming and discover exactly which domains (cleanliness, accuracy, etc.) need improvement.")
    
    # 1. Deficiencies Diagnostic Table
    st.markdown("### 🔍 Improvement Diagnostics by Neighbourhood")
    st.markdown("This diagnostic table isolates neighborhoods with lower average scores and shows their lowest-performing sub-rating domain.")
    
    deficiency_df = get_area_deficiencies(filtered_df)
    if not deficiency_df.empty:
        st.dataframe(
            deficiency_df.head(15).style.background_gradient(subset=['Average Rating'], cmap='Reds_r'),
            use_container_width=True
        )
    else:
        st.info("Not enough data to calculate area deficiencies.")

    col_x, col_y = st.columns(2)
    
    with col_x:
        # Top Neighborhoods by Overall Rating
        top_nb = filtered_df.groupby('neighbourhood_cleansed')['review_scores_rating'].mean().nlargest(10).reset_index()
        fig = px.bar(
            top_nb,
            x='review_scores_rating',
            y='neighbourhood_cleansed',
            orientation='h',
            title='Top 10 Neighbourhoods by Rating',
            color_discrete_sequence=['#00A699'],
            labels={'review_scores_rating': 'Rating (out of 100)', 'neighbourhood_cleansed': 'Neighbourhood'}
        )
        fig.update_layout(xaxis_range=[80, 100])
        st.plotly_chart(fig, use_container_width=True)
        
    with col_y:
        # Bottom Neighborhoods by Overall Rating
        bottom_nb = filtered_df.groupby('neighbourhood_cleansed')['review_scores_rating'].mean().nsmallest(10).reset_index()
        fig = px.bar(
            bottom_nb,
            x='review_scores_rating',
            y='neighbourhood_cleansed',
            orientation='h',
            title='Bottom 10 Neighbourhoods by Rating',
            color_discrete_sequence=['#FF5A5F'],
            labels={'review_scores_rating': 'Rating (out of 100)', 'neighbourhood_cleansed': 'Neighbourhood'}
        )
        fig.update_layout(xaxis_range=[80, 100])
        st.plotly_chart(fig, use_container_width=True)

    # Mapbox Ratings
    if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
        st.markdown("### Geographic Rating Hotspots")
        fig = px.scatter_mapbox(
            filtered_df.dropna(subset=['latitude', 'longitude', 'review_scores_rating']),
            lat='latitude',
            lon='longitude',
            color='review_scores_rating',
            size='price' if 'price' in filtered_df.columns else None,
            color_continuous_scale='RdYlGn',
            size_max=12,
            zoom=11,
            mapbox_style='carto-positron',
            title='Seattle Airbnb Map Colored by Rating (Bubble Size = Price)',
            hover_data=['neighbourhood_cleansed', 'price', 'review_scores_rating']
        )
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

# --- Tab 3: Revenue Analysis ---
with tab3:
    st.markdown("## Regional Revenue Performance")
    st.markdown("Analyzing occupancy proxy (estimated monthly revenue) across macro regions and local neighborhoods.")

    # Macro level revenue
    macro_revenue = get_regional_revenue_data(filtered_df)
    
    if not macro_revenue.empty:
        col_rev_1, col_rev_2 = st.columns([3, 2])
        
        with col_rev_1:
            fig = px.bar(
                macro_revenue.reset_index(),
                x='estimated_monthly_revenue',
                y=macro_revenue.index,
                orientation='h',
                title='Estimated Monthly Revenue by Macro Region (Neighborhood Groups)',
                color='estimated_monthly_revenue',
                color_continuous_scale='Plasma',
                labels={'estimated_monthly_revenue': 'Est. Monthly Revenue ($)', 'neighbourhood_group_cleansed': 'Region'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col_rev_2:
            st.markdown("### Macro Region Summary Table")
            st.dataframe(
                macro_revenue[['listing_count', 'avg_price', 'estimated_monthly_revenue']].style.format({
                    'avg_price': '${:.0f}',
                    'estimated_monthly_revenue': '${:,.0f}'
                }),
                use_container_width=True
            )

        # Neighborhood level details
        st.markdown("### Top 15 Micro-Neighbourhoods by Revenue")
        micro_revenue = get_revenue_data(filtered_df).head(15)
        
        fig = px.bar(
            micro_revenue.reset_index(),
            x='neighbourhood_cleansed',
            y='estimated_monthly_revenue',
            title='Top 15 Micro-Neighbourhoods by Estimated Monthly Revenue',
            color_discrete_sequence=['#FF5A5F'],
            labels={'estimated_monthly_revenue': 'Est. Monthly Revenue ($)', 'neighbourhood_cleansed': 'Neighbourhood'}
        )
        st.plotly_chart(fig, use_container_width=True)

# --- Tab 4: Property Level Analysis ---
with tab4:
    st.markdown("## Property & Configuration Deep Dive")
    st.markdown("Understanding spatial property types, configurations (bedrooms/bathrooms), and the pricing premiums of common amenities.")
    
    prop_data = get_property_analysis(filtered_df)
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        if 'by_type' in prop_data:
            fig = px.bar(
                prop_data['by_type'].reset_index().head(10),
                x='count',
                y='property_type',
                orientation='h',
                title='Top 10 Property Types by Popularity',
                color='price',
                color_continuous_scale='Viridis',
                labels={'count': 'Number of Listings', 'property_type': 'Property Type'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_p2:
        if 'by_room' in prop_data:
            fig = px.pie(
                prop_data['by_room'].reset_index(),
                values='count',
                names='room_type',
                title='Room Type Split',
                color_discrete_sequence=['#FF5A5F', '#00A699', '#FC642D']
            )
            st.plotly_chart(fig, use_container_width=True)

    # Price boxplots by Bedrooms
    if 'bedrooms' in filtered_df.columns:
        st.markdown("### Pricing Distributions by Bedroom Configuration")
        fig = px.box(
            filtered_df[filtered_df['bedrooms'] <= 5].dropna(subset=['price', 'bedrooms']),
            x='bedrooms',
            y='price',
            color='bedrooms',
            title='Price Spread by Number of Bedrooms (Capped at 5)',
            labels={'price': 'Price ($)', 'bedrooms': 'Bedrooms'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Amenity Impact analysis
    st.markdown("### 💎 Amenity Price & Rating Premiums")
    st.markdown("Which amenities allow hosts to charge higher rates or obtain higher scores?")
    
    amenity_prem = get_amenity_premiums(filtered_df)
    if not amenity_prem.empty:
        col_am1, col_am2 = st.columns([3, 2])
        
        with col_am1:
            fig = px.bar(
                amenity_prem,
                x='Price Premium ($)',
                y='Amenity',
                orientation='h',
                title='Estimated Price Premium for Having Amenity ($)',
                color='Price Premium ($)',
                color_continuous_scale='Tealgrn'
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col_am2:
            st.dataframe(
                amenity_prem[['Amenity', 'Price Premium ($)', 'Rating Premium']].style.format({
                    'Price Premium ($)': '${:+.2f}',
                    'Rating Premium': '{:+.2f}'
                }),
                use_container_width=True
            )
    else:
        st.info("Amenities parsing not supported or dataset lacks the required format.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #767676;'>Data Source: Seattle Airbnb Open Data | Built for Airbnb Case Study Analysis</p>", unsafe_allow_html=True)
