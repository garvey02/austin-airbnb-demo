"""
PriceScope ATX v3 — Personalized Pricing with Live Data
========================================================
New in v3:
  - Calendar CSV upload: hosts upload their Airbnb calendar export for REAL booking data
  - Auto-refresh: pulls latest Inside Airbnb data (run refresh_data.py or auto on load)
  - Calendar-aware occupancy: actual booked/available dates replace availability proxy
  - Revenue calculations use real bookings when calendar is uploaded

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
import re, os, glob, warnings, math, json
warnings.filterwarnings('ignore')

st.set_page_config(page_title="PriceScope ATX", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# ─── CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
* { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background-color: #06090F; }
.block-container { padding-top: 1.2rem; max-width: 1100px; }
div[data-testid="stMetric"] {
    background: #0D1420; border: 1px solid #1A2744;
    border-radius: 10px; padding: 12px;
}
.g-box {
    background: linear-gradient(135deg, #064E3B40, #064E3B20);
    border: 1px solid #10B98130; border-radius: 12px; padding: 16px 20px; margin: 12px 0;
}
.r-box {
    background: linear-gradient(135deg, #7F1D1D40, #7F1D1D20);
    border: 1px solid #EF444430; border-radius: 12px; padding: 16px 20px; margin: 12px 0;
}
.b-box {
    background: linear-gradient(135deg, #1E3A5F40, #1E3A5F20);
    border: 1px solid #3B82F630; border-radius: 12px; padding: 16px 20px; margin: 12px 0;
}
.cal-box {
    background: linear-gradient(135deg, #4C1D9540, #4C1D9520);
    border: 1px solid #8B5CF630; border-radius: 12px; padding: 16px 20px; margin: 12px 0;
}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════
HOOD_LABELS = {
    78701:'Downtown', 78702:'East Austin', 78703:'Zilker/Barton Hills',
    78704:'South Austin', 78705:'UT/Campus', 78721:'East (21)',
    78723:'Windsor Park', 78734:'Lakeway', 78741:'South (41)',
    78744:'Southeast', 78745:'South (45)', 78751:'Hyde Park',
    78758:'North (58)', 78752:'North Central', 78753:'North (53)',
    78757:'Crestview', 78746:'West Lake Hills',
}

EVENTS = [
    {"name":"SXSW","start":"2026-03-13","end":"2026-03-22","mult":1.85},
    {"name":"ACL Wk1","start":"2026-10-02","end":"2026-10-04","mult":1.65},
    {"name":"ACL Wk2","start":"2026-10-09","end":"2026-10-11","mult":1.60},
    {"name":"F1 Grand Prix","start":"2026-10-23","end":"2026-10-25","mult":1.90},
    {"name":"UT Football","start":"2026-09-05","end":"2026-09-05","mult":1.30},
    {"name":"UT Football","start":"2026-09-19","end":"2026-09-19","mult":1.30},
    {"name":"UT Football","start":"2026-10-17","end":"2026-10-17","mult":1.30},
    {"name":"UT Football","start":"2026-11-07","end":"2026-11-07","mult":1.30},
    {"name":"July 4th","start":"2026-07-03","end":"2026-07-05","mult":1.25},
    {"name":"Labor Day","start":"2026-09-07","end":"2026-09-07","mult":1.15},
    {"name":"Thanksgiving","start":"2026-11-26","end":"2026-11-29","mult":1.20},
    {"name":"Christmas","start":"2026-12-23","end":"2026-12-26","mult":1.15},
    {"name":"NYE","start":"2026-12-30","end":"2027-01-01","mult":1.35},
    {"name":"ROT Rally","start":"2026-06-11","end":"2026-06-14","mult":1.15},
    {"name":"Trail of Lights","start":"2026-12-05","end":"2026-12-23","mult":1.08},
]

SEASONAL = {1:0.82,2:0.88,3:1.35,4:1.08,5:1.05,6:1.02,7:0.95,8:0.90,9:0.93,10:1.25,11:1.10,12:0.95}

# ═══════════════════════════════════════════
# DATA LOADING (with auto-refresh support)
# ═══════════════════════════════════════════
@st.cache_data(ttl=3600)  # Re-check hourly
def load_market_data():
    """Load listings CSV. Checks data/ dir first (from refresh_data.py), then root."""
    search_paths = [
        'data/listings.csv',             # From refresh_data.py
        'listings_1_.csv', 'listings(1).csv', 'listings.csv',
        'listing.csv', 'data/listings_1_.csv',
    ]
    df = None
    source = None
    for path in search_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                source = path
                break
            except Exception:
                continue
    if df is None:
        for match in glob.glob('*listing*.csv') + glob.glob('data/*listing*.csv'):
            try:
                test = pd.read_csv(match)
                if 'price' in test.columns:
                    df, source = test, match
                    break
            except Exception:
                continue
    if df is None:
        st.error("❌ No listings CSV found. Place `listings_1_.csv` in the repo root.")
        st.code('\n'.join(os.listdir('.')))
        st.stop()

    df = df.dropna(subset=['price'])
    df = df[(df['price'] > 10) & (df['price'] < 5000)]
    df['hood_label'] = df['neighbourhood'].map(HOOD_LABELS).fillna(df['neighbourhood'].astype(str))
    df['est_occupancy'] = ((365 - df['availability_365']) / 365 * 100).clip(0, 100)
    df['est_monthly_rev'] = (df['price'] * df['est_occupancy'] / 100 * 30).round(0)
    df['reviews_per_month'] = df['reviews_per_month'].fillna(0)
    df['last_review'] = pd.to_datetime(df['last_review'], errors='coerce')

    # Check data freshness
    meta_path = 'data/refresh_meta.json'
    freshness = "Unknown"
    if os.path.exists(meta_path):
        try:
            meta = json.load(open(meta_path))
            dl = meta.get('listings', {}).get('downloaded_at', '')
            if dl:
                freshness = dl[:10]
        except Exception:
            pass

    return df, source, freshness


# ═══════════════════════════════════════════
# CALENDAR CSV PARSER
# ═══════════════════════════════════════════
def parse_calendar_upload(uploaded_file, listing_id=None):
    """
    Parse an Airbnb calendar CSV export.
    Expected columns: listing_id, date, available, price, adjusted_price, minimum_nights
    OR: date, available, price (simpler exports)
    Returns processed DataFrame with occupancy insights.
    """
    try:
        cal = pd.read_csv(uploaded_file)
    except Exception as e:
        return None, f"Could not read CSV: {e}"

    # Normalize column names
    cal.columns = cal.columns.str.strip().str.lower()

    # Check for required columns
    if 'date' not in cal.columns:
        return None, "CSV must have a 'date' column."
    if 'available' not in cal.columns and 'status' not in cal.columns:
        return None, "CSV must have an 'available' or 'status' column."

    # Parse dates
    cal['date'] = pd.to_datetime(cal['date'], errors='coerce')
    cal = cal.dropna(subset=['date'])

    # Filter to specific listing if ID column exists
    if listing_id and 'listing_id' in cal.columns:
        cal_filtered = cal[cal['listing_id'] == listing_id]
        if len(cal_filtered) > 0:
            cal = cal_filtered

    # Parse availability
    if 'available' in cal.columns:
        cal['is_booked'] = cal['available'].astype(str).str.lower().isin(['f', 'false', '0', 'no', 'blocked'])
        cal['is_available'] = ~cal['is_booked']
    elif 'status' in cal.columns:
        cal['is_booked'] = cal['status'].astype(str).str.lower().isin(['booked', 'reserved', 'blocked'])
        cal['is_available'] = ~cal['is_booked']

    # Parse price
    if 'price' in cal.columns:
        cal['cal_price'] = pd.to_numeric(
            cal['price'].astype(str).str.replace(r'[$,]', '', regex=True),
            errors='coerce'
        )
    elif 'adjusted_price' in cal.columns:
        cal['cal_price'] = pd.to_numeric(
            cal['adjusted_price'].astype(str).str.replace(r'[$,]', '', regex=True),
            errors='coerce'
        )
    else:
        cal['cal_price'] = np.nan

    # Add time features
    cal['month'] = cal['date'].dt.month
    cal['dow'] = cal['date'].dt.dayofweek
    cal['is_weekend'] = cal['dow'].isin([4, 5, 6])

    # Sort by date
    cal = cal.sort_values('date').reset_index(drop=True)

    return cal, None


def analyze_calendar(cal):
    """Generate insights from parsed calendar data."""
    total_days = len(cal)
    booked_days = cal['is_booked'].sum()
    available_days = cal['is_available'].sum()
    occupancy_rate = (booked_days / total_days * 100) if total_days > 0 else 0

    # Monthly breakdown
    monthly = cal.groupby('month').agg(
        total=('date', 'count'),
        booked=('is_booked', 'sum'),
        avg_price=('cal_price', 'mean'),
    ).reset_index()
    monthly['occ_rate'] = (monthly['booked'] / monthly['total'] * 100).round(1)

    # Weekend vs weekday
    weekend_occ = cal[cal['is_weekend']]['is_booked'].mean() * 100 if len(cal[cal['is_weekend']]) > 0 else 0
    weekday_occ = cal[~cal['is_weekend']]['is_booked'].mean() * 100 if len(cal[~cal['is_weekend']]) > 0 else 0

    # Price analysis from calendar
    avg_listed_price = cal['cal_price'].mean() if cal['cal_price'].notna().any() else None

    # Find empty stretches (consecutive available days)
    empty_stretches = []
    in_stretch = False
    start_idx = 0
    for i, row in cal.iterrows():
        if row['is_available']:
            if not in_stretch:
                in_stretch = True
                start_idx = i
        else:
            if in_stretch:
                length = i - start_idx
                if length >= 3:
                    empty_stretches.append({
                        'start': cal.loc[start_idx, 'date'],
                        'end': cal.loc[i-1, 'date'],
                        'days': length,
                        'avg_price': cal.loc[start_idx:i-1, 'cal_price'].mean(),
                    })
                in_stretch = False
    # Handle trailing stretch
    if in_stretch:
        length = len(cal) - start_idx
        if length >= 3:
            empty_stretches.append({
                'start': cal.loc[start_idx, 'date'],
                'end': cal.iloc[-1]['date'],
                'days': length,
                'avg_price': cal.loc[start_idx:, 'cal_price'].mean(),
            })

    return {
        'total_days': total_days,
        'booked_days': booked_days,
        'available_days': available_days,
        'occupancy_rate': occupancy_rate,
        'monthly': monthly,
        'weekend_occ': weekend_occ,
        'weekday_occ': weekday_occ,
        'avg_listed_price': avg_listed_price,
        'empty_stretches': sorted(empty_stretches, key=lambda x: x['days'], reverse=True),
        'date_range': f"{cal['date'].min().strftime('%b %d, %Y')} – {cal['date'].max().strftime('%b %d, %Y')}",
    }


# ═══════════════════════════════════════════
# ML MODEL
# ═══════════════════════════════════════════
@st.cache_resource
def train_model(_df):
    from sklearn.preprocessing import LabelEncoder
    df = _df.copy()
    le_h, le_r = LabelEncoder(), LabelEncoder()
    df['h'] = le_h.fit_transform(df['neighbourhood'].astype(str))
    df['r'] = le_r.fit_transform(df['room_type'].astype(str))
    today = pd.Timestamp.now()
    df['recency'] = (1 - (today - df['last_review']).dt.days.fillna(999).clip(0,999) / 999).clip(0,1)
    feats = ['h','r','minimum_nights','number_of_reviews','reviews_per_month',
             'recency','calculated_host_listings_count','availability_365',
             'est_occupancy','latitude','longitude']
    X = df[feats].fillna(0)
    y = np.log1p(df['price'])
    m = GradientBoostingRegressor(n_estimators=200, max_depth=5, learning_rate=0.1,
                                   subsample=0.8, min_samples_leaf=10, random_state=42)
    m.fit(X, y)
    from sklearn.model_selection import cross_val_score
    r2 = cross_val_score(m, X, y, cv=5, scoring='r2').mean()
    return m, le_h, le_r, feats, r2

def predict_price(model, le_h, le_r, feats, listing):
    row = {
        'h': le_h.transform([str(listing['neighbourhood'])])[0] if str(listing['neighbourhood']) in le_h.classes_ else 0,
        'r': le_r.transform([listing['room_type']])[0] if listing['room_type'] in le_r.classes_ else 0,
        'minimum_nights': listing.get('minimum_nights', 2),
        'number_of_reviews': listing.get('number_of_reviews', 0),
        'reviews_per_month': listing.get('reviews_per_month', 0),
        'recency': 0.5,
        'calculated_host_listings_count': listing.get('calculated_host_listings_count', 1),
        'availability_365': listing.get('availability_365', 200),
        'est_occupancy': listing.get('est_occupancy', 40),
        'latitude': listing.get('latitude', 30.27),
        'longitude': listing.get('longitude', -97.74),
    }
    return round(np.expm1(model.predict(pd.DataFrame([row])[feats])[0]))


# ═══════════════════════════════════════════
# FORECAST ENGINE
# ═══════════════════════════════════════════
def get_event(date):
    for e in EVENTS:
        if pd.Timestamp(e['start']) <= date <= pd.Timestamp(e['end']):
            return e
    return None

def generate_forecast(base_price, ml_price, occ_rate, days=90, cal_data=None):
    """Generate forecast. If cal_data provided, use actual booking patterns."""
    today = datetime.now()
    records = []
    dow_m = {0:0.92, 1:0.88, 2:0.88, 3:1.02, 4:1.15, 5:1.20, 6:1.05}

    # If we have calendar data, learn from actual patterns
    cal_monthly_occ = {}
    cal_dow_occ = {}
    if cal_data is not None:
        for mo, grp in cal_data.groupby('month'):
            cal_monthly_occ[mo] = grp['is_booked'].mean()
        for dow, grp in cal_data.groupby('dow'):
            cal_dow_occ[dow] = grp['is_booked'].mean()

    for i in range(days):
        d = today + timedelta(days=i)
        date = pd.Timestamp(d)
        mo, dow = d.month, d.weekday()

        s = SEASONAL.get(mo, 1.0)
        dw = dow_m.get(dow, 1.0)
        ev = get_event(date)
        em = ev['mult'] if ev else 1.0

        total = s * dw * em
        optimal = round(ml_price * total)

        # Occupancy: prefer calendar-learned patterns if available
        if cal_monthly_occ:
            base_occ = cal_monthly_occ.get(mo, occ_rate / 100)
            if dow in cal_dow_occ:
                dow_factor = cal_dow_occ[dow] / max(0.01, np.mean(list(cal_dow_occ.values())))
                base_occ *= dow_factor
            if ev:
                base_occ = min(0.95, base_occ * em * 0.8)
            base_occ = np.clip(base_occ, 0.05, 0.95)
        else:
            base_occ = min(0.85, max(0.15, occ_rate/100 + (s - 1) * 0.25))
            if ev:
                base_occ = min(0.95, base_occ * em * 0.85)
            if dow in [4,5]:
                base_occ = min(0.95, base_occ * 1.15)
            elif dow in [1,2]:
                base_occ *= 0.85

        np.random.seed(i + int(base_price) + mo)
        occ = np.clip(base_occ + np.random.normal(0, 0.025), 0.05, 0.97)

        records.append({
            'date': d, 'date_str': d.strftime('%b %d'), 'month': mo,
            'dow': dow, 'day_name': d.strftime('%a'),
            'is_weekend': dow in [4,5,6],
            'event': ev['name'] if ev else None,
            'event_mult': em, 'seasonal_mult': s, 'dow_mult': dw,
            'total_mult': round(total, 3),
            'optimal_price': optimal, 'current_price': base_price,
            'occupancy_prob': round(float(occ), 3),
            'expected_rev': round(optimal * occ),
            'data_source': 'calendar' if cal_monthly_occ else 'model',
        })
    return pd.DataFrame(records)


# ═══════════════════════════════════════════
# COMPS
# ═══════════════════════════════════════════
def find_comps(df, listing, n=30):
    c = df[(df['id'] != listing['id']) & (df['room_type'] == listing['room_type'])].copy()
    c['geo'] = np.sqrt((c['latitude']-listing['latitude'])**2 + (c['longitude']-listing['longitude'])**2)
    c['score'] = (
        (c['neighbourhood'] == listing['neighbourhood']).astype(float) * 3 +
        (1 - (abs(c['price'] - listing['price']) / max(listing['price'],1)).clip(0,2)/2) * 2 +
        (1 - c['geo']/c['geo'].max()).clip(0,1) * 2
    )
    return c.nlargest(n, 'score')


def chart_layout(h=380, yt=""):
    return dict(
        template='plotly_dark', plot_bgcolor='#06090F', paper_bgcolor='#06090F',
        height=h, margin=dict(t=30,b=40,l=50,r=20), yaxis_title=yt,
        font=dict(family='Plus Jakarta Sans', color='#94A3B8'),
        xaxis=dict(gridcolor='#1A2744'), yaxis=dict(gridcolor='#1A2744'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(size=11)),
    )


# ═══════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════
def main():
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0A1628,#0F1D32,#0A1628);
        border:1px solid #1A2744; border-radius:16px; padding:24px 28px; margin-bottom:20px;">
        <div style="font-size:28px; font-weight:800; color:#F1F5F9;">
            PriceScope<span style="color:#3B82F6">ATX</span>
            <span style="font-size:14px; color:#64748B; font-weight:500; margin-left:8px;">v3</span>
        </div>
        <div style="font-size:14px; color:#94A3B8; margin-top:4px;">
            AI-powered pricing · Now with calendar upload for real booking data
        </div>
    </div>""", unsafe_allow_html=True)

    df, data_source, freshness = load_market_data()
    model, le_h, le_r, feats, r2 = train_model(df)

    # ─── Sidebar ───
    st.sidebar.markdown("### 🏠 Your Listing")
    method = st.sidebar.radio("Find listing:", ["Browse database", "Airbnb URL / ID"], label_visibility="collapsed")

    listing = None
    if method == "Airbnb URL / ID":
        url_in = st.sidebar.text_input("Airbnb URL or ID", placeholder="airbnb.com/rooms/123456 or 123456")
        if url_in:
            m = re.search(r'(\d{5,})', url_in)
            if m:
                lid = int(m.group(1))
                match = df[df['id'] == lid]
                if len(match) > 0:
                    listing = match.iloc[0]
                    st.sidebar.success(f"✅ Found listing #{lid}")
                else:
                    st.sidebar.warning(f"ID {lid} not in dataset. Use browse or enter details.")
    else:
        hoods = sorted(df['hood_label'].unique())
        sel_h = st.sidebar.selectbox("Neighborhood", hoods,
            index=hoods.index('East Austin') if 'East Austin' in hoods else 0)
        hdf = df[df['hood_label'] == sel_h].nlargest(60, 'number_of_reviews')
        opts = {f"{r['name'][:50]}  ·  ${int(r['price'])}/n": r['id'] for _, r in hdf.iterrows()}
        if opts:
            sel = st.sidebar.selectbox("Listing", list(opts.keys()))
            listing = df[df['id'] == opts[sel]].iloc[0]

    if listing is None:
        st.info("👈 Select a listing in the sidebar to get started.")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Listings Tracked", f"{len(df):,}")
        c2.metric("Median Rate", f"${df['price'].median():.0f}")
        c3.metric("Avg Occupancy", f"{df['est_occupancy'].mean():.1f}%")
        c4.metric("Data Source", data_source or "local")
        st.stop()

    # ─── Calendar Upload ───
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📅 Upload Your Calendar")
    st.sidebar.caption("Export from Airbnb → Listing → Availability → Export Calendar (CSV)")
    cal_file = st.sidebar.file_uploader("Calendar CSV", type=['csv'], label_visibility="collapsed")

    cal_data = None
    cal_insights = None
    if cal_file:
        cal_data, cal_err = parse_calendar_upload(cal_file, listing_id=listing.get('id'))
        if cal_err:
            st.sidebar.error(cal_err)
            cal_data = None
        else:
            cal_insights = analyze_calendar(cal_data)
            st.sidebar.success(f"✅ Loaded {cal_insights['total_days']} days of calendar data")
            st.sidebar.metric("Real Occupancy", f"{cal_insights['occupancy_rate']:.1f}%",
                            f"{cal_insights['occupancy_rate'] - listing['est_occupancy']:+.1f}% vs estimate")

    # ─── Settings ───
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Settings")
    forecast_days = st.sidebar.select_slider("Forecast", [30, 60, 90], value=60)

    # ─── ML + Forecast ───
    ml_price = predict_price(model, le_h, le_r, feats, listing)

    # Use calendar occupancy if available
    actual_occ = cal_insights['occupancy_rate'] if cal_insights else listing['est_occupancy']
    actual_rev = (listing['price'] * actual_occ / 100 * 30) if cal_insights else listing['est_monthly_rev']

    forecast = generate_forecast(listing['price'], ml_price, actual_occ, forecast_days, cal_data)
    comps = find_comps(df, listing)

    # ─── What-If ───
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎚️ What-If")
    wip = st.sidebar.slider("Test rate", int(max(25,listing['price']*0.5)), int(listing['price']*2), int(listing['price']), 5)
    wif = generate_forecast(wip, wip, actual_occ, 30, cal_data)
    wi_rev = wip * wif['occupancy_prob'].mean() * 30
    st.sidebar.metric(f"30-day rev @ ${wip}", f"${wi_rev:,.0f}",
                     f"${wi_rev - actual_rev:+,.0f} vs current")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Model R²: {r2:.3f} · Data: {data_source} · Fresh: {freshness}")

    # ─── Header Metrics ───
    delta = ml_price - listing['price']
    st.markdown(f"### 🏡 {str(listing['name'])[:70]}")

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Current Price", f"${listing['price']:.0f}/night")
    c2.metric("ML Optimal", f"${ml_price}/night", f"${delta:+.0f}")
    c3.metric("Occupancy", f"{actual_occ:.1f}%",
             "📅 from calendar" if cal_insights else "estimated")
    c4.metric("Reviews/Mo", f"{listing['reviews_per_month']:.1f}")
    c5.metric("Est Monthly Rev", f"${actual_rev:,.0f}")

    # Calendar data badge
    if cal_insights:
        st.markdown(f"""
        <div class="cal-box">
            <strong style="color:#8B5CF6; font-size:15px;">📅 Calendar Data Active</strong>
            — Using <strong>{cal_insights['total_days']}</strong> days of real booking data
            ({cal_insights['date_range']})<br>
            <span style="color:#94A3B8;">
                Real occupancy: <strong style="color:#E2E8F0;">{cal_insights['occupancy_rate']:.1f}%</strong>
                ({cal_insights['booked_days']} booked / {cal_insights['available_days']} available) ·
                Weekend: {cal_insights['weekend_occ']:.0f}% · Weekday: {cal_insights['weekday_occ']:.0f}%
                {f" · Avg listed price: ${cal_insights['avg_listed_price']:.0f}" if cal_insights['avg_listed_price'] else ""}
            </span>
        </div>""", unsafe_allow_html=True)

    # Revenue opportunity
    ml_rev = ml_price * actual_occ / 100 * 30
    gap = ml_rev - actual_rev
    if gap > 100:
        st.markdown(f"""<div class="g-box">
            <strong style="color:#10B981; font-size:16px;">💰 +${gap:,.0f}/month opportunity</strong><br>
            <span style="color:#94A3B8;">ML suggests <strong>${ml_price}/night</strong> vs your ${listing['price']:.0f}.
            {"Based on your actual calendar data." if cal_insights else "Based on market estimates."}</span>
        </div>""", unsafe_allow_html=True)
    elif gap < -200:
        st.markdown(f"""<div class="r-box">
            <strong style="color:#EF4444;">⚠️ Possibly overpriced by ${abs(int(delta))}/night</strong><br>
            <span style="color:#94A3B8;">Model suggests ${ml_price}/night for your market position.</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ═══ TABS ═══
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Pricing", "📅 Occupancy", "🏘️ Competitors", "⭐ Score"])

    # ═══ TAB 1 ═══
    with tab1:
        st.markdown("### Dynamic Pricing Forecast")
        data_label = "calendar-trained" if cal_data is not None else "model-estimated"
        st.caption(f"ML + seasonality + events · Occupancy: {data_label}")

        opt_rev_30 = forecast.head(30)['expected_rev'].sum()
        rev_lift = opt_rev_30 - actual_rev

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Avg Optimal Rate", f"${forecast['optimal_price'].mean():.0f}",
                  f"${forecast['optimal_price'].mean()-listing['price']:+.0f}")
        c2.metric("Peak Rate", f"${forecast['optimal_price'].max():.0f}",
                  f"{forecast[forecast['optimal_price']==forecast['optimal_price'].max()].iloc[0].get('event','')}")
        c3.metric("30-Day Projection", f"${opt_rev_30:,.0f}", f"${rev_lift:+,.0f}")
        c4.metric("Events Ahead", f"{forecast['event'].notna().sum()}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=forecast['date'], y=forecast['optimal_price'],
            mode='lines', name='Optimal', line=dict(color='#10B981', width=2.5),
            fill='tozeroy', fillcolor='rgba(16,185,129,0.06)'))
        fig.add_hline(y=listing['price'], line_dash="dash", line_color="#EF4444",
                     annotation_text=f"Current: ${listing['price']:.0f}")
        fig.add_hline(y=ml_price, line_dash="dot", line_color="#3B82F6",
                     annotation_text=f"ML Base: ${ml_price}")
        evd = forecast[forecast['event'].notna()]
        if len(evd) > 0:
            fig.add_trace(go.Scatter(x=evd['date'], y=evd['optimal_price'],
                mode='markers', name='Events', marker=dict(color='#8B5CF6', size=9, symbol='diamond'),
                customdata=evd['event'], hovertemplate='%{customdata}: $%{y}<extra></extra>'))
        fig.update_layout(**chart_layout(400, "Rate ($)"))
        st.plotly_chart(fig, use_container_width=True)

        # Seasonal breakdown
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Seasonal Demand**")
            mn = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
            vals = [SEASONAL[m] for m in range(1,13)]
            cols = ['#10B981' if v > 1.05 else '#EF4444' if v < 0.95 else '#3B82F6' for v in vals]
            fs = go.Figure(go.Bar(x=[mn[m] for m in range(1,13)], y=vals, marker_color=cols,
                text=[f'{v:.0%}' for v in vals], textposition='outside'))
            fs.add_hline(y=1.0, line_dash="dot", line_color="#64748B")
            fs.update_layout(**chart_layout(280, "Multiplier"))
            st.plotly_chart(fs, use_container_width=True)
        with col2:
            st.markdown("**Upcoming Events**")
            ups = forecast[forecast['event'].notna()].groupby('event').agg(
                dates=('date_str', lambda x: f"{x.iloc[0]}–{x.iloc[-1]}"),
                mult=('event_mult','first'), peak=('optimal_price','max')).reset_index()
            for _, ev in ups.iterrows():
                st.markdown(f"**{ev['event']}** ({ev['dates']}) — +{int((ev['mult']-1)*100)}% → ${ev['peak']:.0f}/night")
            if len(ups) == 0:
                st.info("No events in forecast window")

    # ═══ TAB 2 ═══
    with tab2:
        st.markdown("### Occupancy & Empty Days")

        full = generate_forecast(listing['price'], ml_price, actual_occ, 90, cal_data)
        avg_o = full['occupancy_prob'].mean() * 100
        empty = (full['occupancy_prob'] < 0.30).sum()
        peak = (full['occupancy_prob'] > 0.70).sum()

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Predicted Occ", f"{avg_o:.1f}%", "📅 calendar-trained" if cal_data is not None else "")
        c2.metric("Empty-Risk Days", f"{empty}", f"of 90")
        c3.metric("Peak Days", f"{peak}", ">70%")
        c4.metric("Rev at Risk", f"${empty * listing['price'] * 0.5:,.0f}")

        # Calendar heatmap if uploaded
        if cal_insights and len(cal_insights['empty_stretches']) > 0:
            st.markdown("#### 📅 Empty Stretches from Your Calendar (Real Data)")
            for stretch in cal_insights['empty_stretches'][:5]:
                days = stretch['days']
                s_date = stretch['start'].strftime('%b %d')
                e_date = stretch['end'].strftime('%b %d')
                disc = min(25, max(5, int(10 + days * 0.8)))
                sugg = round(listing['price'] * (1 - disc/100))
                st.markdown(f"""<div class="r-box">
                    <strong style="color:#F59E0B;">{s_date} – {e_date} ({days} consecutive empty days)</strong><br>
                    <span style="color:#94A3B8;">
                        Lower to <strong style="color:#E2E8F0;">${sugg}/night</strong> (−{disc}%) to fill.
                        Potential recovery: <strong style="color:#10B981;">~${sugg * days * 0.5:,.0f}</strong>
                    </span>
                </div>""", unsafe_allow_html=True)

        # Forecast occupancy chart
        fig_o = go.Figure()
        fig_o.add_trace(go.Scatter(x=full['date'], y=full['occupancy_prob']*100,
            mode='lines', name='Occ %', line=dict(color='#3B82F6', width=2),
            fill='tozeroy', fillcolor='rgba(59,130,246,0.06)'))
        hi = full[full['occupancy_prob'] > 0.7]
        lo = full[full['occupancy_prob'] < 0.3]
        if len(hi): fig_o.add_trace(go.Scatter(x=hi['date'], y=hi['occupancy_prob']*100,
            mode='markers', name='High', marker=dict(color='#10B981', size=5)))
        if len(lo): fig_o.add_trace(go.Scatter(x=lo['date'], y=lo['occupancy_prob']*100,
            mode='markers', name='At Risk', marker=dict(color='#EF4444', size=5)))
        fig_o.add_hline(y=30, line_dash="dot", line_color="#EF4444")
        fig_o.add_hline(y=70, line_dash="dot", line_color="#10B981")
        fig_o.update_layout(**chart_layout(380, "Occupancy %"))
        st.plotly_chart(fig_o, use_container_width=True)

        # Model recommendations for empty periods
        st.markdown("#### 🎯 Recommendations")
        low_mask = full['occupancy_prob'] < 0.35
        groups = (low_mask != low_mask.shift()).cumsum()
        ct = 0
        for _, grp in full[low_mask].groupby(groups[low_mask]):
            if len(grp) < 2: continue
            disc = min(25, max(5, int((1.1 - grp['total_mult'].mean()) * 35 + 8)))
            sugg = round(listing['price'] * (1 - disc/100))
            st.warning(f"**{grp.iloc[0]['date_str']} – {grp.iloc[-1]['date_str']}** ({len(grp)} days) → "
                      f"Lower to **${sugg}/night** (−{disc}%)")
            ct += 1
            if ct >= 4: break
        if ct == 0:
            st.success("✅ No significant empty-risk periods detected!")

    # ═══ TAB 3 ═══
    with tab3:
        st.markdown("### Competitor Intelligence")
        if len(comps) < 3:
            st.warning("Few comps found.")
        else:
            cm = comps['price'].median()
            co = comps['est_occupancy'].mean()
            pd_ = ((listing['price']-cm)/max(cm,1)*100)
            od_ = actual_occ - co

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Your Price", f"${listing['price']:.0f}", f"{pd_:+.0f}%")
            c2.metric("Comp Median", f"${cm:.0f}", f"{len(comps)} comps")
            c3.metric("Your Occ", f"{actual_occ:.0f}%", f"{od_:+.0f}%")
            c4.metric("ML Price", f"${ml_price}")

            if pd_ > 15 and od_ < -10:
                st.markdown(f"""<div class="r-box">
                    <strong style="color:#EF4444;">⚠️ Overpriced</strong> — {abs(pd_):.0f}% above
                    with {abs(od_):.0f}% lower occupancy. Try ${ml_price}.</div>""", unsafe_allow_html=True)
            elif pd_ < -15 and od_ > 5:
                extra = round((ml_price - listing['price']) * actual_occ/100 * 30)
                st.markdown(f"""<div class="g-box">
                    <strong style="color:#10B981;">🎯 Underpriced</strong> — raise to ${ml_price} →
                    +${extra:,}/mo</div>""", unsafe_allow_html=True)

            # Scatter
            fsc = go.Figure()
            fsc.add_trace(go.Scatter(x=comps['price'], y=comps['est_occupancy'],
                mode='markers', name='Comps', marker=dict(color='#3B82F6', size=7, opacity=0.6)))
            fsc.add_trace(go.Scatter(x=[listing['price']], y=[actual_occ],
                mode='markers+text', name='You',
                marker=dict(color='#10B981', size=14, symbol='star', line=dict(width=2, color='#fff')),
                text=['★ You'], textposition='top center'))
            fsc.update_layout(**chart_layout(400, "Occupancy %"))
            fsc.update_layout(xaxis_title="Price ($)")
            st.plotly_chart(fsc, use_container_width=True)

            # Distribution
            hl = df[(df['hood_label']==listing.get('hood_label',''))&(df['room_type']==listing['room_type'])]
            if len(hl) > 5:
                fd = go.Figure()
                fd.add_trace(go.Histogram(x=hl['price'], nbinsx=35, marker_color='rgba(59,130,246,0.4)'))
                fd.add_vline(x=listing['price'], line_color='#10B981', line_width=3,
                            annotation_text=f"You: ${listing['price']:.0f}")
                fd.add_vline(x=ml_price, line_color='#8B5CF6', line_dash='dash',
                            annotation_text=f"ML: ${ml_price}")
                fd.update_layout(**chart_layout(320, "# Listings"))
                st.plotly_chart(fd, use_container_width=True)

            # Hood comparison
            hs = df[df['room_type']==listing['room_type']].groupby('hood_label').agg(
                med=('price','median'), n=('id','count')).reset_index()
            hs = hs[hs['n']>=10].sort_values('med')
            hc = ['#10B981' if h==listing.get('hood_label','') else '#1E3A5F' for h in hs['hood_label']]
            fh = go.Figure(go.Bar(y=hs['hood_label'], x=hs['med'], orientation='h', marker_color=hc,
                text=hs['med'].apply(lambda x: f'${x:.0f}'), textposition='outside'))
            fh.update_layout(**chart_layout(max(280,len(hs)*30)))
            fh.update_layout(margin=dict(l=130))
            st.plotly_chart(fh, use_container_width=True)

    # ═══ TAB 4 ═══
    with tab4:
        st.markdown("### Revenue Score")
        mx_rpm = max(df['reviews_per_month'].max(), 1)
        mx_rev = max(df['number_of_reviews'].max(), 1)
        sc = {
            'Booking Velocity': min(1, listing['reviews_per_month']/mx_rpm),
            'Occupancy': actual_occ/100,
            'Price Position': min(1, listing['price']/df['price'].quantile(0.9)),
            'Demand': min(1, listing['number_of_reviews']/mx_rev),
        }
        tot = sum(v*w for v,w in zip(sc.values(), [.3,.3,.2,.2]))
        df['_s'] = (df['reviews_per_month'].fillna(0)/mx_rpm*.3 + df['est_occupancy']/100*.3 +
                    (df['price']/df['price'].quantile(0.9)).clip(0,1)*.2 + df['number_of_reviews']/mx_rev*.2).clip(0,1)
        rank = int((df['_s'] > tot).sum()) + 1

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Score", f"{min(100,round(tot*100))}/100")
        c2.metric("Rank", f"#{rank:,}", f"of {len(df):,}")
        c3.metric("Percentile", f"{round((1-rank/len(df))*100)}th")
        c4.metric("Annual Rev", f"${actual_rev*12:,.0f}")

        fr = go.Figure()
        cats = list(sc.keys())
        vals = list(sc.values())
        fr.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=cats+[cats[0]],
            fill='toself', fillcolor='rgba(59,130,246,0.15)', line=dict(color='#3B82F6', width=2.5)))
        fr.update_layout(
            polar=dict(bgcolor='#06090F', radialaxis=dict(visible=True, range=[0,1], gridcolor='#1A2744'),
                      angularaxis=dict(gridcolor='#1A2744')),
            template='plotly_dark', paper_bgcolor='#06090F', height=350, showlegend=False)
        st.plotly_chart(fr, use_container_width=True)

        tips = {
            'Booking Velocity': 'Enable instant book, respond fast, price competitively in slow periods.',
            'Occupancy': 'Lower min nights, flex cancellation, dynamic pricing for gaps.',
            'Price Position': 'Regular comp checks. $5–10 increases on peak days compound fast.',
            'Demand': 'Better photos, SEO title, actively request reviews.',
        }
        for name, val in sorted(sc.items(), key=lambda x: x[1]):
            p = min(100, round(val*100))
            color = '#10B981' if p > 65 else '#F59E0B' if p > 35 else '#EF4444'
            st.markdown(f"**{name}:** <span style='color:{color}'>{p}%</span> — {tips[name]}", unsafe_allow_html=True)
            st.progress(val)

    st.markdown(f"""<div style="text-align:center;padding:20px 0;color:#475569;font-size:12px;">
        PriceScopeATX v3 · R²={r2:.3f} · {len(df):,} listings · {len(EVENTS)} events ·
        {"📅 Calendar data active" if cal_data is not None else "Model estimates"}
    </div>""", unsafe_allow_html=True)


if __name__ == '__main__':
    main()
