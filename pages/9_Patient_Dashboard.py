import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from components import setup_page, render_sidebar, render_header, render_kpi
from styles import get_theme, get_chart_config, apply_custom_css
from data_engine import load_comprehensive_data, get_safe_col

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Patient Analytics", "📈", "analytics")
chart_cfg = get_chart_config()
render_sidebar("analytics", "📈")

apply_custom_css()

# 🛠️ UI HELPERS (Direct HTML Injection to prevent raw code rendering)
def section_hdr(title):
    st.markdown(f"""
    <div style='font-size:0.85rem; font-weight:700; letter-spacing:0.1em; 
                text-transform:uppercase; color:{t['text']}; 
                border-bottom:1px solid {t['border']}; 
                padding-bottom:0.5rem; margin:2rem 0 1rem;'>
        {title}
    </div>
    """,unsafe_allow_html=True)

def hex_to_rgba(hex_color, opacity=0.15):
    hex_color = hex_color.lstrip('#')
    return f"rgba({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}, {opacity})"

# ═══════════════════════════════════════════════════════════════
# 2. LOAD DATA
# ═══════════════════════════════════════════════════════════════
data = load_comprehensive_data()

patients = data.get("patients", pd.DataFrame())
admissions = data.get("admissions", pd.DataFrame())
satisfaction = data.get("satisfaction", pd.DataFrame())

if patients.empty or admissions.empty:
    st.error("Critical Data Missing. Please ensure 'final_healthcare_dataset.xlsx' is in the 'data/' folder.")
    st.stop()

# Safe Column Mapping
age_col = get_safe_col(patients, ["age"])
gender_col = get_safe_col(patients, ["gender"])
state_col = get_safe_col(patients, ["state"])
payment_col = get_safe_col(patients, ["insurance"])
dept_col = get_safe_col(admissions, ["department", "dept"])
date_col = get_safe_col(admissions, ["date", "admission_date"])
los_col = get_safe_col(admissions, ["length_of_stay", "los"])
satisfaction_col = get_safe_col(satisfaction, ["satisfaction", "score"])

# ═══════════════════════════════════════════════════════════════
# 3. KPIs
# ═══════════════════════════════════════════════════════════════
avg_age = round(patients[age_col].mean(), 1) if age_col else 0
avg_satisfaction = round(satisfaction[satisfaction_col].mean(), 1) if satisfaction_col else 0

render_header("Patient Insights", "Historical outcomes and demographic trends.", "📈")

k1, k2, k3, k4 = st.columns(4)
render_kpi(k1, "Total Patients", f"{len(patients):,}", "Database records", t["info"], "👥")
render_kpi(k2, "Admissions", f"{len(admissions):,}", "Total stays", t["success"], "🏥")
render_kpi(k3, "Average Age", f"{avg_age} yrs", "Patient mean", t["text"], "⏳")
render_kpi(k4, "Satisfaction", f"{avg_satisfaction}/5", "Survey average", t["accent"], "⭐")

# ═══════════════════════════════════════════════════════════════
# 4. TRENDS (SPACED & TITLED)
# ═══════════════════════════════════════════════════════════════
section_hdr("Admissions & Length of Stay Timeline")

if date_col and los_col:
    df_admissions = admissions.copy()
    df_admissions[date_col] = pd.to_datetime(df_admissions[date_col], errors='coerce')
    df_admissions['Month'] = df_admissions[date_col].dt.to_period("M").dt.to_timestamp()
    
    trend_df = df_admissions.groupby("Month").agg({los_col: "mean", date_col: "count"}).reset_index()
    trend_df.columns = ["Month", "Avg_LOS", "Patients"]
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df["Month"], y=trend_df["Patients"], mode='lines', name='Admissions',
        line=dict(color=t["success"], width=3, shape='spline'),
        fill='tozeroy', fillcolor=hex_to_rgba(t["success"], 0.1)
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend_df["Month"], y=trend_df["Avg_LOS"], mode='lines+markers', name='Avg LOS',
        line=dict(color=t["accent"], width=2), yaxis='y2'
    ))
    
    fig_trend.update_layout(
        **chart_cfg["common_layout"], height=400,
        margin=dict(l=60, r=60, t=20, b=80), 
        xaxis=dict(showgrid=False, tickangle=-45),
        yaxis=dict(title="Admissions", gridcolor=chart_cfg["grid_color"]),
        yaxis2=dict(title="Days", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

# ═══════════════════════════════════════════════════════════════
# 5. DEMOGRAPHICS & DEPARTMENTS (FIXED LABELS)
# ═══════════════════════════════════════════════════════════════
c1, c2 = st.columns([1, 1.2], gap="large")

with c1:
    section_hdr("Department Load")
    if dept_col:
        dept_counts = admissions[dept_col].value_counts().reset_index()
        dept_counts.columns = [dept_col, "Count"]
        
        fig_pie = go.Figure(go.Pie(
            labels=dept_counts[dept_col], values=dept_counts["Count"], 
            hole=0.6, textinfo='percent', textposition='outside'
        ))
        fig_pie.update_layout(
            **chart_cfg["common_layout"], height=400,
            margin=dict(l=20, r=100, t=10, b=10),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    section_hdr("Age Groups by Gender")
    if age_col and gender_col:
        fig_hist = px.histogram(
            patients, x=age_col, color=gender_col, 
            nbins=12, barmode='group',
            color_discrete_sequence=[t["info"], t["accent"]]
        )
        fig_hist.update_layout(
            **chart_cfg["common_layout"], height=400, 
            margin=dict(l=50, r=20, t=10, b=60),
            xaxis_title="Age", yaxis_title="Count",
            legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# 6. GEOGRAPHY & READMISSIONS
# ═══════════════════════════════════════════════════════════════
c3, c4 = st.columns(2, gap="large")

with c3:
    section_hdr("Top 5 States")
    if state_col:
        state_df = patients[state_col].value_counts().nlargest(10).reset_index()
        state_df.columns = ["State", "Count"]
        fig_state = px.bar(state_df.sort_values("Count"), x="Count", y="State", orientation='h', color_discrete_sequence=[t["info"]])
        fig_state.update_layout(**chart_cfg["common_layout"], height=400, margin=dict(l=10, r=20, t=10, b=40))
        st.plotly_chart(fig_state, use_container_width=True)

with c4:
    section_hdr("Readmission Flag")
    if state_col:
        # Simplified readmission view
        readmit_df = admissions[get_safe_col(admissions, ["readmission"])].value_counts().reset_index()
        readmit_df.columns = ["Status", "Count"]
        fig_re = px.bar(readmit_df, x="Status", y="Count", color="Status", color_discrete_sequence=[t["success"], t["warning"]])
        fig_re.update_layout(**chart_cfg["common_layout"], height=400, margin=dict(l=50, r=20, t=10, b=40), showlegend=False)
        st.plotly_chart(fig_re, use_container_width=True)