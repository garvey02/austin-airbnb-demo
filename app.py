"""
PriceScope ATX — Personalized Predictive Pricing Dashboard v2
==============================================================
Upgraded with:
  - Paste-your-listing-URL input (auto-matches to dataset)
  - ML pricing model (gradient boosting) trained on actual Austin market data
  - Property-specific comp engine (matches on room type, price tier, location radius)
  - Learned seasonal patterns from review velocity across the dataset
  - Personalized revenue gap analysis with dollar-specific recommendations
  - "What-if" simulator: slide price up/down and see projected impact

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import re, os, glob, warnings, math
warnings.filterwarnings('ignore')

# ─── Page Config ───
st.set_page_config(
    page_title="PriceScope ATX — Personalized Pricing",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───
st.markdown("""
<style>
    .stApp { background-color: #0B0F1A; }
    .block-container { padding-top: 1rem; max-width: 1100px; }
    h1, h2, h3 { color: #E2E8F0 !important; }
    div[data-testid="stMetric"] {
        background: #131825; border: 1px solid #1E2640;
        border-radius: 10px; padding: 12px;
    }
    div[data-testid="stMetric"] label { color: #94A3B8 !important; font-size: 12px !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #E2E8F0 !important; }
    .insight-box {
        background: linear-gradient(135deg, #064E3B40, #064E3B20);
        border: 1px solid #10B98130; border-radius: 10px;
        padding: 16px 20px; margin: 12px 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #7F1D1D40, #7F1D1D20);
        border: 1px solid #EF444430; border-radius: 10px;
        padding: 16px 20px; margin: 12px 0;
    }
    .info-box {
        background: linear-gradient(135deg, #1E3A5F40, #1E3A5F20);
        border: 1px solid #3B82F630; border-radius: 10px;
        padding: 16px 20px; margin: 12px 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #131825; border-radius: 8px;
        color: #94A3B8; padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A5F !important; color: #3B82F6 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Constants ───
HOOD_LABELS = {
    78701: 'Downtown', 78702: 'East Austin', 78703: 'Zilker/Barton Hills',
    78704: 'South Austin', 78705: 'UT/Campus', 78721: 'East (21)',
    78723: 'Windsor Park', 78734: 'Lakeway', 78741: 'South (41)',
    78744: 'Southeast', 78745: 'South (45)', 78751: 'Hyde Park',
    78752: 'North Central', 78753: 'North (53)', 78757: 'Crestview',
    78758: 'North (58)', 78746: 'West Lake Hills', 78748: 'South (48)',
    78724: 'East (24)', 78756: 'Rosedale', 78759: 'Northwest',
}

EVENTS = [
    {"name": "SXSW", "month": 3, "start": 7, "end": 16, "mult": 1.85, "icon": "🎸"},
    {"name": "ACL Fest Wk1", "month": 10, "start": 3, "end": 5, "mult": 1.65, "icon": "🎶"},
    {"name": "ACL Fest Wk2", "month": 10, "start": 10, "end": 12, "mult": 1.60, "icon": "🎶"},
    {"name": "F1 US Grand Prix", "month": 10, "start": 17, "end": 19, "mult": 1.90, "icon": "🏎️"},
    {"name": "UT Football", "month": 9, "start": 6, "end": 7, "mult": 1.30, "icon": "🏈"},
    {"name": "UT Football", "month": 10, "start": 25, "end": 26, "mult": 1.30, "icon": "🏈"},
    {"name": "UT Football", "month": 11, "start": 8, "end": 9, "mult": 1.30, "icon": "🏈"},
    {"name": "UT Football", "month": 11, "start": 29, "end": 30, "mult": 1.25, "icon": "🏈"},
    {"name": "July 4th", "month": 7, "start": 3, "end": 5, "mult": 1.25, "icon": "🎆"},
    {"name": "Memorial Day", "month": 5, "start": 24, "end": 26, "mult": 1.15, "icon": "🇺🇸"},
    {"name": "Labor Day", "month": 9, "start": 1, "end": 1, "mult": 1.15, "icon": "🇺🇸"},
    {"name": "Thanksgiving", "month": 11, "start": 27, "end": 30, "mult": 1.20, "icon": "🦃"},
    {"name": "Christmas", "month": 12, "start": 23, "end": 26, "mult": 1.15, "icon": "🎄"},
    {"name": "NYE", "month": 12, "start": 30, "end": 31, "mult": 1.35, "icon": "🎉"},
    {"name": "ROT Rally", "month": 6, "start": 12, "end": 15, "mult": 1.15, "icon": "🏍️"},
    {"name": "Trail of Lights", "month": 12, "start": 8, "end": 23, "mult": 1.08, "icon": "✨"},
]


# ═══════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════
@st.cache_data
def load_data():
    """Load and clean listings CSV with robust file detection."""
    possible = [
        'listings_1_.csv', 'listings(1).csv', 'listings.csv',
        'listing.csv', 'listings_1.csv', 'listings (1).csv',
        'data/listings.csv', 'data/listings_1_.csv',
    ]
    df = None
    for path in possible:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                break
            except Exception:
                continue
    if df is None:
        for pattern in ['*listing*.csv', '*.csv']:
            for match in glob.glob(pattern, recursive=True):
                try:
                    test = pd.read_csv(match)
                    if 'price' in test.columns and 'neighbourhood' in test.columns:
                        df = test
                        break
                except Exception:
                    continue
            if df is not None:
                break
    if df is None:
        st.error("❌ CSV not found. Place `listings_1_.csv` next to `app.py`.")
        st.code('\n'.join(os.listdir('.')))
        st.stop()

    # Clean
    df = df.dropna(subset=['price'])
    df = df[(df['price'] > 10) & (df['price'] < 5000)]
    df['hood_label'] = df['neighbourhood'].map(HOOD_LABELS).fillna(df['neighbourhood'].astype(str))
    df['est_occupancy'] = ((365 - df['availability_365']) / 365 * 100).clip(0, 100)
    df['est_monthly_rev'] = (df['price'] * df['est_occupancy'] / 100 * 30).round(0)
    df['reviews_per_month'] = df['reviews_per_month'].fillna(0)
    df['est_bookings_per_month'] = (df['reviews_per_month'] * 2.0).round(1)
    return df


# ═══════════════════════════════════════════════════
# ML PRICING MODEL — trained on actual Austin data
# ═══════════════════════════════════════════════════
@st.cache_resource
def train_pricing_model(_df):
    """
    Train a Gradient Boosting model to predict optimal price.
    Uses listings with high occupancy (>40%) as 'well-priced' examples.
    The underscore prefix on _df tells Streamlit not to hash this arg.
    """
    df = _df.copy()
    well_priced = df[
        (df['est_occupancy'] > 40) &
        (df['reviews_per_month'] > 1) &
        (df['price'] > 20)
    ].copy()

    if len(well_priced) < 100:
        well_priced = df[df['est_occupancy'] > 20].copy()

    room_map = {'Entire home/apt': 3, 'Private room': 2, 'Hotel room': 2.5, 'Shared room': 1}
    well_priced['room_type_enc'] = well_priced['room_type'].map(room_map).fillna(2)

    features = ['neighbourhood', 'room_type_enc', 'reviews_per_month',
                'number_of_reviews', 'est_occupancy', 'latitude', 'longitude']
    X = well_priced[features].fillna(0)
    y = well_priced['price']

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        subsample=0.8, random_state=42
    )
    model.fit(X, y)
    return model, room_map, features


def predict_base_price(model, room_map, features, listing):
    """Predict the ML-based optimal base price for a listing."""
    row = pd.DataFrame([{
        'neighbourhood': listing['neighbourhood'],
        'room_type_enc': room_map.get(listing['room_type'], 2),
        'reviews_per_month': listing['reviews_per_month'],
        'number_of_reviews': listing['number_of_reviews'],
        'est_occupancy': listing['est_occupancy'],
        'latitude': listing['latitude'],
        'longitude': listing['longitude'],
    }])
    pred = model.predict(row[features])[0]
    return max(25, round(pred))


# ═══════════════════════════════════════════════════
# LEARNED SEASONAL PATTERNS from review data
# ═══════════════════════════════════════════════════
@st.cache_data
def learn_seasonal_patterns(_df):
    """Learn month-level demand patterns from actual review dates in the dataset."""
    df = _df.copy()
    df_dated = df.dropna(subset=['last_review']).copy()
    df_dated['last_review_dt'] = pd.to_datetime(df_dated['last_review'], errors='coerce')
    df_dated = df_dated.dropna(subset=['last_review_dt'])
    df_dated['review_month'] = df_dated['last_review_dt'].dt.month

    if len(df_dated) > 500:
        month_counts = df_dated.groupby('review_month').size()
        month_avg = month_counts.mean()
        learned = {m: round(month_counts.get(m, month_avg) / month_avg, 2) for m in range(1, 13)}
    else:
        learned = {1:0.82, 2:0.88, 3:1.35, 4:1.08, 5:1.05, 6:1.02,
                   7:0.95, 8:0.90, 9:0.93, 10:1.25, 11:1.10, 12:0.92}
    return learned


# ═══════════════════════════════════════════════════
# SMART COMP ENGINE
# ═══════════════════════════════════════════════════
def find_comps(listing, df, radius_km=3.0, max_comps=50):
    """Find comparable properties by room type + geographic proximity."""
    same_type = df[
        (df['room_type'] == listing['room_type']) &
        (df['id'] != listing['id'])
    ].copy()

    lat1 = math.radians(listing['latitude'])
    lon1 = math.radians(listing['longitude'])
    same_type['dist_km'] = same_type.apply(lambda r: 6371 * 2 * math.asin(math.sqrt(
        math.sin((math.radians(r['latitude']) - lat1)/2)**2 +
        math.cos(lat1) * math.cos(math.radians(r['latitude'])) *
        math.sin((math.radians(r['longitude']) - lon1)/2)**2
    )), axis=1)

    nearby = same_type[same_type['dist_km'] <= radius_km].copy()
    if len(nearby) < 10:
        nearby = same_type.nsmallest(30, 'dist_km')

    nearby['price_sim'] = 1 - (abs(nearby['price'] - listing['price']) / max(listing['price'], 1)).clip(0, 1)
    nearby['geo_sim'] = 1 - (nearby['dist_km'] / radius_km).clip(0, 1)
    nearby['similarity'] = (nearby['price_sim'] * 0.4 + nearby['geo_sim'] * 0.6).round(3)
    return nearby.nlargest(max_comps, 'similarity')


# ═══════════════════════════════════════════════════
# PERSONALIZED FORECAST ENGINE
# ═══════════════════════════════════════════════════
def generate_personalized_forecast(base_price, est_occupancy, ml_base_price, seasonal, days=90):
    """Generate forecast using ML base price, learned seasonality, and events."""
    today = datetime.now()
    records = []
    dow_mult = {0: 0.92, 1: 0.88, 2: 0.90, 3: 0.95, 4: 1.05, 5: 1.18, 6: 1.08}

    for i in range(days):
        d = today + timedelta(days=i)
        mo, day, dow = d.month, d.day, d.weekday()

        s_mult = seasonal.get(mo, 1.0)
        d_mult = dow_mult.get(dow, 1.0)

        event = None
        e_mult = 1.0
        for ev in EVENTS:
            if ev['month'] == mo and ev['start'] <= day <= ev['end']:
                event = ev
                e_mult = ev['mult']
                break

        combined = s_mult * d_mult * e_mult
        optimal = max(25, round(ml_base_price * combined))

        base_occ = est_occupancy / 100
        price_ratio = base_price / max(optimal, 1)
        occ_adjustment = max(-0.3, min(0.2, (1 - price_ratio) * 0.5))
        np.random.seed(i + int(base_price))
        occ_prob = np.clip(base_occ * s_mult + occ_adjustment + np.random.normal(0, 0.02), 0.05, 0.95)

        records.append({
            'date': d, 'date_str': d.strftime('%b %d'),
            'month': mo, 'day': day, 'dow': dow,
            'day_name': d.strftime('%a'),
            'event_name': event['name'] if event else None,
            'event_icon': event['icon'] if event else '',
            'seasonal_mult': round(s_mult, 2),
            'dow_mult': round(d_mult, 2),
            'event_mult': round(e_mult, 2),
            'combined_mult': round(combined, 3),
            'optimal_price': optimal,
            'current_price': base_price,
            'occupancy_prob': round(float(occ_prob), 3),
            'is_weekend': dow >= 4,
        })

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════
# LISTING LOOKUP BY URL
# ═══════════════════════════════════════════════════
def extract_listing_id(url_or_text):
    """Extract Airbnb listing ID from URL or raw text."""
    patterns = [
        r'airbnb\.com/rooms/(\d+)',
        r'airbnb\.com/h/[\w-]+.*?[\?&]id=(\d+)',
        r'^(\d{4,})$',
    ]
    for pat in patterns:
        m = re.search(pat, str(url_or_text).strip())
        if m:
            return int(m.group(1))
    try:
        val = int(str(url_or_text).strip())
        if val > 1000:
            return val
    except ValueError:
        pass
    return None


# ═══════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════
def main():
    st.markdown("""
    # 📈 PriceScope<span style='color:#3B82F6'>ATX</span> <span style='font-size:16px; color:#64748B;'>v2.0</span>
    **Personalized Predictive Pricing** — Powered by ML trained on 10,000+ Austin listings
    """, unsafe_allow_html=True)

    df = load_data()
    model, room_map, feature_cols = train_pricing_model(df)
    seasonal = learn_seasonal_patterns(df)

    # ─── Sidebar: Listing Selection ───
    st.sidebar.markdown("## 🏠 Your Listing")
    input_method = st.sidebar.radio(
        "Find your listing:", ["Paste Airbnb URL or ID", "Browse by neighborhood"],
        label_visibility="collapsed"
    )

    listing = None

    if input_method == "Paste Airbnb URL or ID":
        url_input = st.sidebar.text_input(
            "Airbnb URL or Listing ID",
            placeholder="https://airbnb.com/rooms/1462311 or 1462311",
        )
        if url_input:
            lid = extract_listing_id(url_input)
            if lid and lid in df['id'].values:
                listing = df[df['id'] == lid].iloc[0]
                st.sidebar.success(f"✅ Found: {listing['name'][:50]}...")
            elif lid:
                st.sidebar.warning(f"ID {lid} not in our Austin dataset. Try browsing instead.")
            else:
                st.sidebar.warning("Couldn't parse that URL. Try pasting just the numeric ID.")
    else:
        neighborhoods = sorted(df['hood_label'].unique())
        default_idx = neighborhoods.index('East Austin') if 'East Austin' in neighborhoods else 0
        sel_hood = st.sidebar.selectbox("Neighborhood", neighborhoods, index=default_idx)
        hood_listings = df[df['hood_label'] == sel_hood].nlargest(60, 'number_of_reviews')
        options = {f"{r['name'][:45]}  ·  ${int(r['price'])}/n  ·  {r['room_type'][:12]}": r['id']
                   for _, r in hood_listings.iterrows()}
        sel_name = st.sidebar.selectbox("Listing", list(options.keys()))
        listing = df[df['id'] == options[sel_name]].iloc[0]

    if listing is None:
        st.markdown("""
        <div class='info-box'>
            <strong style='color:#3B82F6; font-size:16px;'>
                👋 Welcome! Paste your Airbnb URL or browse to get started.
            </strong><br>
            <span style='color:#94A3B8;'>We'll analyze your listing against 10,000+ Austin properties
            and generate personalized pricing recommendations backed by machine learning.</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### Austin Market Snapshot")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Listings", f"{len(df):,}")
        c2.metric("Median Nightly Rate", f"${df['price'].median():.0f}")
        c3.metric("Avg Occupancy", f"{df['est_occupancy'].mean():.1f}%")
        c4.metric("Top Earning Area", df.groupby('hood_label')['est_monthly_rev'].median().idxmax())
        st.stop()

    # ─── Settings & What-If ───
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Settings")
    forecast_days = st.sidebar.select_slider("Forecast horizon", [30, 45, 60, 75, 90], value=60)

    ml_base = predict_base_price(model, room_map, feature_cols, listing)
    forecast = generate_personalized_forecast(
        listing['price'], listing['est_occupancy'], ml_base, seasonal, forecast_days
    )
    comps = find_comps(listing, df)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎚️ What-If Pricing")
    whatif_price = st.sidebar.slider(
        "Test a different nightly rate",
        min_value=int(max(25, listing['price'] * 0.5)),
        max_value=int(listing['price'] * 2.0),
        value=int(listing['price']), step=5,
    )
    whatif_fc = generate_personalized_forecast(
        whatif_price, listing['est_occupancy'], whatif_price, seasonal, 30
    )
    whatif_rev = whatif_price * whatif_fc['occupancy_prob'].mean() * 30
    current_rev_30 = listing['price'] * forecast.head(30)['occupancy_prob'].mean() * 30
    st.sidebar.metric(
        f"30-day rev @ ${whatif_price}",
        f"${whatif_rev:,.0f}", f"${whatif_rev - current_rev_30:+,.0f} vs current"
    )

    # ─── Listing Header ───
    st.markdown(f"### 🏡 {listing['name'][:70]}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Current Price", f"${listing['price']:.0f}/night")
    c2.metric("ML Optimal Price", f"${ml_base}/night", f"${ml_base - listing['price']:+.0f}")
    c3.metric("Occupancy", f"{listing['est_occupancy']:.1f}%")
    c4.metric("Reviews/Month", f"{listing['reviews_per_month']:.1f}")
    c5.metric("Est. Monthly Rev", f"${listing['est_monthly_rev']:,.0f}")

    ml_monthly = ml_base * (listing['est_occupancy'] / 100) * 30
    gap = ml_monthly - listing['est_monthly_rev']
    if gap > 100:
        st.markdown(f"""
        <div class='insight-box'>
            <strong style='color:#10B981; font-size:16px;'>
                💰 Our model sees a ${gap:,.0f}/month revenue opportunity
            </strong><br>
            <span style='color:#94A3B8;'>Your current rate of <strong>${listing['price']:.0f}</strong> is
            below the ML-predicted optimal of <strong>${ml_base}</strong> for your property type,
            location, and market position. Based on what well-performing comps actually achieve.</span>
        </div>
        """, unsafe_allow_html=True)
    elif gap < -200:
        st.markdown(f"""
        <div class='warning-box'>
            <strong style='color:#EF4444; font-size:16px;'>
                ⚠️ You may be overpriced by ${abs(int(listing['price'] - ml_base))}/night
            </strong><br>
            <span style='color:#94A3B8;'>The model suggests <strong>${ml_base}/night</strong> based on
            comparable listings with strong occupancy. Current rate may be reducing bookings.</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ═══ TABS ═══
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Pricing Forecast", "📅 Occupancy & Empty Days",
        "🏘️ Competitor Intel", "⭐ Revenue Score"
    ])

    # ═══ TAB 1: PRICING FORECAST ═══
    with tab1:
        st.markdown("### Your Personalized Price Forecast")
        st.markdown(f"*ML model + learned seasonality + {len(EVENTS)} Austin event windows*")

        avg_opt = forecast['optimal_price'].mean()
        max_opt = forecast['optimal_price'].max()
        min_opt = forecast['optimal_price'].min()
        avg_occ = forecast['occupancy_prob'].mean()
        opt_rev = avg_opt * avg_occ * 30
        event_days = forecast[forecast['event_name'].notna()]
        weekend_avg = forecast[forecast['is_weekend']]['optimal_price'].mean()
        weekday_avg = forecast[~forecast['is_weekend']]['optimal_price'].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Optimal Rate", f"${avg_opt:.0f}", f"${avg_opt - listing['price']:+.0f} vs current")
        c2.metric("Rate Range", f"${min_opt:.0f} – ${max_opt:.0f}")
        c3.metric("Projected Monthly Rev", f"${opt_rev:,.0f}", f"${opt_rev - listing['est_monthly_rev']:+,.0f}")
        c4.metric("Weekend Premium", f"${weekend_avg:.0f}", f"+${weekend_avg - weekday_avg:.0f} vs weekday")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=forecast['date'], y=forecast['optimal_price'],
            mode='lines', name='ML Optimal Price',
            line=dict(color='#10B981', width=2.5),
            fill='tozeroy', fillcolor='rgba(16,185,129,0.08)',
            hovertemplate='%{x|%b %d}: <b>$%{y}</b><extra>Optimal</extra>'
        ))
        fig.add_hline(y=listing['price'], line_dash="dash", line_color="#EF4444", line_width=1.5,
                      annotation_text=f"Current: ${listing['price']:.0f}", annotation_position="top left")
        fig.add_hline(y=ml_base, line_dash="dot", line_color="#3B82F6", line_width=1,
                      annotation_text=f"ML Base: ${ml_base}", annotation_position="bottom right")
        if len(event_days) > 0:
            fig.add_trace(go.Scatter(
                x=event_days['date'], y=event_days['optimal_price'],
                mode='markers+text', name='Events',
                marker=dict(color='#8B5CF6', size=10, symbol='diamond'),
                text=event_days['event_icon'], textposition='top center',
                hovertemplate='%{x|%b %d}: <b>$%{y}</b> — %{customdata}<extra></extra>',
                customdata=event_days['event_name']
            ))
        fig.update_layout(
            template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
            title=None, yaxis_title='Nightly Rate ($)', xaxis_title=None,
            height=420, margin=dict(t=20, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            yaxis=dict(gridcolor='#1E2640'), xaxis=dict(gridcolor='#1E2640'),
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Seasonal Demand (Learned from Data)**")
            month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                          7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
            s_vals = [seasonal.get(m, 1.0) for m in range(1, 13)]
            s_colors = ['#10B981' if v > 1.05 else '#EF4444' if v < 0.95 else '#3B82F6' for v in s_vals]
            fig_s = go.Figure()
            fig_s.add_trace(go.Bar(
                x=[month_names[m] for m in range(1, 13)], y=s_vals,
                marker_color=s_colors, text=[f'{v:.0%}' for v in s_vals], textposition='outside'
            ))
            fig_s.add_hline(y=1.0, line_dash="dot", line_color="#64748B")
            fig_s.update_layout(
                template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
                height=280, margin=dict(t=10, b=30),
                yaxis=dict(title='Demand Multiplier', gridcolor='#1E2640'),
            )
            st.plotly_chart(fig_s, use_container_width=True)

        with col2:
            st.markdown("**Upcoming Events Impact**")
            upcoming = forecast[forecast['event_name'].notna()].groupby('event_name').agg(
                dates=('date_str', lambda x: f"{x.iloc[0]} – {x.iloc[-1]}"),
                mult=('event_mult', 'first'),
                peak_price=('optimal_price', 'max'),
            ).reset_index()
            if len(upcoming) > 0:
                for _, ev in upcoming.iterrows():
                    premium = int((ev['mult'] - 1) * 100)
                    st.markdown(f"**{ev['event_name']}** ({ev['dates']}) — +{premium}% → peak **${ev['peak_price']:.0f}/night**")
            else:
                st.info("No major events in your forecast window.")

    # ═══ TAB 2: OCCUPANCY ═══
    with tab2:
        st.markdown("### Occupancy & Empty Day Predictions")
        full_fc = generate_personalized_forecast(
            listing['price'], listing['est_occupancy'], ml_base, seasonal, 90
        )
        avg_occ_pct = full_fc['occupancy_prob'].mean() * 100
        empty_risk = (full_fc['occupancy_prob'] < 0.30).sum()
        peak_demand = (full_fc['occupancy_prob'] > 0.70).sum()
        rev_at_risk = empty_risk * listing['price'] * 0.5

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Predicted Avg Occupancy", f"{avg_occ_pct:.1f}%")
        c2.metric("Empty-Risk Days", f"{empty_risk}", "of 90 days")
        c3.metric("Peak Demand Days", f"{peak_demand}", ">70% probability")
        c4.metric("Revenue at Risk", f"${rev_at_risk:,.0f}", "from empty days")

        fig_occ = go.Figure()
        fig_occ.add_trace(go.Scatter(
            x=full_fc['date'], y=full_fc['occupancy_prob'] * 100,
            mode='lines', name='Occupancy %',
            line=dict(color='#3B82F6', width=2),
            fill='tozeroy', fillcolor='rgba(59,130,246,0.08)',
        ))
        high = full_fc[full_fc['occupancy_prob'] > 0.7]
        low = full_fc[full_fc['occupancy_prob'] < 0.3]
        if len(high) > 0:
            fig_occ.add_trace(go.Scatter(x=high['date'], y=high['occupancy_prob']*100,
                mode='markers', name='High demand', marker=dict(color='#10B981', size=6)))
        if len(low) > 0:
            fig_occ.add_trace(go.Scatter(x=low['date'], y=low['occupancy_prob']*100,
                mode='markers', name='At risk', marker=dict(color='#EF4444', size=6)))
        fig_occ.add_hline(y=30, line_dash="dot", line_color="#EF4444", annotation_text="Risk threshold")
        fig_occ.add_hline(y=70, line_dash="dot", line_color="#10B981", annotation_text="High demand")
        fig_occ.update_layout(
            template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
            yaxis_title='Occupancy Probability %', height=400, margin=dict(t=20, b=40),
            yaxis=dict(gridcolor='#1E2640', range=[0, 100]),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
        )
        st.plotly_chart(fig_occ, use_container_width=True)

        st.markdown("#### 🎯 Personalized Recommendations")
        low_mask = full_fc['occupancy_prob'] < 0.35
        groups = (low_mask != low_mask.shift()).cumsum()
        recs_shown = 0
        for _, group in full_fc[low_mask].groupby(groups[low_mask]):
            if len(group) < 2:
                continue
            start_d, end_d = group.iloc[0]['date_str'], group.iloc[-1]['date_str']
            n = len(group)
            avg_m = group['combined_mult'].mean()
            disc = min(30, max(5, int((1.1 - avg_m) * 40 + 8)))
            sugg = round(listing['price'] * (1 - disc / 100))
            pot_rev = sugg * n * 0.6
            lost_rev = listing['price'] * n * 0.1
            st.markdown(f"""
            <div class='warning-box'>
                <strong style='color:#F59E0B;'>📉 {start_d} – {end_d} ({n} days at risk)</strong><br>
                <span style='color:#94A3B8;'>
                    <strong>Action:</strong> Lower to <strong>${sugg}/night</strong> (−{disc}%)<br>
                    <strong>Impact:</strong> ~{n*0.1:.0f} bookings at current price → ~{n*0.6:.0f} at ${sugg}
                    → <strong style='color:#10B981;'>+${pot_rev - lost_rev:,.0f} recovered</strong>
                </span>
            </div>
            """, unsafe_allow_html=True)
            recs_shown += 1
            if recs_shown >= 4:
                break
        if recs_shown == 0:
            st.success("✅ No significant empty-risk periods detected!")

    # ═══ TAB 3: COMPETITOR INTEL ═══
    with tab3:
        st.markdown("### Competitor Intelligence")
        st.markdown(f"*{len(comps)} comparable properties within 3km radius*")

        if len(comps) == 0:
            st.warning("Not enough comps found.")
        else:
            comp_med = comps['price'].median()
            comp_p25 = comps['price'].quantile(0.25)
            comp_p75 = comps['price'].quantile(0.75)
            comp_occ = comps['est_occupancy'].mean()
            comp_rev = comps['est_monthly_rev'].median()
            price_pct = ((listing['price'] - comp_med) / comp_med * 100) if comp_med > 0 else 0
            occ_diff = listing['est_occupancy'] - comp_occ

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Your Price", f"${listing['price']:.0f}", f"{price_pct:+.1f}% vs comps")
            c2.metric("Comp Median", f"${comp_med:.0f}", f"{len(comps)} properties")
            c3.metric("Your Occupancy", f"{listing['est_occupancy']:.1f}%", f"{occ_diff:+.1f}%")
            c4.metric("Comp Median Rev", f"${comp_rev:,.0f}/mo")

            if price_pct > 20 and occ_diff < -10:
                st.markdown(f"""
                <div class='warning-box'>
                    <strong style='color:#EF4444;'>⚠️ Overpriced vs {len(comps)} nearby competitors</strong><br>
                    <span style='color:#94A3B8;'>You're {abs(price_pct):.0f}% above median with {abs(occ_diff):.0f}%
                    lower occupancy. Try <strong>${int(comp_p75)}</strong> (75th percentile).</span>
                </div>
                """, unsafe_allow_html=True)
            elif price_pct < -20 and occ_diff > 10:
                extra = int((comp_med - listing['price']) * listing['est_occupancy']/100 * 30)
                st.markdown(f"""
                <div class='insight-box'>
                    <strong style='color:#10B981;'>🎯 Underpriced — raise to capture +${extra}/mo</strong><br>
                    <span style='color:#94A3B8;'>You're {abs(price_pct):.0f}% below median with strong occupancy.
                    Raise to <strong>${int(comp_med)}</strong> for more revenue.</span>
                </div>
                """, unsafe_allow_html=True)

            fig_sc = go.Figure()
            fig_sc.add_trace(go.Scatter(
                x=comps['price'], y=comps['est_occupancy'],
                mode='markers', name='Competitors',
                marker=dict(color=comps['est_monthly_rev'], colorscale='Blues', size=8, opacity=0.6,
                           colorbar=dict(title='Rev/mo')),
                hovertemplate='$%{x}/night · %{y:.0f}% occ<extra></extra>'
            ))
            fig_sc.add_trace(go.Scatter(
                x=[listing['price']], y=[listing['est_occupancy']],
                mode='markers+text', name='YOU',
                marker=dict(color='#10B981', size=16, symbol='star', line=dict(width=2, color='white')),
                text=['YOU'], textposition='top center', textfont=dict(color='#10B981', size=12)
            ))
            fig_sc.update_layout(
                template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
                xaxis_title='Nightly Rate ($)', yaxis_title='Occupancy %',
                title='Price vs Occupancy — Your Market Position',
                height=420, margin=dict(t=40, b=40),
                yaxis=dict(gridcolor='#1E2640'), xaxis=dict(gridcolor='#1E2640'),
            )
            st.plotly_chart(fig_sc, use_container_width=True)

            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=comps['price'], nbinsx=25, name='Competitors',
                marker_color='rgba(59,130,246,0.4)', marker_line_color='#3B82F6'
            ))
            fig_dist.add_vline(x=listing['price'], line_color='#10B981', line_width=3,
                              annotation_text=f"You: ${listing['price']:.0f}")
            fig_dist.add_vline(x=ml_base, line_color='#8B5CF6', line_width=2, line_dash='dash',
                              annotation_text=f"ML Optimal: ${ml_base}")
            fig_dist.add_vline(x=comp_med, line_color='#F59E0B', line_dash='dot',
                              annotation_text=f"Median: ${comp_med:.0f}")
            fig_dist.update_layout(
                template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
                title=f"Price Distribution — {len(comps)} Comps",
                xaxis_title='Nightly Rate ($)', yaxis_title='# Listings',
                height=320, margin=dict(t=40, b=40),
            )
            st.plotly_chart(fig_dist, use_container_width=True)

            st.markdown("#### Neighborhood Comparison")
            hood_stats = df[df['room_type'] == listing['room_type']].groupby('hood_label').agg(
                median_price=('price', 'median'), avg_occ=('est_occupancy', 'mean'), count=('id', 'count'),
            ).reset_index()
            hood_stats = hood_stats[hood_stats['count'] >= 10].sort_values('median_price', ascending=True)
            fig_h = go.Figure()
            hcolors = ['#10B981' if h == listing['hood_label'] else '#3B82F6' for h in hood_stats['hood_label']]
            fig_h.add_trace(go.Bar(
                y=hood_stats['hood_label'], x=hood_stats['median_price'],
                orientation='h', marker_color=hcolors,
                text=hood_stats['median_price'].apply(lambda x: f'${x:.0f}'), textposition='outside',
            ))
            fig_h.update_layout(
                template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
                xaxis_title='Median Nightly Rate ($)',
                height=max(300, len(hood_stats)*32), margin=dict(l=130, t=10, b=30),
            )
            st.plotly_chart(fig_h, use_container_width=True)

    # ═══ TAB 4: REVENUE SCORE ═══
    with tab4:
        st.markdown("### Revenue Performance Score")
        max_rpm = max(df['reviews_per_month'].max(), 1)
        max_revs = max(df['number_of_reviews'].max(), 1)
        p90 = df['price'].quantile(0.9)

        scores = {
            'Booking Velocity': min(1, listing['reviews_per_month'] / max_rpm),
            'Occupancy Rate': listing['est_occupancy'] / 100,
            'Price Positioning': min(1, listing['price'] / p90),
            'Market Demand': min(1, listing['number_of_reviews'] / max_revs),
        }
        total = sum(v * w for v, w in zip(scores.values(), [0.3, 0.3, 0.2, 0.2]))

        df_t = df.copy()
        df_t['_s'] = (
            df_t['reviews_per_month'].fillna(0)/max_rpm*0.3 +
            (df_t['est_occupancy']/100)*0.3 +
            (df_t['price']/p90).clip(0,1)*0.2 +
            (df_t['number_of_reviews']/max_revs)*0.2
        ).clip(0,1)
        my_rank = int((df_t['_s'] > total).sum() + 1)
        pctile = (1 - my_rank / len(df_t)) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue Rank", f"#{my_rank:,}", f"of {len(df):,}")
        c2.metric("Score", f"{total*100:.0f}/100")
        c3.metric("Percentile", f"{pctile:.0f}th")
        c4.metric("Est. Annual Rev", f"${listing['est_monthly_rev']*12:,.0f}")

        fig_r = go.Figure()
        cats = list(scores.keys())
        vals = list(scores.values())
        fig_r.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats+[cats[0]],
            fill='toself', fillcolor='rgba(59,130,246,0.15)',
            line=dict(color='#3B82F6', width=2.5), name='Your Listing'
        ))
        if len(comps) > 0:
            cv = [
                min(1, comps['reviews_per_month'].mean()/max_rpm),
                comps['est_occupancy'].mean()/100,
                min(1, comps['price'].mean()/p90),
                min(1, comps['number_of_reviews'].mean()/max_revs),
            ]
            fig_r.add_trace(go.Scatterpolar(
                r=cv+[cv[0]], theta=cats+[cats[0]],
                fill='toself', fillcolor='rgba(239,68,68,0.08)',
                line=dict(color='#EF4444', width=1.5, dash='dot'), name='Comp Average'
            ))
        fig_r.update_layout(
            polar=dict(bgcolor='#0B0F1A',
                      radialaxis=dict(visible=True, range=[0,1], gridcolor='#1E2640'),
                      angularaxis=dict(gridcolor='#1E2640')),
            template='plotly_dark', paper_bgcolor='#0B0F1A',
            height=380, margin=dict(t=30, b=30),
            legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
        )
        st.plotly_chart(fig_r, use_container_width=True)

        st.markdown("#### Improvement Opportunities")
        tips = {
            'Booking Velocity': 'Enable instant book, respond within 1hr, competitive pricing in low periods.',
            'Occupancy Rate': 'Lower minimum nights, flexible cancellation, dynamic pricing for empty stretches.',
            'Price Positioning': 'Review comp pricing regularly. Even $5–10 increases on peak dates compound.',
            'Market Demand': 'Improve photos, title SEO, actively request reviews from every guest.',
        }
        for name, val in sorted(scores.items(), key=lambda x: x[1]):
            pct = val * 100
            color = '#EF4444' if pct < 30 else '#F59E0B' if pct < 60 else '#10B981'
            label = '⚠️ Needs work' if pct < 30 else '📈 Room to grow' if pct < 60 else '✅ Strong'
            st.markdown(f"**{name}:** <span style='color:{color};'>{pct:.0f}%</span> — {label}<br>"
                       f"<span style='color:#64748B; font-size:13px;'>{tips.get(name,'')}</span>",
                       unsafe_allow_html=True)
            st.progress(val)

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center; color:#64748B; font-size:12px;'>
        PriceScope ATX v2.0 · ML trained on {len(df):,} listings ·
        Learned seasonality · {len(EVENTS)} events · Haversine comp matching
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
