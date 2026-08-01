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
    get_calendar_occupancy,
    get_real_revenue_by_neighbourhood,
    get_seasonal_trends,
    get_revenue_data,
    get_regional_revenue_data,
    get_price_vs_listings,
    get_property_analysis,
    get_amenity_premiums,
    parse_amenities,
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Airbnb Analytics — Seattle Case Study",
    page_icon="🏠",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
  .main { background-color: #F7F7F7; }
  h1, h2, h3 { color: #484848 !important; font-weight: 700 !important; }
  section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EBEBEB;
  }
  /* KPI Cards */
  .kpi-card {
    background: #FFFFFF;
    border: 1px solid #EBEBEB;
    border-radius: 16px;
    padding: 22px 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.05);
    text-align: center;
    transition: transform .18s ease, box-shadow .18s ease;
    margin-bottom: 12px;
  }
  .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 14px 28px rgba(0,0,0,0.09); }
  .kpi-title { font-size:12px; color:#767676; text-transform:uppercase; letter-spacing:.9px; font-weight:600; margin-bottom:6px; }
  .kpi-value { font-size:30px; color:#FF5A5F; font-weight:700; }
  .kpi-sub   { font-size:12px; color:#00A699; margin-top:4px; }
  /* Section badge */
  .section-badge {
    display:inline-block; background:#FFF0F0; color:#FF5A5F;
    border-radius:8px; padding:4px 12px; font-size:13px;
    font-weight:600; margin-bottom:8px;
  }
  button[data-baseweb="tab"] { font-weight:600 !important; font-size:15px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("<h1 style='color:#FF5A5F;margin-bottom:0'>🏠 Airbnb Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size:17px;color:#767676;margin-top:0'>Seattle Airbnb Case Study — Host Quality · Area Diagnostics · Revenue · Property Analysis</p>", unsafe_allow_html=True)

# ─── Sidebar: Data Configuration ──────────────────────────────────────────────
st.sidebar.markdown("<h2 style='color:#FF5A5F;font-size:20px;margin-top:0'>📁 Data</h2>", unsafe_allow_html=True)
listings_file = st.sidebar.text_input("Listings CSV", "data/listings.csv")
calendar_file = st.sidebar.text_input("Calendar CSV", "data/calendar.csv")

with st.spinner("Loading data…"):
    listings_df = load_listings_data(listings_file)
    calendar_df = load_calendar_data(calendar_file)

if listings_df is None:
    st.error("❌ Could not load listings.csv. Check the path in the sidebar.")
    st.stop()

cal_loaded = calendar_df is not None
st.sidebar.success(f"✅ {len(listings_df):,} listings loaded")
if cal_loaded:
    st.sidebar.success(f"✅ {len(calendar_df):,} calendar rows loaded")
else:
    st.sidebar.warning("⚠️ calendar.csv not found — revenue will use proxy estimates")

# ─── Sidebar: Modern Filters ───────────────────────────────────────────────────
st.sidebar.markdown("<hr style='margin:14px 0'>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='color:#484848;font-size:19px;margin-top:0'>🔍 Filters</h2>", unsafe_allow_html=True)

# Price range
p_min = float(listings_df['price'].min()) if 'price' in listings_df.columns else 0.0
price_range = st.sidebar.slider("Nightly Price ($)", min_value=p_min, max_value=p_min + 1000.0,
                                value=(p_min, p_min + 500.0), step=10.0)

# Neighbourhood group
if 'neighbourhood_group_cleansed' in listings_df.columns:
    nb_groups = sorted(listings_df['neighbourhood_group_cleansed'].dropna().unique())
    sel_groups = st.sidebar.multiselect("Macro Region", nb_groups, placeholder="All regions")
else:
    sel_groups = []

# Property type
if 'property_type' in listings_df.columns:
    prop_types = sorted(listings_df['property_type'].dropna().unique())
    sel_props = st.sidebar.multiselect("Property Type", prop_types, placeholder="All types")
else:
    sel_props = []

# Room type
if 'room_type' in listings_df.columns:
    room_types = sorted(listings_df['room_type'].dropna().unique())
    sel_rooms = st.sidebar.multiselect("Room Type", room_types, placeholder="All room types")
else:
    sel_rooms = []

# Neighbourhood (micro)
if 'neighbourhood_cleansed' in listings_df.columns:
    nb_list = sorted(listings_df['neighbourhood_cleansed'].dropna().unique())
    sel_nb = st.sidebar.multiselect("Neighbourhood", nb_list, placeholder="All neighbourhoods")
else:
    sel_nb = []

# Bedrooms
if 'bedrooms' in listings_df.columns:
    max_bed = int(listings_df['bedrooms'].max()) if listings_df['bedrooms'].max() <= 10 else 10
    sel_beds = st.sidebar.slider("Max Bedrooms", 1, max_bed, max_bed)
else:
    sel_beds = 10

st.sidebar.markdown("**Quick Toggles**")
superhost_only      = st.sidebar.toggle("Superhosts only",       value=False)
instant_book_only   = st.sidebar.toggle("Instant bookable only", value=False)

# ─── Apply Filters ─────────────────────────────────────────────────────────────
fdf = listings_df.copy()
if 'price' in fdf.columns:
    fdf = fdf[(fdf['price'] >= price_range[0]) & (fdf['price'] <= price_range[1])]
if sel_groups and 'neighbourhood_group_cleansed' in fdf.columns:
    fdf = fdf[fdf['neighbourhood_group_cleansed'].isin(sel_groups)]
if sel_props and 'property_type' in fdf.columns:
    fdf = fdf[fdf['property_type'].isin(sel_props)]
if sel_rooms and 'room_type' in fdf.columns:
    fdf = fdf[fdf['room_type'].isin(sel_rooms)]
if sel_nb and 'neighbourhood_cleansed' in fdf.columns:
    fdf = fdf[fdf['neighbourhood_cleansed'].isin(sel_nb)]
if 'bedrooms' in fdf.columns:
    fdf = fdf[fdf['bedrooms'] <= sel_beds]
if superhost_only and 'host_is_superhost' in fdf.columns:
    fdf = fdf[fdf['host_is_superhost'] == True]
if instant_book_only and 'instant_bookable' in fdf.columns:
    fdf = fdf[fdf['instant_bookable'] == True]

st.sidebar.caption(f"**{len(fdf):,}** listings match current filters")

# ─── KPI Cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

avg_price  = fdf['price'].mean()                        if 'price'                in fdf.columns and len(fdf) > 0 else 0
avg_rating = fdf['review_scores_rating'].mean()         if 'review_scores_rating' in fdf.columns and len(fdf) > 0 else 0
sh_pct     = fdf['host_is_superhost'].sum() / len(fdf) * 100 if 'host_is_superhost' in fdf.columns and len(fdf) > 0 else 0
nb_count   = fdf['neighbourhood_cleansed'].nunique()    if 'neighbourhood_cleansed' in fdf.columns else 0

# Real occupancy from calendar if available
if cal_loaded and 'booked' in calendar_df.columns:
    occ_global = calendar_df['booked'].mean() * 100
    occ_display = f"{occ_global:.1f}%"
    occ_sub = "real from calendar"
else:
    occ_display = "N/A"
    occ_sub = "calendar not loaded"

for col, title, val, sub in [
    (c1, "Total Listings",   f"{len(fdf):,}",        f"of {len(listings_df):,} total"),
    (c2, "Avg Nightly Price",f"${avg_price:.0f}",    "per listing"),
    (c3, "Avg Rating",       f"{avg_rating:.1f}",    "out of 100"),
    (c4, "Superhost %",      f"{sh_pct:.1f}%",       f"{int(fdf['host_is_superhost'].sum()) if 'host_is_superhost' in fdf.columns else 0} hosts"),
    (c5, "Occupancy Rate",   occ_display,            occ_sub),
]:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "👤 Q1 · Host Quality",
    "📍 Q2 · Area Ratings & Improvements",
    "💰 Q3 · Revenue Analysis",
    "🏘️ Q4 · Property Level Analysis",
])

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 1 — HOST QUALITY
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<div class='section-badge'>Business Question 1</div>", unsafe_allow_html=True)
    st.markdown("## How is our Host Quality looking?")
    st.markdown("Examining response behaviours, acceptance rates, Superhost distribution, and per-category rating scores.")

    metrics = get_host_quality_metrics(fdf)

    # Row 1: response rate + response speed
    col_a, col_b = st.columns(2)

    with col_a:
        fig = go.Figure()
        if 'host_response_rate' in fdf.columns:
            fig.add_trace(go.Histogram(x=fdf['host_response_rate'].dropna(),
                                       name='Response Rate', marker_color='#FF5A5F', opacity=0.75))
        if 'host_acceptance_rate' in fdf.columns:
            fig.add_trace(go.Histogram(x=fdf['host_acceptance_rate'].dropna(),
                                       name='Acceptance Rate', marker_color='#00A699', opacity=0.75))
        fig.update_layout(title='Response & Acceptance Rate Distributions',
                          barmode='overlay', xaxis_title='Rate (%)', yaxis_title='# Listings',
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                          legend=dict(orientation='h', y=1.12))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if 'host_response_time' in fdf.columns:
            rt = fdf['host_response_time'].value_counts().reset_index()
            rt.columns = ['response_time', 'count']
            fig = px.pie(rt, values='count', names='response_time',
                         title='How Fast Do Hosts Respond?',
                         color_discrete_sequence=['#FF5A5F','#00A699','#FC642D','#484848'])
            st.plotly_chart(fig, use_container_width=True)

    # Row 2: Superhost pie + rating vs superhost box
    col_c, col_d = st.columns(2)

    with col_c:
        if 'host_is_superhost' in fdf.columns:
            sh_data = fdf['host_is_superhost'].value_counts().reset_index()
            sh_data.columns = ['status', 'count']
            sh_data['status'] = sh_data['status'].map({True: 'Superhost', False: 'Regular Host'})
            fig = px.pie(sh_data, values='count', names='status',
                         title='Superhost vs Regular Host Split',
                         color_discrete_sequence=['#FF5A5F','#EBEBEB'])
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        if 'host_is_superhost' in fdf.columns and 'review_scores_rating' in fdf.columns:
            tmp = fdf.dropna(subset=['review_scores_rating']).copy()
            tmp['Host Type'] = tmp['host_is_superhost'].map({True: 'Superhost', False: 'Regular Host'})
            fig = px.box(tmp, x='Host Type', y='review_scores_rating',
                         color='Host Type',
                         color_discrete_map={'Superhost': '#FF5A5F', 'Regular Host': '#767676'},
                         title='Overall Rating Distribution by Host Type',
                         labels={'review_scores_rating': 'Rating (out of 100)'})
            st.plotly_chart(fig, use_container_width=True)

    # Row 3: Sub-ratings deep dive
    st.markdown("### 🔬 Sub-Rating Deep Dive: Superhost vs Regular Host")
    sub_cols_map = {
        'review_scores_accuracy': 'Accuracy',
        'review_scores_cleanliness': 'Cleanliness',
        'review_scores_checkin': 'Check-in',
        'review_scores_communication': 'Communication',
        'review_scores_location': 'Location',
        'review_scores_value': 'Value',
    }
    exist_sub = [c for c in sub_cols_map if c in fdf.columns]
    if exist_sub and 'host_is_superhost' in fdf.columns:
        cmp = fdf.groupby('host_is_superhost')[exist_sub].mean().reset_index()
        cmp['host_is_superhost'] = cmp['host_is_superhost'].map({True: 'Superhost', False: 'Regular Host'})
        melted = cmp.melt(id_vars='host_is_superhost', value_vars=exist_sub,
                          var_name='Category', value_name='Score')
        melted['Category'] = melted['Category'].map(sub_cols_map)
        fig = px.bar(melted, x='Category', y='Score', color='host_is_superhost',
                     barmode='group',
                     color_discrete_map={'Superhost': '#FF5A5F', 'Regular Host': '#767676'},
                     title='Average Sub-Rating Scores by Host Type (scale: 1–10)',
                     labels={'Score': 'Avg Score (/10)', 'host_is_superhost': 'Host Type'})
        fig.update_layout(yaxis_range=[8.0, 10.0])
        st.plotly_chart(fig, use_container_width=True)

    # Summary KPI row
    st.markdown("### Summary")
    m1, m2, m3, m4 = st.columns(4)
    for col, label, val in [
        (m1, "Avg Response Rate",   f"{metrics['avg_response_rate']:.1f}%"),
        (m2, "Avg Acceptance Rate", f"{metrics['avg_acceptance_rate']:.1f}%"),
        (m3, "Superhost %",         f"{metrics['superhost_pct']:.1f}%"),
        (m4, "Avg Host Rating",     f"{metrics['avg_host_rating']:.1f}/100"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-title">{label}</div>
              <div class="kpi-value" style="font-size:22px">{val}</div>
            </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 2 — AREA RATINGS & IMPROVEMENTS
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div class='section-badge'>Business Question 2</div>", unsafe_allow_html=True)
    st.markdown("## Which areas have bad ratings & what do they need to improve?")

    # Diagnostic table
    st.markdown("### 🔍 Neighbourhood Deficiency Diagnostic")
    st.caption("Shows each neighbourhood's weakest sub-rating category — the direct improvement lever.")
    def_df = get_area_deficiencies(fdf)
    if not def_df.empty:
        st.dataframe(
            def_df.head(20).style.background_gradient(subset=['Avg Rating (100)'], cmap='Reds_r')
                                  .format({'Avg Rating (100)': '{:.1f}', 'Deficiency Score (/10)': '{:.2f}'}),
            use_container_width=True, height=420
        )
    else:
        st.info("Not enough data for deficiency diagnostics with current filters.")

    # Top vs Bottom bar charts
    col_x, col_y = st.columns(2)
    with col_x:
        top10 = fdf.groupby('neighbourhood_cleansed')['review_scores_rating'].mean().nlargest(10).reset_index()
        fig = px.bar(top10, x='review_scores_rating', y='neighbourhood_cleansed', orientation='h',
                     title='✅ Top 10 Highest-Rated Neighbourhoods',
                     color_discrete_sequence=['#00A699'],
                     labels={'review_scores_rating': 'Avg Rating (100)', 'neighbourhood_cleansed': ''})
        fig.update_layout(xaxis_range=[85, 100])
        st.plotly_chart(fig, use_container_width=True)

    with col_y:
        bot10 = fdf.groupby('neighbourhood_cleansed')['review_scores_rating'].mean().nsmallest(10).reset_index()
        fig = px.bar(bot10, x='review_scores_rating', y='neighbourhood_cleansed', orientation='h',
                     title='⚠️ Bottom 10 Lowest-Rated Neighbourhoods',
                     color_discrete_sequence=['#FF5A5F'],
                     labels={'review_scores_rating': 'Avg Rating (100)', 'neighbourhood_cleansed': ''})
        fig.update_layout(xaxis_range=[60, 100])
        st.plotly_chart(fig, use_container_width=True)

    # Sub-ratings heatmap by neighbourhood
    st.markdown("### 🌡️ Sub-Rating Heatmap by Neighbourhood (Bottom 15)")
    sub_map = {
        'review_scores_cleanliness': 'Cleanliness',
        'review_scores_accuracy': 'Accuracy',
        'review_scores_checkin': 'Check-in',
        'review_scores_communication': 'Communication',
        'review_scores_location': 'Location',
        'review_scores_value': 'Value',
    }
    exist_sub2 = [c for c in sub_map if c in fdf.columns]
    if exist_sub2 and 'neighbourhood_cleansed' in fdf.columns:
        heat = fdf.groupby('neighbourhood_cleansed')[exist_sub2].mean()
        heat = heat.loc[heat['review_scores_cleanliness'].nsmallest(15).index] if 'review_scores_cleanliness' in heat.columns else heat.head(15)
        heat.columns = [sub_map[c] for c in heat.columns]
        fig = px.imshow(heat, color_continuous_scale='RdYlGn', aspect='auto',
                        title='Sub-Rating Heatmap (bottom 15 neighbourhoods by cleanliness)',
                        labels=dict(color='Score /10'))
        st.plotly_chart(fig, use_container_width=True)

    # Map
    if 'latitude' in fdf.columns and 'longitude' in fdf.columns:
        st.markdown("### 🗺️ Geographic Rating Heatmap")
        map_df = fdf.dropna(subset=['latitude', 'longitude', 'review_scores_rating'])
        fig = px.scatter_mapbox(map_df, lat='latitude', lon='longitude',
                                color='review_scores_rating',
                                size='price' if 'price' in map_df.columns else None,
                                color_continuous_scale='RdYlGn', size_max=12,
                                zoom=11, mapbox_style='carto-positron',
                                title='Ratings by Location (bubble = price)',
                                hover_data=['neighbourhood_cleansed', 'price', 'review_scores_rating'])
        fig.update_layout(height=520)
        st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 3 — REVENUE ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-badge'>Business Question 3</div>", unsafe_allow_html=True)
    st.markdown("## Which regions generate good revenue?")

    # ── 3A: Real occupancy from calendar ──────────────────────────────────────
    if cal_loaded:
        st.markdown("### 📅 Real Occupancy Rate by Neighbourhood (from calendar.csv)")
        st.caption("Occupancy = booked nights ÷ total tracked nights per neighbourhood")
        occ_df = get_calendar_occupancy(calendar_df, fdf)
        if not occ_df.empty:
            c_occ1, c_occ2 = st.columns([3, 2])
            with c_occ1:
                occ_plot = occ_df.reset_index().head(20)
                fig = px.bar(occ_plot, x='occupancy_rate_pct', y='neighbourhood',
                             orientation='h', color='occupancy_rate_pct',
                             color_continuous_scale='Teal',
                             title='Top 20 Neighbourhoods by Real Occupancy Rate (%)',
                             labels={'occupancy_rate_pct': 'Occupancy (%)', 'neighbourhood': ''})
                st.plotly_chart(fig, use_container_width=True)
            with c_occ2:
                st.markdown("**Occupancy Summary**")
                st.dataframe(occ_df.head(15).style.format({
                    'occupancy_rate_pct': '{:.1f}%',
                    'booked_nights': '{:,}',
                    'total_nights': '{:,}',
                }), use_container_width=True)

        # ── 3B: Real Revenue from calendar ────────────────────────────────────
        st.markdown("### 💵 Real Revenue by Neighbourhood (booked nights × price)")
        real_rev = get_real_revenue_by_neighbourhood(calendar_df, fdf)
        if not real_rev.empty:
            c_r1, c_r2 = st.columns([3, 2])
            with c_r1:
                fig = px.bar(real_rev.reset_index().head(15),
                             x='total_revenue', y='neighbourhood',
                             orientation='h', color='total_revenue',
                             color_continuous_scale='Plasma',
                             title='Top 15 Neighbourhoods by Total Calendar Revenue ($)',
                             labels={'total_revenue': 'Total Revenue ($)', 'neighbourhood': ''})
                st.plotly_chart(fig, use_container_width=True)
            with c_r2:
                st.markdown("**Revenue Detail Table**")
                st.dataframe(real_rev.head(15).style.format({
                    'total_revenue': '${:,.0f}',
                    'avg_nightly_price': '${:.2f}',
                    'booked_nights': '{:,}',
                }), use_container_width=True)

        # ── 3C: Seasonal Trends ────────────────────────────────────────────────
        st.markdown("### 📈 Seasonal Occupancy & Price Trends")
        seasonal = get_seasonal_trends(calendar_df)
        if not seasonal.empty:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                fig = px.line(seasonal.reset_index(), x='month', y='occupancy_rate_pct',
                              markers=True, title='Monthly Occupancy Rate (%)',
                              color_discrete_sequence=['#FF5A5F'],
                              labels={'month': 'Month', 'occupancy_rate_pct': 'Occupancy (%)'})
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            with col_s2:
                fig = px.line(seasonal.reset_index(), x='month', y='avg_price',
                              markers=True, title='Monthly Average Nightly Price ($)',
                              color_discrete_sequence=['#00A699'],
                              labels={'month': 'Month', 'avg_price': 'Avg Price ($)'})
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("📂 **calendar.csv not loaded** — showing proxy revenue estimates based on listings data.")

    # ── 3D: Proxy revenue (always shown as reference) ─────────────────────────
    st.markdown("### 🗺️ Macro Region Revenue (Proxy: Avg Price × Reviews/Month)")
    macro_rev = get_regional_revenue_data(fdf)
    if not macro_rev.empty:
        c_m1, c_m2 = st.columns([3, 2])
        with c_m1:
            fig = px.bar(macro_rev.reset_index(), x='estimated_monthly_revenue', y=macro_rev.index,
                         orientation='h', color='estimated_monthly_revenue',
                         color_continuous_scale='Viridis',
                         title='Estimated Monthly Revenue by Macro Region',
                         labels={'estimated_monthly_revenue': 'Est. Revenue ($)'})
            st.plotly_chart(fig, use_container_width=True)
        with c_m2:
            st.dataframe(macro_rev[['listing_count', 'avg_price', 'estimated_monthly_revenue']]
                         .style.format({'avg_price': '${:.0f}', 'estimated_monthly_revenue': '${:,.0f}'}),
                         use_container_width=True)

    # ── 3E: Price vs listing count scatter ────────────────────────────────────
    st.markdown("### 🎯 What Drives Revenue? Avg Price vs Listing Volume")
    st.caption("High-value regions sit top-right (high price + many listings). Bubble size = avg rating.")
    scatter_df = get_price_vs_listings(fdf)
    if not scatter_df.empty:
        fig = px.scatter(scatter_df, x='listing_count', y='avg_price',
                         size='avg_rating', color='avg_rating',
                         color_continuous_scale='RdYlGn',
                         hover_name='neighbourhood_cleansed',
                         title='Avg Price vs Listing Count per Neighbourhood',
                         labels={'listing_count': 'Number of Listings',
                                 'avg_price': 'Avg Nightly Price ($)',
                                 'avg_rating': 'Avg Rating'})
        fig.update_layout(height=480)
        st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 4 — PROPERTY LEVEL ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("<div class='section-badge'>Business Question 4</div>", unsafe_allow_html=True)
    st.markdown("## Property Level Analysis")
    st.markdown("How property type, room type, bedroom/bathroom count, and amenities affect price and guest ratings.")

    prop = get_property_analysis(fdf)

    # ── 4A: Property Type & Room Type ─────────────────────────────────────────
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if 'by_type' in prop:
            fig = px.bar(prop['by_type'].reset_index().head(10),
                         x='count', y='property_type', orientation='h',
                         color='price', color_continuous_scale='Viridis',
                         title='Top 10 Property Types (color = avg price)',
                         labels={'count': '# Listings', 'property_type': ''})
            st.plotly_chart(fig, use_container_width=True)
    with col_p2:
        if 'by_room' in prop:
            fig = px.pie(prop['by_room'].reset_index(), values='count', names='room_type',
                         title='Room Type Distribution',
                         color_discrete_sequence=['#FF5A5F', '#00A699', '#FC642D'])
            st.plotly_chart(fig, use_container_width=True)

    # ── 4B: Rating by Property Type ───────────────────────────────────────────
    st.markdown("### ⭐ Rating Distribution by Property Type")
    if 'property_type' in fdf.columns and 'review_scores_rating' in fdf.columns:
        top_types = fdf['property_type'].value_counts().head(8).index
        fig = px.box(fdf[fdf['property_type'].isin(top_types)].dropna(subset=['review_scores_rating']),
                     x='property_type', y='review_scores_rating', color='property_type',
                     title='Rating Spread Across Top 8 Property Types',
                     labels={'property_type': 'Property Type', 'review_scores_rating': 'Rating (100)'})
        fig.update_layout(showlegend=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    # ── 4C: Bedrooms & Bathrooms vs Price ─────────────────────────────────────
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if 'bedrooms' in fdf.columns:
            bed_df = fdf[fdf['bedrooms'] <= 6].dropna(subset=['price', 'bedrooms'])
            fig = px.box(bed_df, x='bedrooms', y='price', color='bedrooms',
                         title='Price Spread by Number of Bedrooms',
                         labels={'price': 'Nightly Price ($)', 'bedrooms': 'Bedrooms'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_b2:
        if 'by_bathrooms' in prop:
            bath_data = prop['by_bathrooms'].reset_index()
            bath_data = bath_data[bath_data['bathrooms'] <= 5]
            fig = px.bar(bath_data, x='bathrooms', y='price',
                         color='price', color_continuous_scale='Blues',
                         title='Avg Nightly Price by Number of Bathrooms',
                         labels={'price': 'Avg Price ($)', 'bathrooms': 'Bathrooms'})
            st.plotly_chart(fig, use_container_width=True)

    # ── 4D: Amenity Premium ───────────────────────────────────────────────────
    st.markdown("### 💎 Amenity Price & Rating Premiums")
    st.caption("Difference in average price/rating between listings WITH vs WITHOUT each amenity.")
    amenity_df = get_amenity_premiums(fdf)
    if not amenity_df.empty:
        col_am1, col_am2 = st.columns([3, 2])
        with col_am1:
            fig = px.bar(amenity_df, x='Price Premium ($)', y='Amenity', orientation='h',
                         color='Price Premium ($)', color_continuous_scale='Teal',
                         title='Amenity Price Premium — How Much Extra Can Hosts Charge?')
            st.plotly_chart(fig, use_container_width=True)
        with col_am2:
            st.markdown("**Detailed Breakdown**")
            st.dataframe(amenity_df.style.format({
                'Avg Price With ($)':    '${:.0f}',
                'Avg Price Without ($)': '${:.0f}',
                'Price Premium ($)':     '${:+.0f}',
                'Rating Premium':        '{:+.2f}',
            }), use_container_width=True)

    # ── 4E: Top Amenities by Count ────────────────────────────────────────────
    st.markdown("### 📋 Most Common Amenities")
    amenity_counts = parse_amenities(fdf)
    if not amenity_counts.empty:
        fig = px.bar(y=amenity_counts.index[:15], x=amenity_counts.values[:15],
                     orientation='h', color=amenity_counts.values[:15],
                     color_continuous_scale='Tealgrn',
                     title='Top 15 Most Listed Amenities',
                     labels={'x': '# Listings', 'y': 'Amenity'})
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<p style='text-align:center;color:#767676;font-size:13px'>Data: Seattle Airbnb Open Data (Kaggle) · Built for Airbnb Case Study Analysis</p>",
            unsafe_allow_html=True)
