import streamlit as st
import plotly.graph_objects as go
import random
import json
import os
from datetime import datetime, timedelta
from components import setup_page, render_sidebar, render_header, render_kpi
from styles import get_theme, get_chart_config

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Ward Capacity", "🛏️", "patient_flow")
chart_cfg = get_chart_config()
render_sidebar("patient_flow", "🛏️")

# ═══════════════════════════════════════════════════════════════
# 2. PERSISTENT DATA ENGINE
# ═══════════════════════════════════════════════════════════════
DB_FILE = "data/ward_state.json"
DEPARTMENTS = ["Emergency", "Cardiology", "Neurology", "Orthopaedics", "Paediatrics", "General Ward", "ICU"]
BED_CAPACITY = {"Emergency": 20, "Cardiology": 18, "Neurology": 16, "Orthopaedics": 14, "Paediatrics": 12, "General Ward": 30, "ICU": 10}
PATIENT_NAMES = ["Ravi Shankar", "Sunita Desai", "Venkatesh Reddy", "Kavitha Nair", "Mohan Lal Gupta", "Lakshmi Krishnan", "Pooja Tiwari", "Subramaniam Pillai", "Geeta Bhandari", "Harish Chandra Tata", "Anita Rao", "Rajesh Kumar", "Meena Pillai", "Arjun Patel", "Divya Menon", "Sanjay Iyer"]
DISCHARGE_REASONS = ["Recovery complete", "Transferred to rehab", "Patient request", "Doctor clearance", "Post-op stable", "Observation period over"]

def load_ward_state():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return None

def save_ward_state():
    state_to_save = {
        "bed_state": st.session_state.bed_state,
        "discharge_list": st.session_state.discharge_list,
        "admission_list": st.session_state.admission_list
    }
    os.makedirs("data", exist_ok=True)
    with open(DB_FILE, "w") as f: json.dump(state_to_save, f)

saved_state = load_ward_state()

if "bed_state" not in st.session_state:
    if saved_state:
        st.session_state.bed_state = saved_state["bed_state"]
        st.session_state.discharge_list = saved_state["discharge_list"]
        st.session_state.admission_list = saved_state["admission_list"]
    else:
        now = datetime.now()
        st.session_state.bed_state = {dept: {"occupied": min(cap - random.randint(1, 4), cap), "capacity": cap} for dept, cap in BED_CAPACITY.items()}
        
        # Init Discharges
        discharges = []
        for i in range(random.randint(6, 12)):
            dept = random.choice(DEPARTMENTS)
            disc_time = now.replace(hour=8, minute=0) + timedelta(hours=random.randint(0, 10), minutes=random.choice([0, 15, 30, 45]))
            discharges.append({
                "id": i + 1, "patient": random.choice(PATIENT_NAMES), "dept": dept,
                "bed": f"{dept[:3].upper()}-{random.randint(1, BED_CAPACITY[dept]):02d}",
                "time": disc_time.strftime("%I:%M %p"), "reason": random.choice(DISCHARGE_REASONS),
                "status": "Completed" if disc_time < now else "Scheduled",
                "priority": random.choice(["Routine", "Routine", "Routine", "Urgent"])
            })
        st.session_state.discharge_list = sorted(discharges, key=lambda x: x["time"])

        # Init Admissions
        admissions = []
        for i in range(random.randint(4, 9)):
            dept = random.choice(DEPARTMENTS)
            adm_time = now.replace(hour=7, minute=0) + timedelta(hours=random.randint(0, 10))
            admissions.append({
                "id": i + 1, "patient": random.choice(PATIENT_NAMES), "dept": dept,
                "time": adm_time.strftime("%I:%M %p"), "status": "Admitted" if adm_time < now else "Pending",
                "condition": random.choice(["Cardiac monitoring", "Post-op recovery", "Trauma", "Respiratory issue", "Fracture", "Neurological eval"])
            })
        st.session_state.admission_list = sorted(admissions, key=lambda x: x["time"])
        save_ward_state()

# ═══════════════════════════════════════════════════════════════
# 3. COMPUTED METRICS
# ═══════════════════════════════════════════════════════════════
total_beds = sum(v["capacity"] for v in st.session_state.bed_state.values())
total_occupied = sum(v["occupied"] for v in st.session_state.bed_state.values())
total_free = total_beds - total_occupied
occupancy_pct = round((total_occupied / total_beds) * 100, 1)

discharged_today = len([d for d in st.session_state.discharge_list if d["status"] == "Completed"])
scheduled_today = len([d for d in st.session_state.discharge_list if d["status"] == "Scheduled"])
admitted_today = len([a for a in st.session_state.admission_list if a["status"] == "Admitted"])
pending_admission = len([a for a in st.session_state.admission_list if a["status"] == "Pending"])
net_change = admitted_today - discharged_today

occ_label = "CRITICAL" if occupancy_pct >= 90 else "HIGH" if occupancy_pct >= 75 else "NORMAL"
occ_color = t["critical"] if occupancy_pct >= 90 else t["warning"] if occupancy_pct >= 75 else t["success"]

def section_hdr(title, icon=""):
    st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin:1.5rem 0 1rem;'>{icon}&nbsp; {title}</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 4. SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("---")
    st.markdown(f"""
    <div style="padding:14px 16px;background:{t['surface']};border:1px solid {t['border']};border-radius:10px;margin-bottom:0.75rem;">
        <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{t['text_muted']};margin-bottom:10px;">Bed Status</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Occupancy</span><span style="font-size:0.95rem;font-weight:700;color:{occ_color};">{occupancy_pct}%</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Occupied</span><span style="font-size:0.95rem;font-weight:700;color:{t['text']};">{total_occupied} / {total_beds}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Available</span><span style="font-size:0.95rem;font-weight:700;color:{t['success']};">{total_free}</span></div>
    </div>
    <div style="padding:14px 16px;background:{t['surface']};border:1px solid {t['border']};border-radius:10px;">
        <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{t['text_muted']};margin-bottom:10px;">Today's Movement</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Discharged</span><span style="font-size:0.95rem;font-weight:700;color:{t['success']};">{discharged_today}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Admitted</span><span style="font-size:0.95rem;font-weight:700;color:{t['info']};">{admitted_today}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Net Change</span><span style="font-size:0.95rem;font-weight:700;color:{t['critical'] if net_change > 0 else t['success']};">{"+" if net_change > 0 else ""}{net_change}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. HEADER & KPIs
# ═══════════════════════════════════════════════════════════════
render_header("Ward Capacity & Flow", f"Bed availability · Admissions · Discharges · {datetime.now().strftime('%d %b %Y, %I:%M %p')}", "🛏️", f"{occ_label} — {occupancy_pct}% OCCUPIED", occ_color)

k1, k2, k3, k4, k5, k6 = st.columns(6)
render_kpi(k1, "Total Beds", str(total_beds), "hospital capacity", t["text"])
render_kpi(k2, "Occupied", str(total_occupied), f"{occupancy_pct}% occupancy", occ_color)
render_kpi(k3, "Available Now", str(total_free), "ready for admission", t["success"])
render_kpi(k4, "Discharged Today", str(discharged_today), f"{scheduled_today} pending", t["success"])
render_kpi(k5, "Admitted Today", str(admitted_today), f"{pending_admission} pending", t["info"])
render_kpi(k6, "Net Bed Change", f"{'+'if net_change>0 else ''}{net_change}", "admissions minus discharges", t["critical"] if net_change > 3 else t["success"])

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 6. BED OCCUPANCY CHARTS
# ═══════════════════════════════════════════════════════════════
section_hdr("Department Bed Occupancy")

chart_l, chart_r = st.columns([2, 1], gap="large")

with chart_l:
    depts = list(st.session_state.bed_state.keys())
    occupied = [st.session_state.bed_state[d]["occupied"] for d in depts]
    free_beds = [st.session_state.bed_state[d]["capacity"] - o for d, o in zip(depts, occupied)]
    occ_pcts = [round(o / st.session_state.bed_state[d]["capacity"] * 100, 1) for d, o in zip(depts, occupied)]
    bar_colors = [t["critical"] if p >= 90 else t["warning"] if p >= 75 else t["success"] for p in occ_pcts]

    fig_beds = go.Figure()
    fig_beds.add_trace(go.Bar(name="Occupied", x=depts, y=occupied, marker_color=bar_colors, marker_line=dict(width=0), hovertemplate="<b>%{x}</b><br>Occupied: %{y}<extra></extra>"))
    fig_beds.add_trace(go.Bar(name="Available", x=depts, y=free_beds, marker_color=t["surface"], marker_line=dict(width=1, color=t["border"]), hovertemplate="<b>%{x}</b><br>Available: %{y}<extra></extra>"))
    fig_beds.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t["text"]), barmode="stack", xaxis=dict(showgrid=False), yaxis=dict(gridcolor=chart_cfg["grid_color"]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_beds, use_container_width=True, config={'displayModeBar': False})

with chart_r:
    fig_donut = go.Figure(go.Pie(labels=["Occupied", "Available"], values=[total_occupied, total_free], hole=0.65, marker=dict(colors=[occ_color, t["surface"]], line=dict(color=t["bg"], width=2)), textfont=dict(color=t["text"], size=11), hovertemplate="<b>%{label}</b><br>%{value} beds (%{percent})<extra></extra>"))
    fig_donut.add_annotation(text=f"<b>{occupancy_pct}%</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=26, color=occ_color, family="Inter"))
    fig_donut.update_layout(margin=dict(l=0, r=0, t=10, b=10), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t["text"]), legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
with st.expander("⚙️ Manual Bed Update"):
    mu1, mu2, mu3 = st.columns(3)
    upd_dept = mu1.selectbox("Department", DEPARTMENTS, key="upd_dept")
    upd_action = mu2.selectbox("Action", ["Admit Patient (+1)", "Discharge Patient (−1)"], key="upd_action")
    mu3.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    if mu3.button("Apply", key="apply_bed_upd", use_container_width=True):
        bs = st.session_state.bed_state[upd_dept]
        if "Admit" in upd_action:
            if bs["occupied"] < bs["capacity"]: bs["occupied"] += 1; st.success(f"Patient admitted to {upd_dept}.")
            else: st.error(f"{upd_dept} is at full capacity.")
        else:
            if bs["occupied"] > 0: bs["occupied"] -= 1; st.success(f"Bed vacated in {upd_dept}.")
            else: st.error(f"No occupied beds in {upd_dept}.")
        save_ward_state()
        st.rerun()

# ═══════════════════════════════════════════════════════════════
# 7. TODAY'S DISCHARGES & ADMISSIONS
# ═══════════════════════════════════════════════════════════════
col_disc, col_adm = st.columns(2, gap="large")

with col_disc:
    section_hdr("Today's Discharges", "🚪")
    
    pending_discs = [d for d in st.session_state.discharge_list if d["status"] == "Scheduled"]
    if pending_discs:
        d_sel = st.selectbox("Mark Discharge Complete", pending_discs, format_func=lambda d: f"{d['patient']} ({d['dept']} - {d['bed']})", key="disc_sel")
        if st.button("✅ Confirm Discharge", use_container_width=True):
            for d in st.session_state.discharge_list:
                if d["id"] == d_sel["id"]: d["status"] = "Completed"
            bs = st.session_state.bed_state[d_sel["dept"]]
            if bs["occupied"] > 0: bs["occupied"] -= 1
            save_ward_state()
            st.rerun()
    
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    disc_headers = "".join([f"<div style='font-size:0.75rem;font-weight:700;color:{t['text_muted']};text-transform:uppercase;'>{h}</div>" for h in ["Patient", "Bed", "Status"]])
    st.markdown(f"<div style='display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;padding:8px 4px;border-bottom:1px solid {t['border']};'>{disc_headers}</div>", unsafe_allow_html=True)
    
    for d in st.session_state.discharge_list:
        sc = t["success"] if d["status"] == "Completed" else t["warning"]
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;padding:10px 4px;border-bottom:1px solid {t['border_subtle']};align-items:center;">
            <div><div style="font-size:0.9rem;font-weight:600;color:{t['text']};">{d['patient']}</div><div style="font-size:0.75rem;color:{t['text_secondary']};">{d['time']}</div></div>
            <div style="font-size:0.82rem;font-family:monospace;color:{t['text']};">{d['bed']}</div>
            <div><span style="font-size:0.75rem;font-weight:700;padding:2px 10px;border-radius:99px;background:{t['surface']};color:{sc};border:1px solid {sc};">{d['status']}</span></div>
        </div>
        """, unsafe_allow_html=True)

with col_adm:
    section_hdr("Today's Admissions", "📥")
    st.markdown("<div style='height:4.8rem'></div>", unsafe_allow_html=True) # Spacer to align with discharge action
    
    adm_headers = "".join([f"<div style='font-size:0.75rem;font-weight:700;color:{t['text_muted']};text-transform:uppercase;'>{h}</div>" for h in ["Patient", "Dept", "Status"]])
    st.markdown(f"<div style='display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;padding:8px 4px;border-bottom:1px solid {t['border']};'>{adm_headers}</div>", unsafe_allow_html=True)
    
    for a in st.session_state.admission_list:
        sc = t["success"] if a["status"] == "Admitted" else t["info"]
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;padding:10px 4px;border-bottom:1px solid {t['border_subtle']};align-items:center;">
            <div><div style="font-size:0.9rem;font-weight:600;color:{t['text']};">{a['patient']}</div><div style="font-size:0.75rem;color:{t['text_secondary']};">{a['time']}</div></div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">{a['dept']}</div>
            <div><span style="font-size:0.75rem;font-weight:700;padding:2px 10px;border-radius:99px;background:{t['surface']};color:{sc};border:1px solid {sc};">{a['status']}</span></div>
        </div>
        """, unsafe_allow_html=True)