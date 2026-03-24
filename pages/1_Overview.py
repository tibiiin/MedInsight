import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from data_engine import get_system_data, get_live_metrics
from components import setup_page, render_sidebar, render_kpi, render_header
from styles import get_chart_config

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Institutional Overview", "🏥", "overview")
chart_cfg = get_chart_config()
render_sidebar("overview", "🏥")

# ═══════════════════════════════════════════════════════════════
# 2. DATA LOAD 
# ═══════════════════════════════════════════════════════════════
df_kpi, df_demand = get_system_data()

if df_kpi.empty or df_demand.empty:
    st.warning("Data files are still loading or missing.")
    st.stop()

live, yesterday = get_live_metrics()

# Risk thresholds
CRITICAL_THRESHOLD = 80
WARNING_THRESHOLD = 60
risk_score = live.get('risk_score', 0)

if risk_score >= CRITICAL_THRESHOLD:
    risk_color, risk_label, badge_text = t["critical"], "CRITICAL STRAIN", "CRITICAL RISK"
    risk_dim = t["critical_dim"]
    actions = [
        "Activate ICU Step-down protocols immediately.",
        "Review pending discharges across all wards."
    ]
    icon = "🚨"
elif risk_score >= WARNING_THRESHOLD:
    risk_color, risk_label, badge_text = t["warning"], "ELEVATED STRAIN", "ELEVATED RISK"
    risk_dim = t["warning_dim"]
    actions = [
        "Monitor discharge rates closely.",
        "Consider activating surge protocols."
    ]
    icon = "⚠️"
else:
    risk_color, risk_label, badge_text = t["success"], "OPERATIONS STABLE", "NOMINAL RISK"
    risk_dim = t["success_dim"]
    actions = [
        "All systems operating within normal parameters.",
        "Continue routine monitoring."
    ]
    icon = "✅"

# ═══════════════════════════════════════════════════════════════
# 3. PAGE HEADER
# ═══════════════════════════════════════════════════════════════
render_header(
    title="Institutional Overview",
    subtitle=f"Command Node · {live.get('date', 'Live')} · Status: Active",
    icon="🏥",
    right_badge=badge_text,
    right_color=risk_color
)

# ═══════════════════════════════════════════════════════════════
# 4. KPI SUMMARY ROW
# ═══════════════════════════════════════════════════════════════
k1, k2, k3, k4 = st.columns(4)

render_kpi(k1, "Daily Census", f"{int(live['daily_admissions'])}", "Admissions Today", t["info"], "🏨")
render_kpi(k2, "Occupancy Rate", f"{live['bed_occupancy_pct']:.1f}%", "System Capacity", t["text"], "🛏")
render_kpi(k3, "Avg LOS", f"{live['avg_los']:.1f} Days", "Flow Efficiency", t["text"], "⏱")

# Custom styled Risk KPI to match your older design
k4.markdown(f"""
<div class="kpi-box" style="border-color:{risk_color}!important; background:{risk_dim}!important;">
    <div class="kpi-label" style="color:{risk_color}!important;">⚠ Risk Score</div>
    <div class="kpi-value" style="color:{risk_color}!important;">{risk_score:.1f}</div>
    <div style="font-size:0.875rem;color:{risk_color};margin-top:4px;font-weight:700;letter-spacing:0.08em;">{risk_label}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. PRIORITY ACTIONS & 30-DAY TREND
# ═══════════════════════════════════════════════════════════════
col_action, col_trend = st.columns([1, 2], gap="large")

with col_action:
    st.markdown(f"""
    <div style="font-size:0.82rem;font-weight:700;letter-spacing:0.08em; text-transform:uppercase;
                color:{t['text']}; border-bottom:1px solid {t['border']}; padding-bottom:0.5rem; margin-bottom:1rem;">
        Priority Actions
    </div>
    """, unsafe_allow_html=True)

    # Action Card
    st.markdown(f"""
    <div style="background:{risk_dim}; border:1px solid {risk_color}; border-radius:12px; padding:1.25rem; margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="font-size:1.1rem;">{icon}</span>
            <span style="font-weight:700;color:{risk_color};font-size:1rem;letter-spacing:0.04em;">{risk_label}</span>
        </div>
        <div style="font-size:1.85rem;font-weight:700;color:{risk_color};line-height:1;margin-bottom:8px;">{risk_score:.1f}</div>
        <div style="font-size:0.9rem;color:{t['text_secondary']};line-height:1.6;">
            {'<br>'.join(actions)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Secondary Metrics
    adm_30d = int(df_kpi["daily_admissions"].tail(30).mean())
    peak_adm = int(df_kpi["daily_admissions"].max())
    surge_days = int(df_kpi["capacity_strain"].sum()) if "capacity_strain" in df_kpi.columns else "—"

    for label, val, color in [
        ("30-Day Avg Admissions", str(adm_30d), t["text_secondary"]),
        ("Peak Single Day", str(peak_adm), t["warning"]),
        ("Surge Days (Total)", str(surge_days), t["critical"]),
    ]:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center; padding:8px 0;border-bottom:1px solid {t['border_subtle']};">
            <span style="font-size:0.875rem;color:{t['text_secondary']};">{label}</span>
            <span style="font-size:1rem;font-weight:700;color:{color};">{val}</span>
        </div>
        """, unsafe_allow_html=True)

with col_trend:
    st.markdown(f"""
    <div style="font-size:0.82rem;font-weight:700;letter-spacing:0.08em; text-transform:uppercase;
                color:{t['text']}; border-bottom:1px solid {t['border']}; padding-bottom:0.5rem; margin-bottom:1rem;">
        30-Day System Strain Analytics
    </div>
    """, unsafe_allow_html=True)

    fig_strain = go.Figure()

    fig_strain.add_trace(go.Scatter(
        x=df_kpi["date"], y=df_kpi["bed_occupancy_pct"],
        name="Bed Occupancy (%)", 
        line=dict(color=t["warning"], width=2.5),
        fill="tozeroy", fillcolor=t["warning_dim"]
    ))

    fig_strain.add_trace(go.Scatter(
        x=df_kpi["date"], y=df_kpi["avg_doctor_utilization"],
        name="Doctor Utilization (%)", 
        line=dict(color=t["info"], width=2.5)
    ))

    fig_strain.update_layout(
        **chart_cfg["common_layout"],
        template=chart_cfg["template"],
        height=320,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=chart_cfg["text_color"])),
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"])),
        yaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"]), title="Percentage (%)", titlefont=dict(size=11, color=chart_cfg["tick_color"]))
    )
    st.plotly_chart(fig_strain, use_container_width=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 6. MICRO TRENDS (7-DAY BARS & DAILY SPLIT)
# ═══════════════════════════════════════════════════════════════
col_chart1, col_chart2 = st.columns([1.5, 1], gap="large")

with col_chart1:
    st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin-bottom:1rem;'>7-Day Admissions Volume</div>", unsafe_allow_html=True)
    
    df_week = df_kpi.tail(7).copy()
    try:
        df_week['date_str'] = pd.to_datetime(df_week['date']).dt.strftime('%a %d')
    except:
        df_week['date_str'] = df_week['date']
    
    bar_colors = [t["info_dim"]] * 6 + [t["accent"]]
    text_colors = [chart_cfg["tick_color"]] * 6 + [t["accent"]]
    
    fig_bar = go.Figure(go.Bar(
        x=df_week["date_str"], 
        y=df_week["daily_admissions"],
        marker_color=bar_colors,
        marker_line_width=0,
        text=df_week["daily_admissions"].astype(int),
        textposition="outside",
        textfont=dict(size=14, family="Inter", color=text_colors)
    ))
    
    fig_bar.update_layout(
        **chart_cfg["common_layout"],
        template=chart_cfg["template"],
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=chart_cfg["tick_color"], size=13)),
        yaxis=dict(gridcolor=chart_cfg["grid_color"], showticklabels=False, range=[0, df_week["daily_admissions"].max() * 1.2])
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin-bottom:1rem;'>Live Departmental Split</div>", unsafe_allow_html=True)
    
    live_demand = df_demand.iloc[-1]
    depts = ["Emergency", "General Medicine", "Cardiology", "Orthopedics", "Neurology", "ICU"]
    vals = [live_demand.get(d, 0) for d in depts]
    dept_colors = ["#ef4444", "#22c55e", "#818cf8", "#f97316", "#e879f9", "#06b6d4"]
    
    fig_donut = go.Figure(go.Pie(
        labels=depts, 
        values=vals, 
        hole=0.65,
        marker=dict(colors=dept_colors, line=dict(color=t["card"], width=3)),
        textinfo="none",
        hoverinfo="label+value+percent"
    ))
    
    total_admissions = int(sum(vals))
    
    fig_donut.update_layout(
        **chart_cfg["common_layout"],
        template=chart_cfg["template"],
        height=300,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.9, font=dict(color=chart_cfg["text_color"], size=11))
    )
    
    fig_donut.add_annotation(
        text=f"<span style='font-size:28px;font-weight:700;color:{chart_cfg['text_color']}'>{total_admissions}</span><br><span style='font-size:12px;color:{chart_cfg['tick_color']}'>Total Admissions</span>",
        x=0.5, y=0.5, showarrow=False
    )
    
    st.plotly_chart(fig_donut, use_container_width=True)