import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
import json
import os
from datetime import datetime
from components import setup_page, render_sidebar, render_header, render_kpi
from styles import get_theme, get_chart_config

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("MedEvac Command", "🚑", "medevac")
chart_cfg = get_chart_config()
render_sidebar("medevac", "🚑")

st.markdown("""
<style>
.stButton > button, div[data-testid="stButton"] > button {
    background: #00ff88 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 900 !important;
    letter-spacing: 0.03em !important;
    border: none !important;
}
.stButton > button:hover, div[data-testid="stButton"] > button:hover {
    background: #00e57a !important;
    box-shadow: 0 4px 16px rgba(0,255,136,0.35) !important;
}
div[data-baseweb="select"] > div { background-color: #0d1117 !important; border-color: #30363d !important; }
div[data-baseweb="select"] span { color: #f0f4f8 !important; }
div[data-baseweb="menu"] ul, div[data-baseweb="menu"] li { color: #f0f4f8 !important; background-color: #161b22 !important; }
li[aria-selected="true"] { background-color: #1c2330 !important; color: #00ff88 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 2. PERSISTENT DATA ENGINE
# ═══════════════════════════════════════════════════════════════
DB_FILE = "data/medevac_state.json"

def load_medevac_state():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return None

def save_medevac_state():
    state_to_save = {
        "transfer_queue": st.session_state.transfer_queue,
        "hospital_state": st.session_state.hospital_state,
        "patient_roster": st.session_state.patient_roster,
        "transfer_history": st.session_state.transfer_history,
        "next_patient_id": st.session_state.next_patient_id
    }
    os.makedirs("data", exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(state_to_save, f)

PATIENT_NAME_POOL = [
    ("Arjun Sharma", "Emergency", "Trauma"), ("Priya Menon", "Cardiology", "Chest Pain"),
    ("Rajesh Iyer", "ICU", "Respiratory Failure"), ("Divya Nair", "General", "Post-op Recovery"),
    ("Suresh Pillai", "Neurology", "Stroke Observation"), ("Anita Desai", "Emergency", "Fracture"),
    ("Kiran Reddy", "Cardiology", "Arrhythmia"), ("Meena Krishnan", "ICU", "Sepsis"),
    ("Vikram Patel", "Neurology", "TBI Monitoring"), ("Sneha Joshi", "General", "Appendicitis Post-op")
]
PRIORITY_POOL = ["Critical", "High", "High", "Medium", "Medium", "Medium", "Low"]

saved_state = load_medevac_state()

if "hospital_state" not in st.session_state:
    if saved_state:
        st.session_state.transfer_queue = saved_state["transfer_queue"]
        st.session_state.hospital_state = saved_state["hospital_state"]
        st.session_state.patient_roster = saved_state["patient_roster"]
        st.session_state.transfer_history = saved_state["transfer_history"]
        st.session_state.next_patient_id = saved_state["next_patient_id"]
    else:
        st.session_state.transfer_queue = []
        st.session_state.hospital_state = {
            h["name"]: {"beds": h["base_beds"], "load_pct": round(random.uniform(55, 80), 1)}
            for h in [
                {"name": "Apollo Hospitals, Andheri",      "base_beds": 18},
                {"name": "Apollo Hospitals, Navi Mumbai",  "base_beds": 11},
                {"name": "Apollo Hospitals, Bandra",       "base_beds": 0},
                {"name": "Apollo Hospitals, Powai",        "base_beds": 25},
                {"name": "Apollo Hospitals, Worli",        "base_beds": 4},
                {"name": "Apollo Hospitals, Thane",        "base_beds": 9},
            ]
        }
        st.session_state.patient_roster = [
            {"id": 0, "name": "Ravi Shankar", "age": 58, "ward": "ICU", "condition": "Post-ICU Recovery", "status": "Stable", "priority": "High"},
            {"id": 1, "name": "Sunita Desai", "age": 42, "ward": "Cardiology", "condition": "Post-op Observation", "status": "Improving", "priority": "Medium"},
            {"id": 2, "name": "Venkatesh Reddy", "age": 65, "ward": "Neurology", "condition": "Cardiac Monitoring", "status": "Critical", "priority": "Critical"},
            {"id": 3, "name": "Kavitha Nair", "age": 47, "ward": "Cardiology", "condition": "Cardiac Rehab", "status": "Stable", "priority": "Low"},
            {"id": 4, "name": "Mohan Lal Gupta", "age": 63, "ward": "General", "condition": "Respiratory Issue", "status": "Stable", "priority": "Medium"},
            {"id": 5, "name": "Lakshmi Krishnan", "age": 55, "ward": "Emergency", "condition": "Trauma", "status": "Critical", "priority": "Critical"},
        ]
        st.session_state.next_patient_id = 6
        st.session_state.transfer_history = [
            {"id": 1, "patient": "Ravi Shankar", "age": 58, "ward": "ICU", "from": "Arogya Central", "to": "Apollo Hospitals, Andheri", "date": "2026-03-12", "time": "09:15", "status": "Completed", "reason": "ICU overflow", "priority": "Critical"},
            {"id": 2, "patient": "Sunita Desai", "age": 42, "ward": "Cardiology", "from": "Arogya Central", "to": "Apollo Hospitals, Navi Mumbai", "date": "2026-03-11", "time": "14:30", "status": "Completed", "reason": "Specialist referral", "priority": "High"},
        ]
        save_medevac_state()

if "dispatch_msg" not in st.session_state:
    st.session_state.dispatch_msg = None

HOSPITALS = [
    {"name": "Apollo Hospitals, Andheri", "distance_km": 3.2, "base_beds": 18, "speciality": "Multi-Specialty", "eta_min": 8},
    {"name": "Apollo Hospitals, Navi Mumbai", "distance_km": 5.6, "base_beds": 11, "speciality": "Cardiology", "eta_min": 14},
    {"name": "Apollo Hospitals, Bandra", "distance_km": 7.1, "base_beds": 0, "speciality": "Oncology", "eta_min": 18},
    {"name": "Apollo Hospitals, Powai", "distance_km": 9.4, "base_beds": 25, "speciality": "Neurology", "eta_min": 22},
    {"name": "Apollo Hospitals, Worli", "distance_km": 12.3, "base_beds": 4, "speciality": "Cardiac Surgery", "eta_min": 28},
    {"name": "Apollo Hospitals, Thane", "distance_km": 8.2, "base_beds": 9, "speciality": "Multi-Specialty", "eta_min": 20},
]

PATIENTS = st.session_state.patient_roster

# ═══════════════════════════════════════════════════════════════
# 3. HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def get_live_hospitals():
    result = []
    for h in HOSPITALS:
        state = st.session_state.hospital_state.get(h["name"], {"beds": h["base_beds"], "load_pct": 70.0})
        beds, load = state["beds"], state["load_pct"]
        status = "Full" if beds == 0 else "Limited" if beds <= 5 else "Available"
        result.append({**h, "beds": beds, "load_pct": load, "status": status})
    return result

def _admit_new_patient():
    pool_idx = st.session_state.next_patient_id % len(PATIENT_NAME_POOL)
    name, ward, condition = PATIENT_NAME_POOL[pool_idx]
    priority = random.choice(PRIORITY_POOL)
    status = {"Critical": "Critical", "High": "Stable", "Medium": "Stable", "Low": "Improving"}[priority]
    st.session_state.patient_roster.append({
        "id": st.session_state.next_patient_id, "name": name, "age": random.randint(28, 78),
        "ward": ward, "condition": condition, "status": status, "priority": priority,
    })
    st.session_state.next_patient_id += 1

PRIORITY_CONFIG = {
    "Critical": {"color": t["critical"], "dim": t["critical_dim"], "border": t["critical"]},
    "High": {"color": t["warning"], "dim": t["warning_dim"], "border": t["warning"]},
    "Medium": {"color": t["info"], "dim": t["info_dim"], "border": t["info"]},
    "Low": {"color": t["success"], "dim": t["success_dim"], "border": t["success"]},
}

STATUS_COLOR = {"Available": t["success"], "Limited": t["warning"], "Full": t["critical"], "Completed": t["success"], "In Transit": t["warning"], "Pending": t["info"], "Cancelled": t["text_muted"]}

def priority_badge(priority: str) -> str:
    cfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["Medium"])
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:99px;font-size:0.72rem;font-weight:700;letter-spacing:0.06em;background:{cfg["dim"]};color:{cfg["color"]};border:1px solid {cfg["border"]};">{priority}</span>'

def status_chip(status: str) -> str:
    color = STATUS_COLOR.get(status, t["text_muted"])
    return f'<span style="display:inline-block;padding:2px 10px;border-radius:99px;font-size:0.72rem;font-weight:700;background:{t["surface"]};color:{color};border:1px solid {color};">{status}</span>'

def section_header(title: str, icon: str = ""):
    st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin:1.5rem 0 1rem;'>{icon}&nbsp; {title}</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 4. SIDEBAR APPENDICES
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("---")
    pending_ct = len([q for q in st.session_state.transfer_queue if q["status"] == "Pending"])
    transit_ct = len([q for q in st.session_state.transfer_queue if q["status"] == "In Transit"])

    st.markdown(f"""
    <div style="padding:14px 16px;background:{t['surface']};border:1px solid {t['border']};border-radius:10px;margin-bottom:0.75rem;">
        <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{t['text_muted']};margin-bottom:10px;">Active Transfers</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Pending</span><span style="font-size:0.95rem;font-weight:700;color:{t['warning']};">{pending_ct}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">In Transit</span><span style="font-size:0.95rem;font-weight:700;color:{t['info']};">{transit_ct}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Total Logged</span><span style="font-size:0.95rem;font-weight:700;color:{t['text']};">{len(st.session_state.transfer_history)}</span></div>
    </div>
    """, unsafe_allow_html=True)

    crit_patients = [p for p in st.session_state.patient_roster if p["priority"] == "Critical"]
    if crit_patients:
        st.markdown(f"""
        <div style="padding:12px 14px;background:{t['critical_dim']};border:1px solid {t['critical']};border-radius:10px;animation: critical-pulse 2.2s ease-in-out infinite;">
            <div style="font-size:0.8rem;font-weight:700;color:{t['critical']};letter-spacing:0.06em;margin-bottom:6px;">🚨 CRITICAL PATIENTS</div>
            {"".join(f'<div style="font-size:0.82rem;color:{t["text_secondary"]};margin-top:3px;">· {p["name"]} ({p["ward"]})</div>' for p in crit_patients)}
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. PAGE HEADER & DISPATCH ALERTS
# ═══════════════════════════════════════════════════════════════
render_header("MedEvac Command", "Dispatch patients to network hospitals · Monitor live bed availability", "🚑", "TRANSFER & REROUTING HUB", t["accent"])

if st.session_state.dispatch_msg:
    msg_type, msg_text = st.session_state.dispatch_msg
    color = t["success"] if msg_type == "success" else t["critical"]
    dim = t["success_dim"] if msg_type == "success" else t["critical_dim"]
    icon = "✅" if msg_type == "success" else "❌"
    st.markdown(f"<div style='padding:14px 18px;background:{dim};border:1px solid {color};border-radius:10px;margin-bottom:1rem;font-size:0.95rem;font-weight:600;color:{color};'>{icon} {msg_text}</div>", unsafe_allow_html=True)
    st.session_state.dispatch_msg = None

# ═══════════════════════════════════════════════════════════════
# 6. KPI ROW
# ═══════════════════════════════════════════════════════════════
hospitals_live = get_live_hospitals()
avail_ct = len([h for h in hospitals_live if h["status"] == "Available"])
limited_ct = len([h for h in hospitals_live if h["status"] == "Limited"])
full_ct = len([h for h in hospitals_live if h["status"] == "Full"])
total_beds = sum(h["beds"] for h in hospitals_live)

k1, k2, k3, k4 = st.columns(4)
render_kpi(k1, "Available Hospitals", str(avail_ct), f"of {len(hospitals_live)} in network", t["success"], "🏥")
render_kpi(k2, "Total Free Beds", str(total_beds), "across all facilities", t["info"], "🛏️")
render_kpi(k3, "Limited Capacity", str(limited_ct), "≤5 beds remaining", t["warning"], "⚠️")
render_kpi(k4, "At Full Capacity", str(full_ct), "transfers blocked", t["critical"], "🚨")

# ═══════════════════════════════════════════════════════════════
# 7. HOSPITAL NETWORK + DISPATCH PANEL
# ═══════════════════════════════════════════════════════════════
section_header("Network Hospital Status", "🏥")

left, right = st.columns([3, 2], gap="large")

with left:
    network_headers = "".join([f"<div style='font-size:0.78rem;font-weight:700;color:{t['text_muted']};text-transform:uppercase;letter-spacing:0.06em;'>{h}</div>" for h in ['Hospital', 'Specialty', 'Beds', 'ETA', 'Status', '']])
    st.markdown(f"<div style='display:grid;grid-template-columns:2.5fr 1fr 0.8fr 0.8fr 1fr 1.2fr;gap:8px;padding:0 4px 8px;border-bottom:1px solid {t['border']};'>{network_headers}</div>", unsafe_allow_html=True)

    for h in hospitals_live:
        status_color = STATUS_COLOR.get(h["status"], t["text"])
        bed_color = t["success"] if h["beds"] > 10 else t["warning"] if h["beds"] > 0 else t["critical"]
        disabled = h["status"] == "Full"

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2.5fr 1fr 0.8fr 0.8fr 1fr 1.2fr;gap:8px;padding:12px 4px;border-bottom:1px solid {t['border_subtle']};align-items:center;">
            <div style="font-size:0.9rem;font-weight:600;color:{t['text']};">{h['name']}</div>
            <div style="font-size:0.78rem;color:{t['text_secondary']};">{h['speciality']}</div>
            <div style="font-size:1rem;font-weight:700;color:{bed_color};">{h['beds']}</div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">{h['eta_min']}m</div>
            <div><span style="font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:99px;background:{t['surface']};color:{status_color};border:1px solid {status_color};">{h['status']}</span></div>
        </div>
        """, unsafe_allow_html=True)

        col_spacer, col_btn = st.columns([4.2, 1.8])
        with col_btn:
            if st.button("Dispatch →" if not disabled else "Full", key=f"dispatch_{h['name']}", disabled=disabled, use_container_width=True):
                st.session_state._pending_hospital = h["name"]
                st.session_state._pending_beds = h["beds"]
                st.session_state._pending_eta = h["eta_min"]

with right:
    section_header("Dispatch Order", "📋")

    patient_names = [f"{p['name']} — {p['ward']} ({p['status']})" for p in PATIENTS]
    selected_idx = st.selectbox("Select Patient", range(len(PATIENTS)), format_func=lambda i: patient_names[i], key="dispatch_patient")
    selected_patient = PATIENTS[selected_idx]

    pc = PRIORITY_CONFIG[selected_patient["priority"]]
    st.markdown(f"""
    <div style="padding:14px 16px;background:{pc['dim']};border:1px solid {pc['border']};border-radius:10px;margin:0.5rem 0 1rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><span style="font-size:1rem;font-weight:700;color:{t['text']};">{selected_patient['name']}</span>{priority_badge(selected_patient['priority'])}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
            <div style="font-size:0.82rem;color:{t['text_secondary']};">Age: <strong style="color:{t['text']};">{selected_patient['age']}</strong></div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">Ward: <strong style="color:{t['text']};">{selected_patient['ward']}</strong></div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">Condition: <strong style="color:{t['text']};">{selected_patient['condition']}</strong></div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">Status: <strong style="color:{pc['color']};">{selected_patient['status']}</strong></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    reason = st.selectbox("Transfer Reason", ["Bed shortage", "Specialist referral", "ICU overflow", "Emergency surgery", "Cardiac care", "Neurology consult", "Oncology referral", "Post-op observation", "Other"], key="transfer_reason")
    priority_override = st.selectbox("Dispatch Priority", ["Critical", "High", "Medium", "Low"], index=["Critical","High","Medium","Low"].index(selected_patient["priority"]), key="dispatch_priority")
    notes = st.text_area("Clinical Notes (optional)", height=80, key="clinical_notes", placeholder="e.g. Patient requires cardiac monitoring en route...")

    hosp_name = st.session_state.get("_pending_hospital", None)
    if hosp_name:
        st.markdown(f"""
        <div style="padding:10px 14px;background:{t['accent_dim']};border:1px solid {t['accent']};border-radius:8px;margin-bottom:0.75rem;">
            <div style="font-size:0.78rem;color:{t['accent']};font-weight:700;margin-bottom:2px;">DESTINATION SELECTED</div>
            <div style="font-size:0.9rem;font-weight:600;color:{t['text']};">{hosp_name}</div>
            <div style="font-size:0.8rem;color:{t['text_secondary']};">ETA: {st.session_state.get('_pending_eta', '?')} min · {st.session_state.get('_pending_beds', '?')} beds available</div>
        </div>
        """, unsafe_allow_html=True)

        confirm = st.button("✅ Confirm Transfer Order", use_container_width=True, key="confirm_transfer")
        cancel = st.button("Cancel", use_container_width=True, key="cancel_transfer")

        if confirm:
            new_entry = {
                "id": len(st.session_state.transfer_history) + len(st.session_state.transfer_queue) + 1,
                "patient": selected_patient["name"], "age": selected_patient["age"], "ward": selected_patient["ward"],
                "from": "Arogya Central", "to": hosp_name, "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"), "status": "In Transit", "reason": reason,
                "priority": priority_override, "notes": notes, "eta_min": st.session_state.get("_pending_eta", "?"),
            }
            st.session_state.transfer_queue.append(new_entry)
            st.session_state.transfer_history.insert(0, new_entry)

            if hosp_name in st.session_state.hospital_state:
                hs = st.session_state.hospital_state[hosp_name]
                hs["beds"] = max(0, hs["beds"] - 1)
                hs["load_pct"] = min(99.9, round(hs["load_pct"] + random.uniform(1.5, 3.5), 1))

            st.session_state.patient_roster = [p for p in st.session_state.patient_roster if p["id"] != selected_patient["id"]]
            _admit_new_patient()

            st.session_state.dispatch_msg = ("success", f"Transfer dispatched — {selected_patient['name']} → {hosp_name} (ETA: {new_entry['eta_min']} min)")
            for key in ["_pending_hospital", "_pending_beds", "_pending_eta"]: del st.session_state[key]
            
            save_medevac_state() # Trigger persistent save
            st.rerun()

        if cancel:
            for key in ["_pending_hospital", "_pending_beds", "_pending_eta"]: del st.session_state[key]
            st.rerun()
    else:
        st.markdown(f"<div style='padding:14px;background:{t['surface']};border:1px dashed {t['border']};border-radius:10px;text-align:center;color:{t['text_muted']};font-size:0.875rem;'>← Click <strong style='color:{t['text']};'>Dispatch →</strong> on a hospital row to set destination</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 8. ACTIVE TRANSFERS & CHARTS
# ═══════════════════════════════════════════════════════════════
active = [r for r in st.session_state.transfer_history if r["status"] in ("In Transit", "Pending")]

if active:
    section_header("Active Transfers", "🔴")
    for record in active:
        pc = PRIORITY_CONFIG.get(record.get("priority", "Medium"), PRIORITY_CONFIG["Medium"])
        st.markdown(f"""
        <div style="padding:16px 20px;background:{pc['dim']};border:1px solid {pc['border']};border-radius:12px;margin-bottom:0.75rem;{'animation:critical-pulse 2.2s ease-in-out infinite;' if record.get('priority')=='Critical' else ''}">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                <div style="display:flex;align-items:center;gap:10px;"><span style="font-size:1rem;font-weight:700;color:{t['text']};">{record['patient']}</span>{priority_badge(record.get('priority','Medium'))}{status_chip(record['status'])}</div>
                <span style="font-size:0.82rem;color:{t['text_secondary']};">{record['date']} {record['time']}</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;">
                <div style="font-size:0.82rem;color:{t['text_secondary']};">From: <strong style="color:{t['text']};">{record['from']}</strong></div>
                <div style="font-size:0.82rem;color:{t['text_secondary']};">To: <strong style="color:{t['text']};">{record['to']}</strong></div>
                <div style="font-size:0.82rem;color:{t['text_secondary']};">Ward: <strong style="color:{t['text']};">{record.get('ward','—')}</strong></div>
                <div style="font-size:0.82rem;color:{t['text_secondary']};">Reason: <strong style="color:{t['text']};">{record['reason']}</strong></div>
            </div>
            {f'<div style="font-size:0.82rem;color:{t["text_secondary"]};margin-top:6px;">ETA: <strong style="color:{t["info"]};">{record.get("eta_min","?")} min</strong></div>' if record.get("eta_min") else ""}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Mark Completed — {record['patient']}", key=f"complete_{record['id']}"):
            for r in st.session_state.transfer_history:
                if r["id"] == record["id"]: r["status"] = "Completed"
            st.session_state.transfer_queue = [q for q in st.session_state.transfer_queue if q["id"] != record["id"]]
            dest = record.get("to", "")
            if dest in st.session_state.hospital_state:
                st.session_state.hospital_state[dest]["load_pct"] = min(99.9, round(st.session_state.hospital_state[dest]["load_pct"] + random.uniform(0.5, 1.5), 1))
            st.session_state.dispatch_msg = ("success", f"{record['patient']} transfer completed. Destination load updated.")
            
            save_medevac_state() # Trigger persistent save
            st.rerun()

section_header("Network Capacity Snapshot", "📊")
chart_left, chart_right = st.columns(2, gap="large")

with chart_left:
    hosp_names = [h["name"].split(", ")[-1] for h in hospitals_live]
    bed_counts = [h["beds"] for h in hospitals_live]
    bar_colors = [t["success"] if b > 10 else t["warning"] if b > 0 else t["critical"] for b in bed_counts]
    
    fig_beds = go.Figure(go.Bar(x=hosp_names, y=bed_counts, marker_color=bar_colors, width=0.55, hovertemplate="<b>%{x}</b><br>Available Beds: %{y}<extra></extra>"))
    fig_beds.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t["text"]), title=dict(text="Available Beds per Hospital", font=dict(size=13, color=t["text"]), x=0), xaxis=dict(showgrid=False), yaxis=dict(gridcolor=chart_cfg["grid_color"]))
    st.plotly_chart(fig_beds, use_container_width=True, config={'displayModeBar': False})

with chart_right:
    load_vals = [h["load_pct"] for h in hospitals_live]
    load_colors = [t["critical"] if v >= 85 else t["warning"] if v >= 70 else t["success"] for v in load_vals]
    
    fig_load = go.Figure(go.Bar(x=hosp_names, y=load_vals, marker_color=load_colors, width=0.55, hovertemplate="<b>%{x}</b><br>Load: %{y}%<extra></extra>"))
    fig_load.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=t["text"]), title=dict(text="Hospital Load (%)", font=dict(size=13, color=t["text"]), x=0), xaxis=dict(showgrid=False), yaxis=dict(gridcolor=chart_cfg["grid_color"], range=[0, 100]))
    st.plotly_chart(fig_load, use_container_width=True, config={'displayModeBar': False})

# ═══════════════════════════════════════════════════════════════
# 9. TRANSFER HISTORY LOG
# ═══════════════════════════════════════════════════════════════
section_header("Transfer History Log", "📁")

f1, f2, f3 = st.columns([1, 1, 2])
filter_status = f1.selectbox("Filter by Status", ["All", "Completed", "In Transit", "Pending", "Cancelled"], key="hist_filter_status")
filter_priority = f2.selectbox("Filter by Priority", ["All", "Critical", "High", "Medium", "Low"], key="hist_filter_priority")

history = st.session_state.transfer_history
if filter_status != "All": history = [r for r in history if r["status"] == filter_status]
if filter_priority != "All": history = [r for r in history if r.get("priority","Medium") == filter_priority]

history_headers = "".join([f"<div style='font-size:0.78rem;font-weight:700;color:{t['text_muted']};text-transform:uppercase;letter-spacing:0.05em;'>{h}</div>" for h in ['Patient', 'From → To', 'Reason', 'Date', 'Priority', 'Status']])
st.markdown(f"<div style='display:grid;grid-template-columns:2fr 1.5fr 2fr 1fr 1fr 1fr;gap:8px;padding:8px 4px;border-bottom:1px solid {t['border']};margin-top:0.5rem;'>{history_headers}</div>", unsafe_allow_html=True)

if not history:
    st.markdown(f"<div style='text-align:center;padding:2rem;color:{t['text_muted']};font-size:0.9rem;'>No transfer records match the selected filters.</div>", unsafe_allow_html=True)
else:
    for record in history:
        sc = STATUS_COLOR.get(record["status"], t["text_muted"])
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1.5fr 2fr 1fr 1fr 1fr;gap:8px;padding:12px 4px;border-bottom:1px solid {t['border_subtle']};align-items:center;">
            <div><div style="font-size:0.9rem;font-weight:600;color:{t['text']};">{record['patient']}</div><div style="font-size:0.78rem;color:{t['text_secondary']};">Age {record.get('age','—')} · {record.get('ward','—')}</div></div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">{record['from'].split(',')[0]} → {record['to'].split(',')[0]}</div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">{record['reason']}</div>
            <div style="font-size:0.82rem;color:{t['text_secondary']};">{record['date']}<br>{record['time']}</div>
            <div>{priority_badge(record.get('priority','Medium'))}</div>
            <div><span style="font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:99px;background:{t['surface']};color:{sc};border:1px solid {sc};">{record['status']}</span></div>
        </div>
        """, unsafe_allow_html=True)