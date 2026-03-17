import { useState, useMemo, useEffect, useRef } from "react";

// ─── Embedded Data ───
const DATA = {"c":[{"neighbourhood":78701,"hood_label":"Downtown","room_type":"Entire home/apt","ap":247.3,"mp":212.0,"p25":156.0,"p75":280.2,"av":240.5,"nr":48.5,"rpm":1.7,"n":736},{"neighbourhood":78701,"hood_label":"Downtown","room_type":"Hotel room","ap":444.2,"mp":350.0,"p25":344.0,"p75":485.0,"av":233.6,"nr":4.9,"rpm":0.4,"n":11},{"neighbourhood":78701,"hood_label":"Downtown","room_type":"Private room","ap":255.7,"mp":195.0,"p25":155.0,"p75":261.0,"av":216.9,"nr":20.0,"rpm":2.1,"n":137},{"neighbourhood":78702,"hood_label":"East Austin","room_type":"Entire home/apt","ap":255.4,"mp":159.0,"p25":105.0,"p75":265.8,"av":225.9,"nr":108.2,"rpm":2.4,"n":1122},{"neighbourhood":78702,"hood_label":"East Austin","room_type":"Private room","ap":86.8,"mp":64.0,"p25":51.0,"p75":86.0,"av":206.2,"nr":88.5,"rpm":1.9,"n":85},{"neighbourhood":78703,"hood_label":"Zilker/Barton Hills","room_type":"Entire home/apt","ap":294.7,"mp":170.0,"p25":110.0,"p75":291.0,"av":239.7,"nr":59.9,"rpm":1.7,"n":429},{"neighbourhood":78703,"hood_label":"Zilker/Barton Hills","room_type":"Private room","ap":122.2,"mp":77.5,"p25":53.2,"p75":130.2,"av":221.3,"nr":37.3,"rpm":0.7,"n":32},{"neighbourhood":78704,"hood_label":"South Austin","room_type":"Entire home/apt","ap":274.5,"mp":153.5,"p25":101.0,"p75":293.0,"av":228.1,"nr":70.1,"rpm":1.8,"n":1416},{"neighbourhood":78704,"hood_label":"South Austin","room_type":"Private room","ap":144.0,"mp":95.0,"p25":58.8,"p75":150.2,"av":227.0,"nr":40.6,"rpm":1.0,"n":68},{"neighbourhood":78705,"hood_label":"UT/Campus","room_type":"Entire home/apt","ap":137.7,"mp":96.0,"p25":77.0,"p75":137.0,"av":240.0,"nr":42.5,"rpm":1.9,"n":317},{"neighbourhood":78705,"hood_label":"UT/Campus","room_type":"Private room","ap":98.2,"mp":44.0,"p25":35.0,"p75":79.5,"av":265.1,"nr":17.0,"rpm":1.9,"n":36},{"neighbourhood":78721,"hood_label":"East (21)","room_type":"Entire home/apt","ap":206.2,"mp":137.0,"p25":90.8,"p75":228.2,"av":249.2,"nr":69.0,"rpm":2.3,"n":284},{"neighbourhood":78721,"hood_label":"East (21)","room_type":"Private room","ap":59.2,"mp":49.0,"p25":39.0,"p75":69.8,"av":196.3,"nr":50.7,"rpm":1.5,"n":24},{"neighbourhood":78723,"hood_label":"Windsor Park","room_type":"Entire home/apt","ap":168.8,"mp":126.0,"p25":84.0,"p75":190.0,"av":229.5,"nr":60.0,"rpm":1.9,"n":291},{"neighbourhood":78723,"hood_label":"Windsor Park","room_type":"Private room","ap":90.5,"mp":59.0,"p25":45.0,"p75":87.0,"av":194.4,"nr":21.2,"rpm":0.8,"n":65},{"neighbourhood":78741,"hood_label":"South (41)","room_type":"Entire home/apt","ap":195.8,"mp":111.0,"p25":84.0,"p75":177.0,"av":244.6,"nr":46.9,"rpm":1.8,"n":505},{"neighbourhood":78741,"hood_label":"South (41)","room_type":"Private room","ap":57.9,"mp":46.0,"p25":39.0,"p75":73.0,"av":197.5,"nr":36.3,"rpm":1.3,"n":61},{"neighbourhood":78744,"hood_label":"Southeast","room_type":"Entire home/apt","ap":215.7,"mp":135.5,"p25":87.2,"p75":194.0,"av":224.9,"nr":47.6,"rpm":1.9,"n":250},{"neighbourhood":78744,"hood_label":"Southeast","room_type":"Private room","ap":59.9,"mp":46.5,"p25":36.2,"p75":65.0,"av":195.6,"nr":51.5,"rpm":1.8,"n":114},{"neighbourhood":78745,"hood_label":"South (45)","room_type":"Entire home/apt","ap":176.6,"mp":133.5,"p25":93.0,"p75":199.2,"av":224.6,"nr":44.4,"rpm":1.6,"n":516},{"neighbourhood":78745,"hood_label":"South (45)","room_type":"Private room","ap":66.2,"mp":58.0,"p25":44.0,"p75":79.0,"av":204.9,"nr":27.6,"rpm":0.9,"n":81},{"neighbourhood":78751,"hood_label":"Hyde Park","room_type":"Entire home/apt","ap":126.1,"mp":96.5,"p25":73.0,"p75":138.2,"av":235.9,"nr":84.7,"rpm":2.0,"n":244},{"neighbourhood":78751,"hood_label":"Hyde Park","room_type":"Private room","ap":54.2,"mp":41.0,"p25":36.0,"p75":51.5,"av":297.2,"nr":14.5,"rpm":0.3,"n":39},{"neighbourhood":78758,"hood_label":"North (58)","room_type":"Entire home/apt","ap":138.7,"mp":117.0,"p25":93.0,"p75":159.5,"av":251.2,"nr":31.4,"rpm":1.6,"n":315},{"neighbourhood":78758,"hood_label":"North (58)","room_type":"Private room","ap":54.1,"mp":41.0,"p25":36.0,"p75":54.0,"av":204.9,"nr":15.3,"rpm":0.7,"n":35}],"l":[{"id":1462311,"name":"The Austin Texas House South Congress","neighbourhood":78704,"hood_label":"South Austin","room_type":"Entire home/apt","price":120,"number_of_reviews":1305,"reviews_per_month":9.01,"occ":40.0,"rev":1440},{"id":48867583,"name":"Close to UT Austin + Rooftop Pool","neighbourhood":78701,"hood_label":"Downtown","room_type":"Private room","price":206,"number_of_reviews":1271,"reviews_per_month":23.44,"occ":61.1,"rev":3776},{"id":949922,"name":"Vintage Airstream in East Austin","neighbourhood":78723,"hood_label":"Windsor Park","room_type":"Entire home/apt","price":65,"number_of_reviews":1268,"reviews_per_month":8.29,"occ":17.3,"rev":337},{"id":44334720,"name":"Kasa | 1BD, Walk to South Congress Bridge","neighbourhood":78701,"hood_label":"Downtown","room_type":"Entire home/apt","price":251,"number_of_reviews":1258,"reviews_per_month":20.09,"occ":18.1,"rev":1363},{"id":202187,"name":"South Congress Apartment","neighbourhood":78704,"hood_label":"South Austin","room_type":"Entire home/apt","price":72,"number_of_reviews":1133,"reviews_per_month":6.66,"occ":42.5,"rev":918},{"id":7859914,"name":"Private Garage Apartment Near Airport","neighbourhood":78744,"hood_label":"Southeast","room_type":"Entire home/apt","price":65,"number_of_reviews":1098,"reviews_per_month":8.96,"occ":39.7,"rev":774},{"id":5873238,"name":"Hyde Park Casita","neighbourhood":78751,"hood_label":"Hyde Park","room_type":"Entire home/apt","price":66,"number_of_reviews":896,"reviews_per_month":7.05,"occ":38.6,"rev":764},{"id":16157135,"name":"Sweet South Austin Studio Bouldin Creek","neighbourhood":78704,"hood_label":"South Austin","room_type":"Entire home/apt","price":127,"number_of_reviews":866,"reviews_per_month":8.11,"occ":88.5,"rev":3372},{"id":23505794,"name":"Modern Studio Heart of East Austin","neighbourhood":78702,"hood_label":"East Austin","room_type":"Entire home/apt","price":92,"number_of_reviews":780,"reviews_per_month":8.5,"occ":61.1,"rev":1686},{"id":628034,"name":"Charming Vintage Craftsman East DT","neighbourhood":78702,"hood_label":"East Austin","room_type":"Entire home/apt","price":161,"number_of_reviews":780,"reviews_per_month":4.91,"occ":100.0,"rev":4830},{"id":977492,"name":"Private Studio in Modern Crash Pad","neighbourhood":78702,"hood_label":"East Austin","room_type":"Entire home/apt","price":77,"number_of_reviews":692,"reviews_per_month":4.54,"occ":78.4,"rev":1811},{"id":4171708,"name":"Downtown Treetop Hideaway","neighbourhood":78701,"hood_label":"Downtown","room_type":"Entire home/apt","price":120,"number_of_reviews":812,"reviews_per_month":6.45,"occ":31.5,"rev":1134},{"id":18041548,"name":"Hili's Back house","neighbourhood":78703,"hood_label":"Zilker/Barton Hills","room_type":"Entire home/apt","price":135,"number_of_reviews":807,"reviews_per_month":7.87,"occ":38.9,"rev":1575},{"id":21231281,"name":"Sweet South Austin Bungalow Bouldin Creek","neighbourhood":78704,"hood_label":"South Austin","room_type":"Entire home/apt","price":132,"number_of_reviews":628,"reviews_per_month":6.54,"occ":85.8,"rev":3398},{"id":522136,"name":"Downtown Oasis - 1 Mile from Football","neighbourhood":78701,"hood_label":"Downtown","room_type":"Entire home/apt","price":130,"number_of_reviews":552,"reviews_per_month":3.42,"occ":58.9,"rev":2297},{"id":39974185,"name":"Tiny House Big Personality w/ Hot Tub","neighbourhood":78705,"hood_label":"UT/Campus","room_type":"Entire home/apt","price":108,"number_of_reviews":559,"reviews_per_month":7.88,"occ":75.1,"rev":2433},{"id":27901166,"name":"Amazing Location! Huge, Hip and Super Stylish","neighbourhood":78704,"hood_label":"South Austin","room_type":"Entire home/apt","price":470,"number_of_reviews":549,"reviews_per_month":6.39,"occ":85.5,"rev":12056},{"id":20801999,"name":"The Brady Carriage House Downtown","neighbourhood":78701,"hood_label":"Downtown","room_type":"Entire home/apt","price":134,"number_of_reviews":480,"reviews_per_month":5.07,"occ":86.0,"rev":3457},{"id":49015282,"name":"Brand new Private Studio close to Downtown","neighbourhood":78741,"hood_label":"South (41)","room_type":"Entire home/apt","price":164,"number_of_reviews":474,"reviews_per_month":8.77,"occ":82.5,"rev":4059},{"id":30104242,"name":"Modern and Cozy South Austin Studio","neighbourhood":78745,"hood_label":"South (45)","room_type":"Entire home/apt","price":52,"number_of_reviews":535,"reviews_per_month":6.45,"occ":86.6,"rev":1351}],"s":{"Jan":0.82,"Feb":0.88,"Mar":1.35,"Apr":1.08,"May":1.05,"Jun":1.02,"Jul":0.95,"Aug":0.9,"Sep":0.93,"Oct":1.25,"Nov":1.1,"Dec":0.92},"e":[{"n":"SXSW","m":3,"d":[7,16],"x":1.85},{"n":"ACL Wk1","m":10,"d":[2,4],"x":1.65},{"n":"ACL Wk2","m":10,"d":[9,11],"x":1.6},{"n":"F1 Grand Prix","m":10,"d":[17,19],"x":1.9},{"n":"UT Football","m":9,"d":[6,6],"x":1.3},{"n":"July 4th","m":7,"d":[3,5],"x":1.25},{"n":"Thanksgiving","m":11,"d":[27,30],"x":1.2},{"n":"NYE","m":12,"d":[30,31],"x":1.35}],"sum":{"total":10457,"avg":219,"med":134,"occ":35.6}};

const SEASONAL = DATA.s;
const EVENTS = DATA.e;
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const MONTH_FULL = ['January','February','March','April','May','June','July','August','September','October','November','December'];

// ─── Color system ───
const C = {
  bg: '#0B0F1A', card: '#131825', cardHover: '#1A2035', border: '#1E2640',
  accent: '#3B82F6', accentDim: '#1E3A5F', green: '#10B981', greenDim: '#064E3B',
  red: '#EF4444', redDim: '#7F1D1D', amber: '#F59E0B', amberDim: '#78350F',
  text: '#E2E8F0', textDim: '#94A3B8', textMuted: '#64748B',
  purple: '#8B5CF6', purpleDim: '#4C1D95',
};

// ─── Helpers ───
const fmt = (n) => n == null || isNaN(n) ? '—' : `$${Math.round(n).toLocaleString()}`;
const fmtPct = (n) => n == null || isNaN(n) ? '—' : `${n.toFixed(1)}%`;
const fmtK = (n) => n >= 1000 ? `$${(n/1000).toFixed(1)}k` : fmt(n);

function getEventForDate(month, day) {
  for (const e of EVENTS) {
    if (e.m === month + 1 && day >= e.d[0] && day <= e.d[1]) return e;
  }
  return null;
}

function getSeasonalMultiplier(monthIdx) {
  return SEASONAL[MONTHS[monthIdx]] || 1.0;
}

function generateForecast(basePrice, days = 90) {
  const today = new Date();
  const forecast = [];
  for (let i = 0; i < days; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    const mo = d.getMonth();
    const day = d.getDate();
    const dow = d.getDay();
    let mult = getSeasonalMultiplier(mo);
    const ev = getEventForDate(mo, day);
    if (ev) mult *= ev.x;
    if (dow === 5 || dow === 6) mult *= 1.12;
    if (dow === 0) mult *= 1.05;
    const optPrice = Math.round(basePrice * mult);
    const occProb = Math.min(0.95, Math.max(0.15, 0.55 + (1 - mult) * -0.3 + (Math.random() * 0.1 - 0.05)));
    forecast.push({
      date: d, dateStr: `${mo+1}/${day}`,
      month: mo, day, dow,
      event: ev ? ev.n : null,
      multiplier: mult,
      optimalPrice: optPrice,
      currentPrice: basePrice,
      occupancyProb: occProb,
      isWeekend: dow === 5 || dow === 6,
    });
  }
  return forecast;
}

// ─── Micro Components ───
const Badge = ({ children, color = C.accent, bg }) => (
  <span style={{
    display: 'inline-block', padding: '2px 8px', borderRadius: 4,
    fontSize: 11, fontWeight: 600, letterSpacing: '0.02em',
    background: bg || (color + '20'), color,
  }}>{children}</span>
);

const StatCard = ({ label, value, sub, accent = C.accent }) => (
  <div style={{
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10,
    padding: '16px 18px', flex: 1, minWidth: 150,
  }}>
    <div style={{ fontSize: 11, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 26, fontWeight: 700, color: accent, lineHeight: 1.1 }}>{value}</div>
    {sub && <div style={{ fontSize: 12, color: C.textDim, marginTop: 4 }}>{sub}</div>}
  </div>
);

const BarChart = ({ data, maxVal, color = C.accent, label, height = 18 }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
    <div style={{ width: 90, fontSize: 12, color: C.textDim, textAlign: 'right', flexShrink: 0 }}>{label}</div>
    <div style={{ flex: 1, background: C.bg, borderRadius: 4, height, overflow: 'hidden' }}>
      <div style={{
        width: `${Math.max(2, (data / maxVal) * 100)}%`, height: '100%',
        background: `linear-gradient(90deg, ${color}80, ${color})`,
        borderRadius: 4, transition: 'width 0.4s ease',
      }} />
    </div>
    <div style={{ width: 60, fontSize: 12, fontWeight: 600, color: C.text, textAlign: 'right' }}>{typeof data === 'number' && data > 1 ? fmt(data) : fmtPct(data)}</div>
  </div>
);

// ─── Mini SVG Sparkline ───
const Sparkline = ({ data, width = 200, height = 50, color = C.accent, showArea = true }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * width,
    height - ((v - min) / range) * (height - 4) - 2
  ]);
  const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0]},${p[1]}`).join(' ');
  const areaD = pathD + ` L${width},${height} L0,${height} Z`;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {showArea && <path d={areaD} fill={`${color}15`} />}
      <path d={pathD} fill="none" stroke={color} strokeWidth={2} />
    </svg>
  );
};

// ─── Calendar Heatmap ───
const CalendarHeatmap = ({ forecast }) => {
  const weeks = [];
  let currentWeek = [];
  const startDow = forecast[0]?.dow || 0;
  for (let i = 0; i < startDow; i++) currentWeek.push(null);
  forecast.forEach((d, idx) => {
    currentWeek.push(d);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });
  if (currentWeek.length > 0) weeks.push(currentWeek);

  const cellSize = 16;
  const gap = 2;

  return (
    <div style={{ overflowX: 'auto', paddingBottom: 8 }}>
      <div style={{ display: 'flex', gap: 2, marginBottom: 4 }}>
        {['S','M','T','W','T','F','S'].map((d,i) => (
          <div key={i} style={{ width: cellSize, textAlign: 'center', fontSize: 9, color: C.textMuted }}>{d}</div>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap }}>
        {weeks.map((week, wi) => (
          <div key={wi} style={{ display: 'flex', gap }}>
            {week.map((d, di) => {
              if (!d) return <div key={di} style={{ width: cellSize, height: cellSize }} />;
              const occ = d.occupancyProb;
              const bg = occ > 0.7 ? C.green : occ > 0.45 ? C.amber : C.red;
              return (
                <div key={di} title={`${d.dateStr}: ${(occ*100).toFixed(0)}% occ${d.event ? ` (${d.event})` : ''}`} style={{
                  width: cellSize, height: cellSize, borderRadius: 3,
                  background: `${bg}${Math.round(Math.max(30, occ * 100)).toString(16).padStart(2,'0')}`,
                  border: d.event ? `1px solid ${C.purple}` : 'none',
                  cursor: 'default',
                }} />
              );
            })}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: 10, color: C.textMuted }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: C.green + '80', display: 'inline-block' }} /> High Occupancy</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: C.amber + '60', display: 'inline-block' }} /> Medium</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: C.red + '40', display: 'inline-block' }} /> Low / At Risk</span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, borderRadius: 2, border: `1px solid ${C.purple}`, display: 'inline-block' }} /> Event</span>
      </div>
    </div>
  );
};

// ─── Tab Navigation ───
const TabBar = ({ tabs, active, onChange }) => (
  <div style={{ display: 'flex', gap: 2, background: C.bg, borderRadius: 10, padding: 3, marginBottom: 20 }}>
    {tabs.map(t => (
      <button key={t.id} onClick={() => onChange(t.id)} style={{
        flex: 1, padding: '10px 12px', border: 'none', borderRadius: 8, cursor: 'pointer',
        fontSize: 13, fontWeight: active === t.id ? 700 : 500, letterSpacing: '0.01em',
        background: active === t.id ? C.card : 'transparent',
        color: active === t.id ? C.accent : C.textMuted,
        transition: 'all 0.2s',
      }}>{t.icon} {t.label}</button>
    ))}
  </div>
);

// ─── Section 1: Predictive Pricing ───
const PricingForecast = ({ listing, comps }) => {
  const [days, setDays] = useState(60);
  const forecast = useMemo(() => generateForecast(listing.price, days), [listing.price, days]);

  const optPrices = forecast.map(f => f.optimalPrice);
  const avgOpt = Math.round(optPrices.reduce((a,b)=>a+b,0) / optPrices.length);
  const maxOpt = Math.max(...optPrices);
  const minOpt = Math.min(...optPrices);

  const currentMonthlyRev = listing.rev || listing.price * (listing.occ / 100) * 30;
  const avgOcc = forecast.reduce((a,d) => a + d.occupancyProb, 0) / forecast.length;
  const optMonthlyRev = Math.round(avgOpt * avgOcc * 30);
  const revLift = optMonthlyRev - currentMonthlyRev;

  const eventDays = forecast.filter(d => d.event);
  const weekendAvg = Math.round(forecast.filter(d => d.isWeekend).reduce((a,d) => a + d.optimalPrice, 0) / Math.max(1, forecast.filter(d => d.isWeekend).length));
  const weekdayAvg = Math.round(forecast.filter(d => !d.isWeekend).reduce((a,d) => a + d.optimalPrice, 0) / Math.max(1, forecast.filter(d => !d.isWeekend).length));

  // Monthly breakdown
  const monthlyBreakdown = useMemo(() => {
    const mb = {};
    forecast.forEach(d => {
      const key = MONTH_FULL[d.month];
      if (!mb[key]) mb[key] = { prices: [], events: new Set(), occ: [] };
      mb[key].prices.push(d.optimalPrice);
      mb[key].occ.push(d.occupancyProb);
      if (d.event) mb[key].events.add(d.event);
    });
    return Object.entries(mb).map(([month, v]) => ({
      month,
      avgPrice: Math.round(v.prices.reduce((a,b)=>a+b,0) / v.prices.length),
      maxPrice: Math.max(...v.prices),
      avgOcc: (v.occ.reduce((a,b)=>a+b,0) / v.occ.length * 100).toFixed(0),
      events: [...v.events],
      days: v.prices.length,
    }));
  }, [forecast]);

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatCard label="Current Nightly Rate" value={fmt(listing.price)} sub="Your listed price" />
        <StatCard label="Optimal Avg Rate" value={fmt(avgOpt)} sub={`Range: ${fmt(minOpt)}–${fmt(maxOpt)}`} accent={C.green} />
        <StatCard label="Projected Monthly Rev" value={fmtK(optMonthlyRev)} accent={C.green}
          sub={revLift > 0 ? `+${fmtK(revLift)} vs current` : 'At or below current'} />
        <StatCard label="Event Days Ahead" value={eventDays.length} sub={eventDays.length > 0 ? `Next: ${eventDays[0].event}` : 'None upcoming'} accent={C.purple} />
      </div>

      {revLift > 0 && (
        <div style={{
          background: `linear-gradient(135deg, ${C.greenDim}40, ${C.greenDim}20)`,
          border: `1px solid ${C.green}30`, borderRadius: 10, padding: '14px 18px', marginBottom: 20,
        }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.green, marginBottom: 4 }}>
            💰 Revenue Opportunity: +{fmtK(revLift)}/month
          </div>
          <div style={{ fontSize: 13, color: C.textDim, lineHeight: 1.5 }}>
            With dynamic pricing, this listing could earn an estimated <strong style={{ color: C.text }}>{fmtK(optMonthlyRev)}/mo</strong> vs current <strong style={{ color: C.text }}>{fmtK(currentMonthlyRev)}/mo</strong>.
            Weekend premium: {fmt(weekendAvg)} vs weekday {fmt(weekdayAvg)}.
            {eventDays.length > 0 && ` During events like ${eventDays[0].event}, rates can reach ${fmt(maxOpt)}.`}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[30, 60, 90].map(d => (
          <button key={d} onClick={() => setDays(d)} style={{
            padding: '6px 16px', borderRadius: 6, border: `1px solid ${days === d ? C.accent : C.border}`,
            background: days === d ? C.accentDim : 'transparent', color: days === d ? C.accent : C.textDim,
            fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}>{d} days</button>
        ))}
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>Optimal Price Forecast</div>
        <Sparkline data={optPrices} width={600} height={80} color={C.green} />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
          <span style={{ fontSize: 10, color: C.textMuted }}>{forecast[0]?.dateStr}</span>
          <span style={{ fontSize: 10, color: C.textMuted }}>— Current: {fmt(listing.price)} —</span>
          <span style={{ fontSize: 10, color: C.textMuted }}>{forecast[forecast.length - 1]?.dateStr}</span>
        </div>
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>Monthly Pricing Breakdown</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 10 }}>
          {monthlyBreakdown.map(mb => (
            <div key={mb.month} style={{
              background: C.bg, borderRadius: 8, padding: 12, border: `1px solid ${C.border}`,
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 6 }}>{mb.month}</div>
              <div style={{ fontSize: 11, color: C.textDim }}>Avg: <strong style={{ color: C.green }}>{fmt(mb.avgPrice)}</strong></div>
              <div style={{ fontSize: 11, color: C.textDim }}>Peak: <strong style={{ color: C.amber }}>{fmt(mb.maxPrice)}</strong></div>
              <div style={{ fontSize: 11, color: C.textDim }}>Occ: {mb.avgOcc}%</div>
              {mb.events.length > 0 && <div style={{ marginTop: 4 }}>{mb.events.map(e => <Badge key={e} color={C.purple}>{e}</Badge>)}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── Section 2: Occupancy Forecasting ───
const OccupancyForecast = ({ listing }) => {
  const forecast = useMemo(() => generateForecast(listing.price, 90), [listing.price]);
  const occData = forecast.map(d => d.occupancyProb * 100);

  // Find low-demand windows
  const lowPeriods = [];
  let inLow = false;
  let lowStart = null;
  forecast.forEach((d, i) => {
    if (d.occupancyProb < 0.35) {
      if (!inLow) { inLow = true; lowStart = i; }
    } else {
      if (inLow) {
        lowPeriods.push({ start: lowStart, end: i - 1 });
        inLow = false;
      }
    }
  });
  if (inLow) lowPeriods.push({ start: lowStart, end: forecast.length - 1 });

  const avgOcc = (forecast.reduce((a, d) => a + d.occupancyProb, 0) / forecast.length * 100).toFixed(1);
  const emptyDays = forecast.filter(d => d.occupancyProb < 0.3).length;
  const peakDays = forecast.filter(d => d.occupancyProb > 0.7).length;

  const priceReductions = lowPeriods.slice(0, 3).map(p => {
    const start = forecast[p.start];
    const end = forecast[p.end];
    const avgMult = forecast.slice(p.start, p.end + 1).reduce((a,d) => a + d.multiplier, 0) / (p.end - p.start + 1);
    const suggestedDiscount = Math.round((1 - avgMult) * 50 + 10);
    return {
      dateRange: `${start.dateStr} – ${end.dateStr}`,
      days: p.end - p.start + 1,
      discount: Math.min(30, Math.max(5, suggestedDiscount)),
      event: start.event,
    };
  });

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatCard label="Avg Predicted Occupancy" value={`${avgOcc}%`} accent={Number(avgOcc) > 50 ? C.green : C.amber} />
        <StatCard label="Empty-Risk Days" value={emptyDays} sub={`of ${forecast.length} days forecast`} accent={C.red} />
        <StatCard label="Peak Demand Days" value={peakDays} sub="70%+ occupancy probability" accent={C.green} />
        <StatCard label="Current Occupancy" value={fmtPct(listing.occ)} sub="Based on availability data" accent={listing.occ > 50 ? C.green : C.amber} />
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 8 }}>90-Day Occupancy Calendar</div>
        <CalendarHeatmap forecast={forecast} />
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>Occupancy Probability Trend</div>
        <Sparkline data={occData} width={600} height={70} color={C.accent} />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
          <span style={{ fontSize: 10, color: C.textMuted }}>{forecast[0]?.dateStr}</span>
          <span style={{ fontSize: 10, color: C.textMuted }}>{forecast[forecast.length - 1]?.dateStr}</span>
        </div>
      </div>

      {priceReductions.length > 0 && (
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>⚡ Recommended Actions to Fill Empty Days</div>
          {priceReductions.map((pr, i) => (
            <div key={i} style={{
              background: `${C.amberDim}30`, border: `1px solid ${C.amber}25`,
              borderRadius: 8, padding: 12, marginBottom: 8,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.amber }}>{pr.dateRange}</div>
                  <div style={{ fontSize: 12, color: C.textDim, marginTop: 2 }}>
                    {pr.days} days at risk · Lower price ~{pr.discount}% to fill these dates
                  </div>
                </div>
                <Badge color={C.amber}>-{pr.discount}%</Badge>
              </div>
              <div style={{ fontSize: 12, color: C.textDim, marginTop: 6 }}>
                Suggested rate: <strong style={{ color: C.text }}>{fmt(Math.round(listing.price * (1 - pr.discount / 100)))}/night</strong> (vs {fmt(listing.price)})
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Section 3: Competitor Analysis ───
const CompetitorAnalysis = ({ listing, comps }) => {
  const myComps = comps.filter(c =>
    c.hood_label === listing.hood_label && c.room_type === listing.room_type
  );
  const comp = myComps[0];
  if (!comp) return <div style={{ color: C.textDim, padding: 20 }}>No comparable data found for this combination.</div>;

  const priceDiff = listing.price - comp.mp;
  const pricePctDiff = ((priceDiff / comp.mp) * 100).toFixed(1);
  const compOcc = ((365 - comp.av) / 365 * 100).toFixed(1);
  const occDiff = (listing.occ - Number(compOcc)).toFixed(1);

  const isOverpriced = Number(pricePctDiff) > 15 && Number(occDiff) < -10;
  const isUnderpriced = Number(pricePctDiff) < -15 && Number(occDiff) > 10;

  // All neighborhoods for comparison
  const hoodComps = comps.filter(c => c.room_type === listing.room_type && c.n >= 10);

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatCard label="Your Price" value={fmt(listing.price)} sub={`${listing.hood_label} · ${listing.room_type}`} />
        <StatCard label="Comp Median" value={fmt(comp.mp)} sub={`${comp.n} similar listings`} accent={C.textDim} />
        <StatCard label="Price vs Comps" value={`${priceDiff > 0 ? '+' : ''}${pricePctDiff}%`}
          accent={Math.abs(Number(pricePctDiff)) < 10 ? C.green : (priceDiff > 0 ? C.amber : C.accent)} />
        <StatCard label="Occupancy vs Comps" value={`${Number(occDiff) > 0 ? '+' : ''}${occDiff}%`}
          accent={Number(occDiff) > 0 ? C.green : C.red} />
      </div>

      {(isOverpriced || isUnderpriced) && (
        <div style={{
          background: isOverpriced ? `${C.redDim}40` : `${C.greenDim}40`,
          border: `1px solid ${isOverpriced ? C.red : C.green}30`,
          borderRadius: 10, padding: '14px 18px', marginBottom: 20,
        }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: isOverpriced ? C.red : C.green, marginBottom: 4 }}>
            {isOverpriced ? '⚠️ Overpriced vs Market' : '🎯 Underpriced — Revenue Opportunity'}
          </div>
          <div style={{ fontSize: 13, color: C.textDim, lineHeight: 1.5 }}>
            {isOverpriced
              ? `Your listing is priced ${Math.abs(pricePctDiff)}% above comparable properties but has ${Math.abs(occDiff)}% lower occupancy. Consider lowering to ${fmt(comp.mp)} to capture more bookings.`
              : `Your listing is priced ${Math.abs(pricePctDiff)}% below comps with ${occDiff}% higher occupancy. You could raise rates to ${fmt(Math.round(comp.mp * 0.95))} and still maintain strong bookings.`
            }
          </div>
        </div>
      )}

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>
          Price Distribution — {listing.hood_label} ({listing.room_type})
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 12 }}>
          <div style={{ flex: 1, height: 28, background: C.bg, borderRadius: 6, position: 'relative', overflow: 'hidden' }}>
            {/* IQR range */}
            <div style={{
              position: 'absolute', left: `${(comp.p25 / comp.p75 / 1.5) * 100}%`,
              width: `${((comp.p75 - comp.p25) / (comp.p75 * 1.5)) * 100}%`,
              height: '100%', background: `${C.accent}30`, borderRadius: 4,
            }} />
            {/* Median line */}
            <div style={{
              position: 'absolute', left: `${(comp.mp / (comp.p75 * 1.5)) * 100}%`,
              width: 2, height: '100%', background: C.textDim,
            }} />
            {/* Your price marker */}
            <div style={{
              position: 'absolute', left: `${Math.min(95, (listing.price / (comp.p75 * 1.5)) * 100)}%`,
              top: 2, width: 8, height: 24, background: C.green, borderRadius: 3,
              transform: 'translateX(-4px)',
            }} />
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: C.textMuted }}>
          <span>25th: {fmt(comp.p25)}</span>
          <span>Median: {fmt(comp.mp)}</span>
          <span>75th: {fmt(comp.p75)}</span>
          <span style={{ color: C.green, fontWeight: 600 }}>You: {fmt(listing.price)}</span>
        </div>
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>Neighborhood Comparison ({listing.room_type})</div>
        {hoodComps.sort((a, b) => b.mp - a.mp).map(h => {
          const isMe = h.hood_label === listing.hood_label;
          const maxP = Math.max(...hoodComps.map(x => x.mp));
          return (
            <div key={h.hood_label} style={{ marginBottom: 6 }}>
              <BarChart
                data={h.mp}
                maxVal={maxP * 1.1}
                color={isMe ? C.green : C.accent}
                label={h.hood_label + (isMe ? ' ★' : '')}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── Section 4: Revenue Score / Lead Scoring ───
const RevenueScoring = ({ listing, allListings }) => {
  const sorted = [...allListings].sort((a, b) => (b.rev || 0) - (a.rev || 0));
  const myRank = sorted.findIndex(l => l.id === listing.id) + 1;
  const top10 = sorted.slice(0, 10);

  const avgRev = Math.round(allListings.reduce((a, l) => a + (l.rev || 0), 0) / allListings.length);
  const myRev = listing.rev || 0;
  const revPercentile = ((1 - myRank / allListings.length) * 100).toFixed(0);

  // Score components
  const maxRpm = Math.max(...allListings.map(l => l.reviews_per_month || 0));
  const scores = {
    booking: Math.min(1, (listing.reviews_per_month || 0) / maxRpm),
    occupancy: (listing.occ || 0) / 100,
    pricing: Math.min(1, listing.price / 500),
    demand: Math.min(1, (listing.number_of_reviews || 0) / 1000),
  };
  const totalScore = (scores.booking * 0.3 + scores.occupancy * 0.3 + scores.pricing * 0.2 + scores.demand * 0.2);

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatCard label="Revenue Rank" value={`#${myRank}`} sub={`of ${allListings.length} listings`} accent={myRank <= 20 ? C.green : C.amber} />
        <StatCard label="Est. Monthly Revenue" value={fmtK(myRev)} sub={`Avg in market: ${fmtK(avgRev)}`} accent={myRev > avgRev ? C.green : C.amber} />
        <StatCard label="Revenue Percentile" value={`${revPercentile}th`} accent={Number(revPercentile) > 75 ? C.green : C.accent} />
        <StatCard label="Performance Score" value={`${(totalScore * 100).toFixed(0)}/100`} accent={totalScore > 0.6 ? C.green : C.amber} />
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>Score Breakdown</div>
        {[
          { label: 'Booking Velocity', score: scores.booking, color: C.accent },
          { label: 'Occupancy Rate', score: scores.occupancy, color: C.green },
          { label: 'Price Positioning', score: scores.pricing, color: C.purple },
          { label: 'Market Demand', score: scores.demand, color: C.amber },
        ].map(s => (
          <div key={s.label} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 3 }}>
              <span style={{ color: C.textDim }}>{s.label}</span>
              <span style={{ color: s.color, fontWeight: 600 }}>{(s.score * 100).toFixed(0)}%</span>
            </div>
            <div style={{ height: 6, background: C.bg, borderRadius: 3 }}>
              <div style={{
                width: `${s.score * 100}%`, height: '100%', borderRadius: 3,
                background: `linear-gradient(90deg, ${s.color}60, ${s.color})`,
              }} />
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 12 }}>Top 10 Revenue Listings</div>
        <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 8 }}>Based on estimated monthly revenue (price × occupancy)</div>
        {top10.map((l, i) => (
          <div key={l.id} style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0',
            borderBottom: i < 9 ? `1px solid ${C.border}` : 'none',
            background: l.id === listing.id ? `${C.accent}10` : 'transparent',
            borderRadius: l.id === listing.id ? 6 : 0,
            padding: l.id === listing.id ? '8px 10px' : '8px 0',
          }}>
            <span style={{ width: 24, fontSize: 14, fontWeight: 700, color: i < 3 ? C.amber : C.textMuted, textAlign: 'center' }}>
              {i + 1}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, color: l.id === listing.id ? C.accent : C.text, fontWeight: l.id === listing.id ? 700 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {l.name} {l.id === listing.id && '← You'}
              </div>
              <div style={{ fontSize: 10, color: C.textMuted }}>{l.hood_label} · {fmt(l.price)}/night · {fmtPct(l.occ)} occ</div>
            </div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.green, whiteSpace: 'nowrap' }}>{fmtK(l.rev)}/mo</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Main Dashboard ───
export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('pricing');
  const [selectedId, setSelectedId] = useState(DATA.l[0]?.id);

  const listing = DATA.l.find(l => l.id === selectedId) || DATA.l[0];
  const comps = DATA.c;

  const tabs = [
    { id: 'pricing', label: 'Pricing Forecast', icon: '📈' },
    { id: 'occupancy', label: 'Occupancy', icon: '📅' },
    { id: 'comps', label: 'Competitors', icon: '🏘️' },
    { id: 'score', label: 'Revenue Score', icon: '⭐' },
  ];

  const neighborhoods = [...new Set(DATA.l.map(l => l.hood_label))].sort();

  return (
    <div style={{
      background: C.bg, minHeight: '100vh', color: C.text,
      fontFamily: "'DM Sans', 'Segoe UI', system-ui, sans-serif",
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(135deg, ${C.card}, ${C.bg})`,
        borderBottom: `1px solid ${C.border}`, padding: '20px 24px',
      }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 8,
              background: `linear-gradient(135deg, ${C.accent}, ${C.purple})`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 18, fontWeight: 800, color: '#fff',
            }}>P</div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>
                PriceScope<span style={{ color: C.accent }}>ATX</span>
              </div>
              <div style={{ fontSize: 11, color: C.textMuted }}>Predictive Pricing & Analytics · Austin Short-Term Rentals</div>
            </div>
          </div>

          {/* Market overview pills */}
          <div style={{ display: 'flex', gap: 16, marginTop: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, color: C.textDim }}>{DATA.sum.total.toLocaleString()} listings</span>
            <span style={{ fontSize: 11, color: C.textDim }}>Avg rate: {fmt(DATA.sum.avg)}</span>
            <span style={{ fontSize: 11, color: C.textDim }}>Median: {fmt(DATA.sum.med)}</span>
            <span style={{ fontSize: 11, color: C.textDim }}>Avg occ: {fmtPct(DATA.sum.occ)}</span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '20px 24px' }}>
        {/* Listing selector */}
        <div style={{
          background: C.card, border: `1px solid ${C.border}`, borderRadius: 10,
          padding: 16, marginBottom: 20,
        }}>
          <div style={{ fontSize: 11, color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
            Select Your Listing
          </div>
          <select
            value={selectedId}
            onChange={e => setSelectedId(Number(e.target.value))}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: `1px solid ${C.border}`, background: C.bg, color: C.text,
              fontSize: 13, cursor: 'pointer', appearance: 'auto',
            }}
          >
            {neighborhoods.map(hood => (
              <optgroup key={hood} label={hood}>
                {DATA.l.filter(l => l.hood_label === hood).map(l => (
                  <option key={l.id} value={l.id}>
                    {l.name} — {fmt(l.price)}/night · {fmtPct(l.occ)} occ
                  </option>
                ))}
              </optgroup>
            ))}
          </select>

          {listing && (
            <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
              <Badge color={C.accent}>{listing.hood_label}</Badge>
              <Badge color={C.purple}>{listing.room_type}</Badge>
              <Badge color={C.green}>{fmt(listing.price)}/night</Badge>
              <Badge color={listing.occ > 50 ? C.green : C.amber}>{fmtPct(listing.occ)} occupancy</Badge>
              <Badge color={C.textDim}>{listing.number_of_reviews} reviews</Badge>
            </div>
          )}
        </div>

        {/* Tab navigation */}
        <TabBar tabs={tabs} active={activeTab} onChange={setActiveTab} />

        {/* Tab content */}
        {activeTab === 'pricing' && <PricingForecast listing={listing} comps={comps} />}
        {activeTab === 'occupancy' && <OccupancyForecast listing={listing} />}
        {activeTab === 'comps' && <CompetitorAnalysis listing={listing} comps={comps} />}
        {activeTab === 'score' && <RevenueScoring listing={listing} allListings={DATA.l} />}

        {/* Footer */}
        <div style={{
          marginTop: 32, padding: '16px 0', borderTop: `1px solid ${C.border}`,
          fontSize: 11, color: C.textMuted, textAlign: 'center',
        }}>
          PriceScopeATX · Built with Inside Airbnb Austin data ({DATA.sum.total.toLocaleString()} listings) · Models: Seasonal decomposition + event multipliers + demand scoring
        </div>
      </div>
    </div>
  );
}
