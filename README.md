# austin-airbnb-demo
# PriceScope ATX — Predictive Pricing & Analytics Dashboard

A data-driven dashboard for Austin short-term rental hosts and property managers (Airbnb/VRBO), demonstrating how predictive analytics can increase revenue through optimized pricing decisions.

Built with the Inside Airbnb Austin dataset (10,457 listings).

---

## Deliverables

### 1. Interactive React Dashboard (`austin_pricing_dashboard.jsx`)
A self-contained React component that runs directly in Claude's artifact viewer or any React environment. Includes all data embedded — no external dependencies needed.

### 2. Streamlit App (`app.py`)
A full Python Streamlit dashboard with interactive charts (Plotly), designed to run locally.

---

## How to Run the Streamlit App

```bash
# 1. Install dependencies
pip install streamlit pandas numpy plotly scikit-learn

# 2. Place the listings CSV in the same directory as app.py
#    (rename to listings_1_.csv, listings(1).csv, or listings.csv)

# 3. Launch
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

---

## Dashboard Sections

### 📈 1. Predictive Pricing Forecast
- Forecasts optimal nightly rates for the next 30–90 days
- **Factors modeled:** Seasonality (monthly patterns), day-of-week (weekend premium), major Austin events (SXSW +85%, F1 +90%, ACL +65%), demand trends
- **Output:** Sparkline/chart of predicted optimal price over time, monthly breakdown with avg/peak prices, estimated revenue lift vs current pricing
- **Key insight:** Shows dollar impact — e.g., "+$1,200/month with dynamic pricing"

### 📅 2. Occupancy & Empty Days Forecast
- Predicts 90-day occupancy probability for the selected listing
- Calendar heatmap showing high/medium/low demand days
- Identifies "churn periods" — stretches likely to remain unbooked
- **Actionable recommendations:** "Lower price 15% during Apr 8–14 to fill 7 empty-risk days"

### 🏘️ 3. Competitor Analysis
- Compares selected listing against all comparable properties (same neighborhood + room type)
- Price distribution showing where you sit vs the market (25th/median/75th percentile)
- Cross-neighborhood median price comparison
- **Smart alerts:** Flags overpriced listings (high price + low occupancy vs comps) and underpriced opportunities

### ⭐ 4. Revenue Score & Lead Ranking
- Composite performance score (0–100) based on 4 factors:
  - Booking Velocity (reviews/month) — 30% weight
  - Occupancy Rate — 30% weight
  - Price Positioning — 20% weight
  - Market Demand (total reviews) — 20% weight
- Revenue ranking against all tracked listings
- Top 10/15 revenue leaderboard

---

## Data & Methodology

**Source:** Inside Airbnb Austin dataset (`listings.csv`)
- 10,457 listings after cleaning (removed nulls, outliers >$5,000/night)
- 12 neighborhoods tracked (by zip code)

**Occupancy Estimation:**
- `est_occupancy = (365 - availability_365) / 365 × 100`
- This is a proxy; actual occupancy would come from calendar/booking data

**Pricing Model:**
- Seasonal decomposition: Monthly multipliers derived from Austin tourism patterns
- Event calendar: Hard-coded major Austin events with empirically-informed price multipliers
- Day-of-week: Weekend premium (Fri/Sat +12%, Sun +5%)
- Combined: `optimal_price = base_price × seasonal × event × weekend`

**Events Modeled:**
| Event | Month | Multiplier |
|-------|-------|-----------|
| SXSW | March 7–16 | 1.85× |
| F1 US Grand Prix | Oct 17–19 | 1.90× |
| ACL Festival Wk1 | Oct 2–4 | 1.65× |
| ACL Festival Wk2 | Oct 9–11 | 1.60× |
| UT Football (Home) | Sep–Nov | 1.30× |
| July 4th | Jul 3–5 | 1.25× |
| Thanksgiving | Nov 27–30 | 1.20× |
| New Year's Eve | Dec 30–31 | 1.35× |

---

## Key Visuals (What the Client Sees)

1. **Revenue Opportunity Banner** — Green callout showing "+$X,XXX/month with optimized pricing" with before/after comparison
2. **Price Forecast Sparkline** — 90-day optimal rate curve with current price baseline and event markers
3. **Occupancy Calendar Heatmap** — Color-coded grid (green=high, amber=medium, red=at-risk) with purple borders for events
4. **Competitor Price Distribution** — Histogram of comp prices with "You are here" marker
5. **Performance Radar Chart** — 4-axis score breakdown showing strengths and improvement areas

---

## Why This Matters for Clients

A host paying a $2k/month retainer sees value when:
- **Dynamic pricing** captures an extra $1,200–$3,000/month during peak periods
- **Empty day detection** fills 5–10 otherwise-vacant nights per month
- **Competitor intelligence** prevents over/underpricing by 15–25%
- **Revenue scoring** prioritizes which listings to optimize first

The dashboard makes this impact immediately visible and measurable.
