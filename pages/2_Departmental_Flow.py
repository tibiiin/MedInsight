import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from data_engine import get_system_data, get_utilization_data
from styles import get_chart_config
from components import setup_page, render_sidebar, render_kpi, render_header

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Departmental Flow", "🏥", "flow")
chart_cfg = get_chart_config()
render_sidebar("flow", "⬡")

# ═══════════════════════════════════════════════════════════════
# 2. DATA LOAD
# ═══════════════════════════════════════════════════════════════
_, df_demand = get_system_data()
df_util      = get_utilization_data()

if df_util.empty or df_demand.empty:
    st.warning("Data files are still loading or missing.")
    st.stop()

latest_date  = df_util["date"].max()
live_util    = df_util[df_util["date"] == latest_date]

# ═══════════════════════════════════════════════════════════════
# 3. PAGE HEADER
# ═══════════════════════════════════════════════════════════════
render_header(
    title="Departmental Pulse & Flow", 
    subtitle=f"Institutional Intelligence Node · {latest_date}", 
    icon="🏥", 
    right_badge=f"{len(live_util)} Wards Active", 
    right_color=t["info"]
)

# ═══════════════════════════════════════════════════════════════
# 4. KPI SUMMARY ROW
# ═══════════════════════════════════════════════════════════════
avg_util    = live_util["doctor_utilization_pct"].mean()
critical_ct = (live_util["doctor_utilization_pct"] >= 85).sum()
warning_ct  = ((live_util["doctor_utilization_pct"] >= 70) & 
               (live_util["doctor_utilization_pct"] < 85)).sum()
healthy_ct  = (live_util["doctor_utilization_pct"] < 70).sum()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
render_kpi(kpi1, "Avg Utilisation", f"{avg_util:.1f}%", "Across all wards", t["info"])
render_kpi(kpi2, "Critical Wards", str(critical_ct), "≥85% capacity", t["critical"])
render_kpi(kpi3, "Warning Wards", str(warning_ct), "70–84% capacity", t["warning"])
render_kpi(kpi4, "Healthy Wards", str(healthy_ct), "<70% capacity", t["success"])

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. DEPARTMENTAL GAUGES
# ═══════════════════════════════════════════════════════════════
st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin-bottom:1rem;'>Capacity Pressure per Ward</div>", unsafe_allow_html=True)

gauge_cols = st.columns(len(live_util))

for i, (_, row) in enumerate(live_util.iterrows()):
    with gauge_cols[i]:
        val = row["doctor_utilization_pct"]
        if val >= 85:
            g_color, status_label = t["critical"], "CRITICAL"
        elif val >= 70:
            g_color, status_label = t["warning"], "WARNING"
        else:
            g_color, status_label = t["success"], "HEALTHY"

        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=val,
            title={"text": row["department"], "font": {"size": 13, "color": chart_cfg["text_color"]}},
            number={"suffix": "%", "font": {"color": g_color, "size": 28}},
            gauge={
                "axis": {"range": [None, 100], "tickwidth": 1, "tickcolor": chart_cfg["tick_color"]},
                "bar": {"color": g_color, "thickness": 0.7},
                "bgcolor": t["card"], "borderwidth": 1, "bordercolor": t["border"],
                "steps": [
                    {"range": [0, 70], "color": t["success_dim"]},
                    {"range": [70, 85], "color": t["warning_dim"]},
                    {"range": [85, 100], "color": t["critical_dim"]},
                ],
                "threshold": {"line": {"color": g_color, "width": 2}, "thickness": 0.8, "value": val},
            },
        ))

        fig.update_layout(height=220, margin=dict(l=16, r=16, t=44, b=10), **chart_cfg["common_layout"])
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"<div style='text-align:center;margin-top:-8px;margin-bottom:8px;'><span style='font-size:0.78rem;font-weight:700;letter-spacing:0.1em;color:{g_color};text-transform:uppercase;'>{status_label}</span></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 6. BOTTLENECK DETECTION SECTION
# ═══════════════════════════════════════════════════════════════
st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin:1.5rem 0 1rem;'>Bottleneck Detection</div>", unsafe_allow_html=True)

left, right = st.columns(2, gap="large")

with left:
    df_bar = live_util[["department", "adjusted_treatment_minutes", "daily_capacity_minutes"]].copy()
    df_bar = df_bar.rename(columns={"adjusted_treatment_minutes": "Treatment Load", "daily_capacity_minutes": "Capacity", "department": "Department"})
    
    cap_color = t["border"] if st.session_state.theme == "dark" else "#adb5bd"

    fig_bar = px.bar(
        df_bar, x="Department", y=["Treatment Load", "Capacity"], barmode="group",
        color_discrete_map={"Treatment Load": t["info"], "Capacity": cap_color},
        template=chart_cfg["template"], labels={"value": "Minutes", "variable": ""}
    )
    fig_bar.update_layout(
        **chart_cfg["common_layout"],
        title=dict(text="Workload vs. Capacity (Minutes)", font=dict(size=13, color=chart_cfg["text_color"])),
        legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0),
        xaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"]), tickangle=-30, title_text=""),
        yaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"]), title_text="Minutes"),
        margin=dict(l=10, r=10, t=45, b=100),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    # Safely filter out columns we don't want to plot
    exclude = {"date", "is_surge", "base_trend", "is_weekend", "surge_multiplier", "daily_admissions", "noise", "weekend_multiplier", "daily_number", "day_number"}
    dept_cols = [c for c in df_demand.columns if c not in exclude]

    DEPT_COLORS = {"Emergency": "#ef4444", "General Medicine": "#22c55e", "Cardiology": "#818cf8", "Orthopedics": "#f97316", "Neurology": "#e879f9", "ICU": "#06b6d4"}
    
    fig_line = px.line(
        df_demand.tail(7), x="date", y=dept_cols, template=chart_cfg["template"],
        color_discrete_map=DEPT_COLORS, labels={"value": "Admissions", "variable": "Department", "date": "Date"}, markers=True
    )
    
    fig_line.update_layout(
        **chart_cfg["common_layout"],
        title=dict(text="Weekly Demand Trends (7-day)", font=dict(size=13, color=chart_cfg["text_color"])),
        hovermode="x unified",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(l=10, r=110, t=40, b=10),
        xaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"])),
        yaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"])),
    )
    st.plotly_chart(fig_line, use_container_width=True)