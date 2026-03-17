"""
PriceScope ATX — Predictive Pricing & Analytics Dashboard
=========================================================
A Streamlit dashboard for Austin short-term rental hosts/property managers.
Uses Inside Airbnb Austin dataset to forecast optimal pricing, predict occupancy,
analyze competitors, and score listing revenue potential.

Run: streamlit run app.py
Requirements: pip install streamlit pandas numpy plotly scikit-learn
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ─── Page Config ───
st.set_page_config(
    page_title="PriceScope ATX — Predictive Pricing",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───
st.markdown("""
<style>
    .stApp { background-color: #0B0F1A; }
    .block-container { padding-top: 1rem; }
    h1, h2, h3 { color: #E2E8F0 !important; }
    .metric-card {
        background: #131825; border: 1px solid #1E2640; border-radius: 10px;
        padding: 16px 18px; text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #3B82F6; }
    .metric-label { font-size: 12px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; }
    .insight-box {
        background: linear-gradient(135deg, #064E3B40, #064E3B20);
        border: 1px solid #10B98130; border-radius: 10px; padding: 14px 18px; margin: 10px 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #7F1D1D40, #7F1D1D20);
        border: 1px solid #EF444430; border-radius: 10px; padding: 14px 18px; margin: 10px 0;
    }
    div[data-testid="stMetric"] { background: #131825; border: 1px solid #1E2640; border-radius: 10px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── Constants ───
HOOD_LABELS = {
    78701: 'Downtown', 78702: 'East Austin', 78703: 'Zilker/Barton Hills',
    78704: 'South Austin', 78705: 'UT/Campus', 78721: 'East (21)',
    78723: 'Windsor Park', 78734: 'Lakeway', 78741: 'South (41)',
    78744: 'Southeast', 78745: 'South (45)', 78751: 'Hyde Park',
    78752: 'North Central', 78753: 'North (53)', 78757: 'Crestview',
    78758: 'North (58)', 78746: 'West Lake Hills',
}

SEASONAL_MULTIPLIERS = {
    1: 0.82, 2: 0.88, 3: 1.35, 4: 1.08, 5: 1.05, 6: 1.02,
    7: 0.95, 8: 0.90, 9: 0.93, 10: 1.25, 11: 1.10, 12: 0.92
}

EVENTS = [
    {"name": "SXSW", "month": 3, "start": 7, "end": 16, "multiplier": 1.85},
    {"name": "ACL Festival Wk1", "month": 10, "start": 2, "end": 4, "multiplier": 1.65},
    {"name": "ACL Festival Wk2", "month": 10, "start": 9, "end": 11, "multiplier": 1.60},
    {"name": "F1 US Grand Prix", "month": 10, "start": 17, "end": 19, "multiplier": 1.90},
    {"name": "UT Football (Home)", "month": 9, "start": 6, "end": 6, "multiplier": 1.30},
    {"name": "July 4th Weekend", "month": 7, "start": 3, "end": 5, "multiplier": 1.25},
    {"name": "Thanksgiving", "month": 11, "start": 27, "end": 30, "multiplier": 1.20},
    {"name": "New Year's Eve", "month": 12, "start": 30, "end": 31, "multiplier": 1.35},
]


# ─── Data Loading ───
@st.cache_data
def load_data():
    """Load and clean the listings CSV."""
    # Try multiple possible file locations
    for path in ['listings_1_.csv', 'listings(1).csv', 'listings.csv']:
        try:
            df = pd.read_csv(path)
            break
        except FileNotFoundError:
            continue
    else:
        st.error("Could not find listings CSV file. Place it in the same directory as app.py.")
        st.stop()

    # Clean data
    df = df.dropna(subset=['price'])
    df = df[df['price'] > 0]
    df = df[df['price'] < 5000]  # Remove outliers

    # Add computed columns
    df['hood_label'] = df['neighbourhood'].map(HOOD_LABELS).fillna(df['neighbourhood'].astype(str))
    df['est_occupancy'] = ((365 - df['availability_365']) / 365 * 100).clip(0, 100)
    df['est_monthly_rev'] = (df['price'] * df['est_occupancy'] / 100 * 30).round(0)

    return df


def get_event(month, day):
    """Return event info if date falls within an event."""
    for e in EVENTS:
        if e['month'] == month and e['start'] <= day <= e['end']:
            return e
    return None


def generate_forecast(base_price, base_occupancy, days=90):
    """Generate price and occupancy forecast for the next N days."""
    today = datetime.now()
    records = []

    for i in range(days):
        d = today + timedelta(days=i)
        month = d.month
        day = d.day
        dow = d.weekday()  # 0=Monday, 6=Sunday

        # Base seasonal multiplier
        mult = SEASONAL_MULTIPLIERS.get(month, 1.0)

        # Event multiplier
        event = get_event(month, day)
        event_name = event['name'] if event else None
        if event:
            mult *= event['multiplier']

        # Weekend premium
        if dow >= 4:  # Fri, Sat, Sun
            mult *= 1.12 if dow < 6 else 1.05

        # Optimal price
        optimal_price = round(base_price * mult)

        # Occupancy probability (inversely related to price when overpriced)
        occ_base = base_occupancy / 100
        occ_seasonal = min(0.95, max(0.15, occ_base + (mult - 1) * 0.2))
        np.random.seed(i + int(base_price))
        noise = np.random.normal(0, 0.03)
        occ_prob = np.clip(occ_seasonal + noise, 0.1, 0.95)

        records.append({
            'date': d, 'date_str': d.strftime('%m/%d'),
            'month': month, 'day': day, 'dow': dow,
            'event': event_name,
            'multiplier': round(mult, 2),
            'optimal_price': optimal_price,
            'current_price': base_price,
            'occupancy_prob': round(occ_prob, 3),
            'is_weekend': dow >= 4,
            'day_name': d.strftime('%a'),
        })

    return pd.DataFrame(records)


# ─── Main App ───
def main():
    # Header
    st.markdown("""
    # 📈 PriceScope<span style='color:#3B82F6'>ATX</span>
    **Predictive Pricing & Analytics Dashboard** — Austin Short-Term Rentals
    """, unsafe_allow_html=True)

    # Load data
    df = load_data()

    # Sidebar — Listing Selection
    st.sidebar.markdown("### 🏠 Select Your Listing")

    # Filter by neighborhood
    neighborhoods = sorted(df['hood_label'].unique())
    selected_hood = st.sidebar.selectbox("Neighborhood", neighborhoods, index=neighborhoods.index('East Austin') if 'East Austin' in neighborhoods else 0)

    # Filter listings in that neighborhood
    hood_listings = df[df['hood_label'] == selected_hood].nlargest(50, 'number_of_reviews')
    listing_options = {f"{r['name'][:50]}... ({r['room_type']}, ${int(r['price'])}/night)": r['id']
                       for _, r in hood_listings.iterrows()}

    selected_name = st.sidebar.selectbox("Listing", list(listing_options.keys()))
    selected_id = listing_options[selected_name]
    listing = df[df['id'] == selected_id].iloc[0]

    # Sidebar — Parameters
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Forecast Settings")
    forecast_days = st.sidebar.slider("Forecast horizon (days)", 30, 90, 60)
    price_adj = st.sidebar.slider("Price adjustment (%)", -30, 30, 0)
    adjusted_price = listing['price'] * (1 + price_adj / 100)

    # Sidebar — Market Summary
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Market Summary")
    st.sidebar.metric("Total Listings", f"{len(df):,}")
    st.sidebar.metric("Avg Nightly Rate", f"${df['price'].mean():.0f}")
    st.sidebar.metric("Median Rate", f"${df['price'].median():.0f}")
    st.sidebar.metric("Avg Occupancy", f"{df['est_occupancy'].mean():.1f}%")

    # Listing info bar
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Current Price", f"${listing['price']:.0f}/night")
    col2.metric("Occupancy", f"{listing['est_occupancy']:.1f}%")
    col3.metric("Reviews/Month", f"{listing['reviews_per_month']:.1f}" if pd.notna(listing['reviews_per_month']) else "N/A")
    col4.metric("Total Reviews", f"{listing['number_of_reviews']:,}")
    col5.metric("Est. Monthly Rev", f"${listing['est_monthly_rev']:,.0f}")

    st.markdown("---")

    # ─── Tabs ───
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Pricing Forecast", "📅 Occupancy", "🏘️ Competitors", "⭐ Revenue Score"])

    # ═══════════════════════════════════════════
    # TAB 1: PREDICTIVE PRICING
    # ═══════════════════════════════════════════
    with tab1:
        st.markdown("### Predictive Pricing Model")
        st.markdown(f"*Forecasting optimal nightly rates for the next {forecast_days} days using seasonal patterns, Austin events, and demand signals.*")

        forecast = generate_forecast(adjusted_price, listing['est_occupancy'], forecast_days)

        # Key metrics
        avg_opt = forecast['optimal_price'].mean()
        max_opt = forecast['optimal_price'].max()
        min_opt = forecast['optimal_price'].min()
        avg_occ = forecast['occupancy_prob'].mean()
        opt_monthly_rev = avg_opt * avg_occ * 30
        current_monthly_rev = listing['est_monthly_rev']
        rev_lift = opt_monthly_rev - current_monthly_rev

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Optimal Avg Rate", f"${avg_opt:.0f}", f"{((avg_opt/adjusted_price)-1)*100:+.1f}% vs current")
        c2.metric("Price Range", f"${min_opt:.0f} – ${max_opt:.0f}")
        c3.metric("Projected Monthly Rev", f"${opt_monthly_rev:,.0f}", f"${rev_lift:+,.0f}")
        c4.metric("Event Days", f"{forecast['event'].notna().sum()}", f"Peak: ${max_opt:.0f}")

        # Revenue opportunity callout
        if rev_lift > 0:
            st.markdown(f"""
            <div class='insight-box'>
                <strong style='color:#10B981; font-size:16px;'>💰 Revenue Opportunity: +${rev_lift:,.0f}/month</strong><br>
                <span style='color:#94A3B8;'>With dynamic pricing, estimated monthly revenue increases from
                <strong>${current_monthly_rev:,.0f}</strong> to <strong>${opt_monthly_rev:,.0f}</strong>.
                Weekend premium and event pricing drive the biggest gains.</span>
            </div>
            """, unsafe_allow_html=True)

        # Price forecast chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=forecast['date'], y=forecast['optimal_price'],
            mode='lines', name='Optimal Price',
            line=dict(color='#10B981', width=2),
            fill='tozeroy', fillcolor='rgba(16,185,129,0.1)'
        ))
        fig.add_hline(y=adjusted_price, line_dash="dash", line_color="#EF4444",
                      annotation_text=f"Current: ${adjusted_price:.0f}")

        # Mark events
        event_dates = forecast[forecast['event'].notna()]
        if len(event_dates) > 0:
            fig.add_trace(go.Scatter(
                x=event_dates['date'], y=event_dates['optimal_price'],
                mode='markers', name='Events',
                marker=dict(color='#8B5CF6', size=8, symbol='diamond'),
                text=event_dates['event'], hoverinfo='text+y'
            ))

        fig.update_layout(
            template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
            title='Optimal Nightly Rate Forecast',
            yaxis_title='Price ($)', xaxis_title='Date',
            height=400, margin=dict(t=40, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Monthly breakdown table
        st.markdown("#### Monthly Pricing Breakdown")
        monthly = forecast.groupby(forecast['date'].dt.strftime('%B')).agg(
            avg_price=('optimal_price', 'mean'),
            max_price=('optimal_price', 'max'),
            min_price=('optimal_price', 'min'),
            avg_occ=('occupancy_prob', 'mean'),
            events=('event', lambda x: ', '.join(x.dropna().unique()) if x.notna().any() else 'None'),
            days=('date', 'count')
        ).round(1)
        monthly['avg_occ'] = (monthly['avg_occ'] * 100).round(1).astype(str) + '%'
        monthly.columns = ['Avg Price', 'Peak Price', 'Min Price', 'Avg Occupancy', 'Events', 'Days']
        st.dataframe(monthly, use_container_width=True)

    # ═══════════════════════════════════════════
    # TAB 2: OCCUPANCY FORECASTING
    # ═══════════════════════════════════════════
    with tab2:
        st.markdown("### Occupancy & Empty Days Forecast")
        st.markdown("*Predicting occupancy trends and identifying high-risk empty periods.*")

        forecast_occ = generate_forecast(listing['price'], listing['est_occupancy'], 90)

        avg_occ_pct = forecast_occ['occupancy_prob'].mean() * 100
        empty_days = (forecast_occ['occupancy_prob'] < 0.30).sum()
        peak_days = (forecast_occ['occupancy_prob'] > 0.70).sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Predicted Occupancy", f"{avg_occ_pct:.1f}%")
        c2.metric("Empty-Risk Days", f"{empty_days}", f"of 90 days")
        c3.metric("Peak Demand Days", f"{peak_days}", "70%+ occupancy")
        c4.metric("Current Occupancy", f"{listing['est_occupancy']:.1f}%")

        # Occupancy heatmap by week
        fig_occ = go.Figure()
        fig_occ.add_trace(go.Scatter(
            x=forecast_occ['date'], y=forecast_occ['occupancy_prob'] * 100,
            mode='lines+markers', name='Occupancy %',
            line=dict(color='#3B82F6', width=2),
            marker=dict(
                color=forecast_occ['occupancy_prob'].apply(
                    lambda x: '#10B981' if x > 0.7 else ('#F59E0B' if x > 0.4 else '#EF4444')
                ),
                size=5
            ),
            fill='tozeroy', fillcolor='rgba(59,130,246,0.1)'
        ))
        fig_occ.add_hline(y=30, line_dash="dot", line_color="#EF4444", annotation_text="Low Risk Threshold")
        fig_occ.add_hline(y=70, line_dash="dot", line_color="#10B981", annotation_text="High Demand")

        fig_occ.update_layout(
            template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
            title='90-Day Occupancy Probability', yaxis_title='Occupancy %',
            height=400, margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig_occ, use_container_width=True)

        # Identify low periods and recommendations
        st.markdown("#### ⚡ Recommendations to Fill Empty Days")

        low_periods = []
        in_low = False
        start_idx = 0
        for i, row in forecast_occ.iterrows():
            if row['occupancy_prob'] < 0.35:
                if not in_low:
                    in_low = True
                    start_idx = i
            else:
                if in_low:
                    low_periods.append((start_idx, i - 1))
                    in_low = False
        if in_low:
            low_periods.append((start_idx, len(forecast_occ) - 1))

        if low_periods:
            for start, end in low_periods[:4]:
                period = forecast_occ.iloc[start:end+1] if end < len(forecast_occ) else forecast_occ.iloc[start:]
                if len(period) == 0:
                    continue
                avg_mult = period['multiplier'].mean()
                discount = min(30, max(5, int((1 - avg_mult) * 50 + 10)))
                suggested = round(listing['price'] * (1 - discount / 100))
                date_range = f"{period.iloc[0]['date_str']} – {period.iloc[-1]['date_str']}"

                st.warning(f"""
                **{date_range}** ({len(period)} days at risk)
                → Lower price ~{discount}% to **${suggested}/night** (vs ${listing['price']:.0f}) to fill these dates.
                """)
        else:
            st.success("No significant empty-risk periods detected in the next 90 days!")

    # ═══════════════════════════════════════════
    # TAB 3: COMPETITOR ANALYSIS
    # ═══════════════════════════════════════════
    with tab3:
        st.markdown("### Competitor Analysis")
        st.markdown(f"*Comparing your listing against similar properties in {listing['hood_label']}.*")

        # Get comps
        comps = df[
            (df['hood_label'] == listing['hood_label']) &
            (df['room_type'] == listing['room_type']) &
            (df['id'] != listing['id'])
        ]

        if len(comps) == 0:
            st.warning("Not enough comparable listings found.")
        else:
            comp_median = comps['price'].median()
            comp_mean = comps['price'].mean()
            comp_p25 = comps['price'].quantile(0.25)
            comp_p75 = comps['price'].quantile(0.75)
            comp_occ = comps['est_occupancy'].mean()

            price_diff = listing['price'] - comp_median
            price_pct = (price_diff / comp_median) * 100
            occ_diff = listing['est_occupancy'] - comp_occ

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Your Price", f"${listing['price']:.0f}", f"{price_pct:+.1f}% vs median")
            c2.metric("Comp Median", f"${comp_median:.0f}", f"{len(comps)} listings")
            c3.metric("Your Occupancy", f"{listing['est_occupancy']:.1f}%", f"{occ_diff:+.1f}% vs comps")
            c4.metric("Comp Avg Occ", f"{comp_occ:.1f}%")

            # Overpriced/underpriced alert
            if price_pct > 15 and occ_diff < -10:
                st.markdown(f"""
                <div class='warning-box'>
                    <strong style='color:#EF4444;'>⚠️ Overpriced vs Market</strong><br>
                    Your listing is priced {abs(price_pct):.0f}% above comparable properties but has
                    {abs(occ_diff):.0f}% lower occupancy. Consider lowering to ~${comp_median:.0f} to capture more bookings.
                </div>
                """, unsafe_allow_html=True)
            elif price_pct < -15 and occ_diff > 10:
                st.markdown(f"""
                <div class='insight-box'>
                    <strong style='color:#10B981;'>🎯 Underpriced — Revenue Opportunity</strong><br>
                    Your listing is priced {abs(price_pct):.0f}% below comps with {occ_diff:.0f}% higher occupancy.
                    You could raise rates to ~${comp_median * 0.95:.0f} and still maintain strong bookings.
                </div>
                """, unsafe_allow_html=True)

            # Price distribution chart
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=comps['price'], nbinsx=30, name='Competitors',
                marker_color='rgba(59,130,246,0.5)', marker_line_color='#3B82F6'
            ))
            fig_dist.add_vline(x=listing['price'], line_color='#10B981', line_width=3,
                              annotation_text=f"You: ${listing['price']:.0f}")
            fig_dist.add_vline(x=comp_median, line_color='#F59E0B', line_dash='dash',
                              annotation_text=f"Median: ${comp_median:.0f}")
            fig_dist.update_layout(
                template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
                title=f"Price Distribution — {listing['hood_label']} ({listing['room_type']})",
                xaxis_title='Nightly Rate ($)', yaxis_title='# Listings',
                height=350, margin=dict(t=40, b=40)
            )
            st.plotly_chart(fig_dist, use_container_width=True)

            # Neighborhood comparison
            st.markdown("#### Neighborhood Comparison")
            hood_stats = df[df['room_type'] == listing['room_type']].groupby('hood_label').agg(
                median_price=('price', 'median'),
                avg_occ=('est_occupancy', 'mean'),
                count=('id', 'count')
            ).reset_index()
            hood_stats = hood_stats[hood_stats['count'] >= 10].sort_values('median_price', ascending=True)

            fig_hood = go.Figure()
            colors = ['#10B981' if h == listing['hood_label'] else '#3B82F6' for h in hood_stats['hood_label']]
            fig_hood.add_trace(go.Bar(
                y=hood_stats['hood_label'], x=hood_stats['median_price'],
                orientation='h', marker_color=colors,
                text=hood_stats['median_price'].apply(lambda x: f'${x:.0f}'),
                textposition='outside'
            ))
            fig_hood.update_layout(
                template='plotly_dark', plot_bgcolor='#0B0F1A', paper_bgcolor='#0B0F1A',
                title=f"Median Price by Neighborhood ({listing['room_type']})",
                xaxis_title='Median Nightly Rate ($)', height=400, margin=dict(l=120, t=40)
            )
            st.plotly_chart(fig_hood, use_container_width=True)

    # ═══════════════════════════════════════════
    # TAB 4: REVENUE SCORING
    # ═══════════════════════════════════════════
    with tab4:
        st.markdown("### Revenue Score & Lead Ranking")
        st.markdown("*Scoring listings by predicted revenue potential using booking velocity, occupancy, pricing, and demand.*")

        # Calculate scores for all listings
        max_rpm = df['reviews_per_month'].max()
        max_reviews = df['number_of_reviews'].max()
        df_scored = df.copy()
        df_scored['score'] = (
            df_scored['reviews_per_month'].fillna(0) / max_rpm * 0.3 +
            (df_scored['est_occupancy'] / 100) * 0.3 +
            (df_scored['price'] / 500).clip(0, 1) * 0.2 +
            (df_scored['number_of_reviews'] / max_reviews) * 0.2
        ).clip(0, 1)

        my_score = df_scored[df_scored['id'] == listing['id']]['score'].values[0]
        my_rank = (df_scored['score'] > my_score).sum() + 1
        my_percentile = ((1 - my_rank / len(df_scored)) * 100)
        avg_rev = df_scored['est_monthly_rev'].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue Rank", f"#{my_rank:,}", f"of {len(df_scored):,}")
        c2.metric("Est. Monthly Revenue", f"${listing['est_monthly_rev']:,.0f}", f"Avg: ${avg_rev:,.0f}")
        c3.metric("Revenue Percentile", f"{my_percentile:.0f}th")
        c4.metric("Performance Score", f"{my_score * 100:.0f}/100")

        # Score breakdown
        st.markdown("#### Score Components")
        score_components = {
            'Booking Velocity': min(1, (listing['reviews_per_month'] or 0) / max_rpm),
            'Occupancy Rate': listing['est_occupancy'] / 100,
            'Price Positioning': min(1, listing['price'] / 500),
            'Market Demand': min(1, listing['number_of_reviews'] / max_reviews),
        }

        fig_radar = go.Figure()
        categories = list(score_components.keys())
        values = list(score_components.values())
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill='toself', fillcolor='rgba(59,130,246,0.2)',
            line=dict(color='#3B82F6', width=2), name='Your Listing'
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor='#0B0F1A',
                radialaxis=dict(visible=True, range=[0, 1], gridcolor='#1E2640'),
                angularaxis=dict(gridcolor='#1E2640')
            ),
            template='plotly_dark', paper_bgcolor='#0B0F1A',
            height=350, margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Top listings table
        st.markdown("#### Top 15 Revenue Listings")
        top_listings = df_scored.nlargest(15, 'est_monthly_rev')[
            ['name', 'hood_label', 'room_type', 'price', 'est_occupancy', 'est_monthly_rev', 'score']
        ].copy()
        top_listings.columns = ['Listing', 'Neighborhood', 'Type', 'Price', 'Occupancy %', 'Est. Monthly Rev', 'Score']
        top_listings['Price'] = top_listings['Price'].apply(lambda x: f'${x:.0f}')
        top_listings['Est. Monthly Rev'] = top_listings['Est. Monthly Rev'].apply(lambda x: f'${x:,.0f}')
        top_listings['Score'] = (top_listings['Score'] * 100).round(0).astype(int)
        top_listings['Occupancy %'] = top_listings['Occupancy %'].round(1)
        st.dataframe(top_listings, use_container_width=True, hide_index=True)


if __name__ == '__main__':
    main()
