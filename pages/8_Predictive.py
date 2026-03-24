import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_engine import get_system_data
from components import setup_page, render_sidebar, render_header, render_kpi
from styles import get_chart_config

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Predictive Intelligence", "🔮", "predictive")
chart_cfg = get_chart_config()
render_sidebar("predictive", "🔮")

# ═══════════════════════════════════════════════════════════════
# 2. DATA PREP
# ═══════════════════════════════════════════════════════════════
df_kpi, df_demand = get_system_data()

with st.sidebar:
    st.markdown("---")
    CAPACITY_LIMIT = st.slider("Critical Capacity Threshold", 30, 100, 60)
    history_window = st.slider("History Window (days)", 7, 90, 30)

# Process Historical Data
history = df_kpi.tail(history_window).copy()
history["date"] = pd.to_datetime(history["date"], dayfirst=True)
last_hist_date = history["date"].iloc[-1]
last_hist_val = history["daily_admissions"].iloc[-1]

# 7-Day AI Forecast Data
forecast_dates = pd.date_range(start=last_hist_date, periods=8)
forecast_vals = [last_hist_val] + list(df_demand["daily_admissions"].iloc[-7:].values)
conf_upper = [v * 1.15 for v in forecast_vals]
conf_lower = [max(0, v * 0.85) for v in forecast_vals]

# Risk Logic
forecast_peak = max(forecast_vals)
admission_risk = "CRITICAL" if forecast_peak >= CAPACITY_LIMIT else "WARNING" if forecast_peak >= CAPACITY_LIMIT * 0.85 else "STABLE"
risk_color = t["critical"] if admission_risk == "CRITICAL" else t["warning"] if admission_risk == "WARNING" else t["success"]

# ═══════════════════════════════════════════════════════════════
# 3. HEADER & KPIs
# ═══════════════════════════════════════════════════════════════
render_header(
    title="Predictive Intelligence",
    subtitle=f"Nexus AI v2.4 Horizon Forecast · Next 7 Days",
    icon="🔮",
    right_badge=admission_risk,
    right_color=risk_color
)

k1, k2, k3, k4 = st.columns(4)
render_kpi(k1, "Forecast Peak", str(int(forecast_peak)), "Max Projected Load", t["warning"], "📈")
render_kpi(k2, "7-Day Avg", f"{np.mean(forecast_vals[1:]):.1f}", "Daily Projection", t["info"], "📊")
render_kpi(k3, "Capacity Risk", f"{sum(1 for v in forecast_vals if v >= CAPACITY_LIMIT)} Days", "Threshold Breaches", t["critical"], "🚨")
render_kpi(k4, "Surge Factor", f"{df_demand['surge_multiplier'].iloc[-1]}x", "Volatility Load", t["accent"], "⚡")

# ═══════════════════════════════════════════════════════════════
# 4. ADMISSION HORIZON (IMAGE_E23A07)
# ═══════════════════════════════════════════════════════════════
st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin:1.5rem 0 1rem;'>Admission Horizon — Historical + AI Projection</div>", unsafe_allow_html=True)

fig_horizon = go.Figure()

# Confidence Band
fig_horizon.add_trace(go.Scatter(x=forecast_dates, y=conf_upper, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig_horizon.add_trace(go.Scatter(x=forecast_dates, y=conf_lower, mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(255,170,0,0.1)", showlegend=False, hoverinfo="skip"))

# Validated History
fig_horizon.add_trace(go.Scatter(x=history["date"], y=history["daily_admissions"], name="Validated History", line=dict(color="#00d4ff", width=3)))

# AI Projection
fig_horizon.add_trace(go.Scatter(x=forecast_dates, y=forecast_vals, name="Nexus AI Projection", line=dict(color="#ffaa00", width=4, dash="dash"), marker=dict(size=8)))

# Critical Threshold Line
fig_horizon.add_hline(y=CAPACITY_LIMIT, line=dict(color=t["critical"], width=2, dash="dot"), annotation_text=f"Critical Capacity ({CAPACITY_LIMIT})", annotation_font=dict(color=t["critical"]))

fig_horizon.update_layout(
    margin=dict(l=0, r=0, t=30, b=0), height=400,
    hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=t["text"]),
    xaxis=dict(gridcolor="rgba(255,255,255,0.1)", showline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.1)", showline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
)
st.plotly_chart(fig_horizon, use_container_width=True, config={'displayModeBar': False})

# ═══════════════════════════════════════════════════════════════
# 5. DAY-BY-DAY FORECAST BREAKDOWN (IMAGE_E23A4A)
# ═══════════════════════════════════════════════════════════════
st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin:2rem 0 1rem;'>Day-by-Day Forecast Breakdown</div>", unsafe_allow_html=True)

# Prepare DataFrame for Table and Bar Chart
forecast_df = pd.DataFrame({
    "Date": [d.strftime("%a, %d %b") for d in forecast_dates[1:]],
    "Forecast": [int(v) for v in forecast_vals[1:]],
    "Lower (-15%)": [int(v) for v in conf_lower[1:]],
    "Upper (+15%)": [int(v) for v in conf_upper[1:]]
})

# Calculate "vs Capacity" status
forecast_df["vs Capacity"] = forecast_df["Forecast"].apply(
    lambda x: f"🔴 +{x - CAPACITY_LIMIT}" if x >= CAPACITY_LIMIT else f"🟢 -{CAPACITY_LIMIT - x}"
)

# Bar Chart
bar_colors = [t["critical"] if v >= CAPACITY_LIMIT else "#ffaa00" for v in forecast_df["Forecast"]]
fig_bars = go.Figure(go.Bar(
    x=forecast_df["Date"], y=forecast_df["Forecast"],
    marker_color=bar_colors, text=forecast_df["Forecast"], textposition='auto'
))
fig_bars.add_hline(y=CAPACITY_LIMIT, line=dict(color=t["critical"], width=1, dash="dot"))
fig_bars.update_layout(
    margin=dict(l=0, r=0, t=10, b=0), height=300,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=t["text"]),
    xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(255,255,255,0.1)")
)
st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})

# Data Table
st.dataframe(
    forecast_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Forecast": st.column_config.NumberColumn(format="%d"),
        "Lower (-15%)": st.column_config.NumberColumn(format="%d"),
        "Upper (+15%)": st.column_config.NumberColumn(format="%d"),
    }
)