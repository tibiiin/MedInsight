import streamlit as st
import pandas as pd
from data_engine import get_patient_data
from components import setup_page, render_sidebar, render_header, render_kpi
from styles import get_chart_config

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Patient Data", "📂", "patient_data")
chart_cfg = get_chart_config()
render_sidebar("patient_data", "📂")

# ═══════════════════════════════════════════════════════════════
# 2. DATA LOAD 
# ═══════════════════════════════════════════════════════════════
df_patients = get_patient_data()

if df_patients.empty:
    st.warning("Patient Data not found or loading.")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# 3. PAGE HEADER
# ═══════════════════════════════════════════════════════════════
render_header(
    title="Patient Census Directory",
    subtitle="Secure Records · Identity Verified",
    icon="📂",
    right_badge="ACCESS LOGGED",
    right_color=t["success"]
)

# ═══════════════════════════════════════════════════════════════
# 4. KPI SUMMARY ROW
# ═══════════════════════════════════════════════════════════════
total_pts = len(df_patients)
avg_stay = df_patients['los_days'].mean() if not df_patients.empty else 0
high_impact_count = len(df_patients[df_patients['los_days'] > 5])

k1, k2, k3, k4 = st.columns(4)
render_kpi(k1, "Total Active", str(total_pts), "Current Census", t["info"], "👥")
render_kpi(k2, "Avg Length of Stay", f"{avg_stay:.1f} Days", "Institutional Avg", t["text"], "⏱")
render_kpi(k3, "High-Pressure", str(high_impact_count), "LOS > 5 Days", t["warning"], "🚨")

if not df_patients.empty:
    ward_stats = df_patients.groupby('department')['los_days'].mean()
    bottleneck_ward = ward_stats.idxmax()
    avg_bottleneck = ward_stats.max()
    render_kpi(k4, "Critical Node", bottleneck_ward, f"{avg_bottleneck:.1f} Days Avg LOS", t["critical"], "⚠️")
else:
    render_kpi(k4, "Critical Node", "N/A", "Insufficient Data", t["text"], "⚠️")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. TACTICAL FILTERS
# ═══════════════════════════════════════════════════════════════
st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin-bottom:1rem;'>Filter Records</div>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns([1.5, 1.5, 1], gap="medium")
with col_a:
    dept_filter = st.multiselect("Filter by Ward", options=sorted(df_patients['department'].unique()), placeholder="Select Departments...")
with col_b:
    search_id = st.text_input("Search Patient ID", placeholder="e.g. PT065...")
with col_c:
    st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True) 
    high_impact = st.toggle("🚨 High-Pressure Only", help="Shows patients with LOS > 5 days", value=False)

# Apply Filters
filtered_df = df_patients.copy()
if dept_filter:
    filtered_df = filtered_df[filtered_df['department'].isin(dept_filter)]
if search_id:
    filtered_df = filtered_df[filtered_df['patient_id'].astype(str).str.contains(search_id, case=False)]
if high_impact:
    filtered_df = filtered_df[filtered_df['los_days'] > 5]

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 6. REFINED DATA TABLE
# ═══════════════════════════════════════════════════════════════
st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin-bottom:1rem;'>Active Census: {len(filtered_df)} Records Found</div>", unsafe_allow_html=True)

columns_to_show = ["patient_id", "department", "admission_date", "los_days", "adjusted_treatment_minutes"]

# Removed the hardcoded sort so operators can click the headers to sort as they please
st.dataframe(
    filtered_df[columns_to_show],
    use_container_width=True,
    hide_index=True,
    column_config={
        "patient_id": st.column_config.TextColumn("Ref ID"),
        "department": st.column_config.TextColumn("Ward Location"),
        "admission_date": st.column_config.TextColumn("Date Admitted"),
        "los_days": st.column_config.NumberColumn("Length of Stay", format="%.1f Days"),
        "adjusted_treatment_minutes": st.column_config.ProgressColumn(
            "Intensity Load",
            format="%d%%", 
            min_value=0,
            max_value=100, 
            color=t["info"] 
        ),
    }
)