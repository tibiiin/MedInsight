import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import os
from components import setup_page, render_sidebar, render_header, render_kpi
from styles import get_theme, get_chart_config

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t = setup_page("Outpatient Operations", "🎫", "outpatient")
chart_cfg = get_chart_config()
render_sidebar("outpatient", "🎫")

st.markdown("""
<style>
.stButton > button, div[data-testid="stButton"] > button {
    font-weight: 700 !important;
    border-radius: 8px !important;
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
DB_FILE = "data/queue_state.json"

DOCTORS = [
    {"name": "Dr. Priya Sharma",  "dept": "Cardiology",    "room": "Room 4"},
    {"name": "Dr. Ramesh Iyer",   "dept": "General",       "room": "Room 7"},
    {"name": "Dr. Anand Verma",   "dept": "Neurology",     "room": "Room 2"},
    {"name": "Dr. Shalini Nair",  "dept": "Orthopaedics",  "room": "Room 9"},
    {"name": "Dr. Meera Pillai",  "dept": "Paediatrics",   "room": "Room 5"},
]

PATIENT_POOL = [
    "Mohan Lal Gupta", "Lakshmi Krishnan", "Ravi Shankar", "Pooja Tiwari",
    "Subramaniam Pillai", "Geeta Bhandari", "Harish Chandra Tata",
    "Anita Rao", "Rajesh Kumar", "Meena Pillai", "Arjun Patel",
    "Divya Menon", "Sanjay Iyer", "Rekha Nair", "Vijay Sharma",
    "Kavitha Nair", "Sunita Desai", "Venkatesh Reddy",
]

STATUS_ORDER = ["Completed", "Completed", "In Progress", "Now Serving", "Waiting", "Waiting", "Waiting"]

def _init_queue():
    now = datetime.now()
    entries = []
    for i in range(7):
        doc = random.choice(DOCTORS)
        arrived = now - timedelta(minutes=random.randint(5, 90))
        entries.append({
            "token": 101 + i, "patient": PATIENT_POOL[i], "doctor": doc["name"],
            "dept": doc["dept"], "room": doc["room"], "status": STATUS_ORDER[i],
            "arrived": arrived.strftime("%I:%M %p"), "wait_mins": max(0, (now - arrived).seconds // 60),
        })
    return entries

def load_queue_state():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return None

def save_queue_state():
    state_to_save = {
        "queue": st.session_state.queue,
        "next_token": st.session_state.next_token,
        "token_history": st.session_state.token_history
    }
    os.makedirs("data", exist_ok=True)
    with open(DB_FILE, "w") as f: json.dump(state_to_save, f)

saved_state = load_queue_state()

if "queue" not in st.session_state:
    if saved_state:
        st.session_state.queue = saved_state["queue"]
        st.session_state.next_token = saved_state["next_token"]
        st.session_state.token_history = saved_state["token_history"]
    else:
        st.session_state.queue = _init_queue()
        st.session_state.next_token = 108
        st.session_state.token_history = [q for q in st.session_state.queue if q["status"] == "Completed"]
        save_queue_state()

if "queue_msg" not in st.session_state:
    st.session_state.queue_msg = None

# ═══════════════════════════════════════════════════════════════
# 3. QUEUE ACTIONS
# ═══════════════════════════════════════════════════════════════
def get_now_serving(): return next((q for q in st.session_state.queue if q["status"] == "Now Serving"), None)
def get_next_waiting(): return next((q for q in st.session_state.queue if q["status"] == "Waiting"), None)

def call_next():
    ns, nw = get_now_serving(), get_next_waiting()
    if ns:
        ns["status"] = "Completed"
        st.session_state.token_history.append(ns)
    if nw:
        nw["status"] = "Now Serving"
        st.session_state.queue_msg = ("success", f"Token #{nw['token']} — {nw['patient']} called to {nw['room']}")
    else:
        st.session_state.queue_msg = ("info", "No patients waiting in queue.")
    save_queue_state()

def skip_current():
    ns = get_now_serving()
    if ns:
        ns["status"] = "Waiting"
        st.session_state.queue.remove(ns)
        st.session_state.queue.append(ns)
        nw = get_next_waiting()
        if nw:
            nw["status"] = "Now Serving"
            st.session_state.queue_msg = ("info", f"#{ns['token']} skipped. Token #{nw['token']} now serving.")
        else:
            ns["status"] = "Now Serving"
            st.session_state.queue_msg = ("info", "Only one patient — moved back to serving.")
    save_queue_state()

def complete_current():
    ns = get_now_serving()
    if ns:
        ns["status"] = "Completed"
        st.session_state.token_history.append(ns)
        nw = get_next_waiting()
        if nw: nw["status"] = "Now Serving"
        st.session_state.queue_msg = ("success", f"Token #{ns['token']} consultation completed.")
    save_queue_state()

def add_patient(name: str, doctor_name: str):
    doc = next((d for d in DOCTORS if d["name"] == doctor_name), DOCTORS[0])
    st.session_state.queue.append({
        "token": st.session_state.next_token, "patient": name, "doctor": doc["name"],
        "dept": doc["dept"], "room": doc["room"], "status": "Waiting",
        "arrived": datetime.now().strftime("%I:%M %p"), "wait_mins": 0,
    })
    st.session_state.queue_msg = ("success", f"Token #{st.session_state.next_token} issued to {name} — {doc['name']}")
    st.session_state.next_token += 1
    save_queue_state()

def reset_queue():
    st.session_state.queue = _init_queue()
    st.session_state.next_token = 108
    st.session_state.token_history = []
    st.session_state.queue_msg = ("info", "Queue reset to initial state.")
    save_queue_state()

# ═══════════════════════════════════════════════════════════════
# 4. COMPUTED METRICS & HELPERS
# ═══════════════════════════════════════════════════════════════
STATUS_COLORS = {"Now Serving": t["accent"], "Waiting": t["info"], "In Progress": t["warning"], "Completed": t["success"]}

queue = st.session_state.queue
waiting_ct = len([q for q in queue if q["status"] == "Waiting"])
serving_ct = len([q for q in queue if q["status"] == "Now Serving"])
completed_ct = len([q for q in queue if q["status"] == "Completed"])
in_prog_ct = len([q for q in queue if q["status"] == "In Progress"])
waiting_times = [q["wait_mins"] for q in queue if q["status"] == "Waiting" and q["wait_mins"] > 0]
avg_wait = round(sum(waiting_times) / len(waiting_times)) if waiting_times else 0
now_serving = get_now_serving()

def section_hdr(title, icon=""):
    st.markdown(f"<div style='font-size:0.82rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{t['text']};border-bottom:1px solid {t['border']};padding-bottom:0.5rem;margin:1.5rem 0 1rem;'>{icon}&nbsp; {title}</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("---")
    st.markdown(f"""
    <div style="padding:14px 16px;background:{t['surface']};border:1px solid {t['border']};border-radius:10px;margin-bottom:1rem;">
        <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:{t['text_muted']};margin-bottom:10px;">Live Snapshot</div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Waiting</span><span style="font-size:0.95rem;font-weight:700;color:{t['info']};">{waiting_ct}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Now Serving</span><span style="font-size:0.95rem;font-weight:700;color:{t['accent']};">{serving_ct}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Completed</span><span style="font-size:0.95rem;font-weight:700;color:{t['success']};">{completed_ct}</span></div>
        <div style="display:flex;justify-content:space-between;"><span style="font-size:0.875rem;color:{t['text_secondary']};">Avg Wait</span><span style="font-size:0.95rem;font-weight:700;color:{t['warning']};">{avg_wait} min</span></div>
    </div>
    """, unsafe_allow_html=True)

    nw = get_next_waiting()
    if nw:
        st.markdown(f"""
        <div style="padding:12px 14px;background:{t['info_dim']};border:1px solid {t['info']};border-radius:10px;">
            <div style="font-size:0.75rem;font-weight:700;color:{t['info']};letter-spacing:0.06em;margin-bottom:4px;">NEXT UP</div>
            <div style="font-size:1rem;font-weight:700;color:{t['text']};">#{nw['token']} — {nw['patient']}</div>
            <div style="font-size:0.8rem;color:{t['text_secondary']};margin-top:2px;">{nw['doctor']} · {nw['room']}</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 6. HEADER & ACTION MESSAGES
# ═══════════════════════════════════════════════════════════════
render_header("Outpatient Operations", f"Live token tracking · {datetime.now().strftime('%d %b %Y, %I:%M %p')}", "🎫", f"{waiting_ct} WAITING", t["accent"])

if st.session_state.queue_msg:
    msg_type, msg_text = st.session_state.queue_msg
    color = t["success"] if msg_type == "success" else t["info"] if msg_type == "info" else t["warning"]
    dim = t["success_dim"] if msg_type == "success" else t["info_dim"] if msg_type == "info" else t["warning_dim"]
    icon = "✅" if msg_type == "success" else "ℹ️"
    st.markdown(f"<div style='padding:12px 18px;background:{dim};border:1px solid {color};border-radius:10px;margin-bottom:1rem;font-size:0.9rem;font-weight:600;color:{color};'>{icon} {msg_text}</div>", unsafe_allow_html=True)
    st.session_state.queue_msg = None

# ═══════════════════════════════════════════════════════════════
# 7. NOW SERVING HERO
# ═══════════════════════════════════════════════════════════════
if now_serving:
    st.markdown(f"""
    <div style="padding:28px 32px;background:linear-gradient(135deg,{t['accent_dim']},{t['info_dim']});border:2px solid {t['accent']};border-radius:16px;margin-bottom:1.5rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
        <div>
            <div style="font-size:0.75rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{t['accent']};margin-bottom:8px;">🔊 Now Serving</div>
            <div style="font-size:3.5rem;font-weight:900;color:{t['accent']};font-family:'JetBrains Mono',monospace;line-height:1;">#{now_serving['token']}</div>
            <div style="font-size:1.1rem;font-weight:700;color:{t['text']};margin-top:8px;">{now_serving['patient']}</div>
            <div style="font-size:0.875rem;color:{t['text_secondary']};margin-top:4px;">{now_serving['doctor']} · {now_serving['room']} · {now_serving['dept']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("⏭️ Call Next Patient", use_container_width=True, key="call_next"): call_next(); st.rerun()
    if b2.button("✅ Complete & Call Next", use_container_width=True, key="complete_next"): complete_current(); st.rerun()
    if b3.button("⏩ Skip Current Token", use_container_width=True, key="skip_curr"): skip_current(); st.rerun()
    if b4.button("🔄 Reset Queue", use_container_width=True, key="reset_q"): reset_queue(); st.rerun()
else:
    st.markdown(f"<div style='padding:24px 28px;background:{t['surface']};border:1px dashed {t['border']};border-radius:16px;text-align:center;margin-bottom:1.5rem;'><div style='font-size:2rem;margin-bottom:8px;'>⏸️</div><div style='font-size:1rem;font-weight:600;color:{t['text_secondary']};'>No patient currently being served</div></div>", unsafe_allow_html=True)
    b1, _, _, b4 = st.columns(4)
    if b1.button("▶️ Start Queue", use_container_width=True, key="start_q"):
        nw = get_next_waiting()
        if nw: nw["status"] = "Now Serving"; save_queue_state(); st.rerun()
    if b4.button("🔄 Reset Queue", use_container_width=True, key="reset_q2"): reset_queue(); st.rerun()

# ═══════════════════════════════════════════════════════════════
# 8. KPIs
# ═══════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)
render_kpi(k1, "Waiting", str(waiting_ct), "in queue", t["info"])
render_kpi(k2, "Now Serving", str(serving_ct), "active consultations", t["accent"])
render_kpi(k3, "In Progress", str(in_prog_ct), "being processed", t["warning"])
render_kpi(k4, "Completed", str(completed_ct), "today", t["success"])
render_kpi(k5, "Avg Wait Time", f"{avg_wait} min", "estimated per patient", t["warning"] if avg_wait > 20 else t["success"])

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 9. ADD PATIENT
# ═══════════════════════════════════════════════════════════════
section_hdr("Issue New Token", "➕")
with st.expander("Add Patient to Queue", expanded=False):
    a1, a2, a3 = st.columns([2, 2, 1])
    new_name = a1.text_input("Patient Name", placeholder="Enter full name", key="new_patient_name")
    new_doc = a2.selectbox("Assign Doctor", [d["name"] for d in DOCTORS], key="new_patient_doc")
    a3.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
    if a3.button("Issue Token", use_container_width=True, key="issue_token"):
        if new_name.strip(): add_patient(new_name.strip(), new_doc); st.rerun()
        else: st.error("Enter patient name.")

# ═══════════════════════════════════════════════════════════════
# 10. LIVE QUEUE TABLE
# ═══════════════════════════════════════════════════════════════
section_hdr("Live Queue", "📋")
qf1, qf2 = st.columns([1, 3])
filter_status = qf1.selectbox("Filter", ["All", "Waiting", "Now Serving", "In Progress", "Completed"], key="queue_filter")

display_queue = queue if filter_status == "All" else [q for q in queue if q["status"] == filter_status]

# Extracted list comprehension to prevent f-string backslash errors
table_headers = "".join([f"<div style='font-size:0.78rem;font-weight:700;color:{t['text_muted']};text-transform:uppercase;letter-spacing:0.05em;'>{h}</div>" for h in ["Token", "Patient", "Doctor", "Dept", "Room", "Arrived", "Status"]])
st.markdown(f"<div style='display:grid;grid-template-columns:0.6fr 1.8fr 1.8fr 1fr 1fr 1fr 1fr;gap:8px;padding:8px 4px;border-bottom:1px solid {t['border']};'>{table_headers}</div>", unsafe_allow_html=True)

for q in display_queue:
    sc = STATUS_COLORS.get(q["status"], t["text_muted"])
    is_ns = q["status"] == "Now Serving"
    row_bg = f"background:{t['accent_dim']};" if is_ns else ""
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:0.6fr 1.8fr 1.8fr 1fr 1fr 1fr 1fr;gap:8px;padding:12px 4px;{row_bg}border-bottom:1px solid {t['border_subtle']};border-radius:{'8px' if is_ns else '0'};align-items:center;">
        <div style="font-size:1rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:{t['accent'] if is_ns else t['text']};">#{q['token']}</div>
        <div style="font-size:0.9rem;font-weight:{'700' if is_ns else '500'};color:{t['text']};">{q['patient']}</div>
        <div style="font-size:0.82rem;color:{t['text_secondary']};">{q['doctor']}</div>
        <div style="font-size:0.78rem;color:{t['text_muted']};">{q['dept']}</div>
        <div style="font-size:0.82rem;color:{t['text']};">{q['room']}</div>
        <div style="font-size:0.82rem;color:{t['text_secondary']};">{q['arrived']}</div>
        <div><span style="font-size:0.75rem;font-weight:700;padding:3px 10px;border-radius:99px;background:{t['surface']};color:{sc};border:1px solid {sc};">{q['status']}</span></div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 11. PER-DOCTOR QUEUE BREAKDOWN
# ═══════════════════════════════════════════════════════════════
section_hdr("Per-Doctor Queue", "👨‍⚕️")

doc_names = [d["name"] for d in DOCTORS]
doc_waiting = [len([q for q in queue if q["doctor"] == d and q["status"] == "Waiting"]) for d in doc_names]
doc_done = [len([q for q in queue if q["doctor"] == d and q["status"] == "Completed"]) for d in doc_names]
doc_labels = [d.split("Dr. ")[1] for d in doc_names]

fig_doc = go.Figure()
fig_doc.add_trace(go.Bar(name="Waiting", x=doc_labels, y=doc_waiting, marker_color=t["info"], marker_line=dict(width=0)))
fig_doc.add_trace(go.Bar(name="Completed", x=doc_labels, y=doc_done, marker_color=t["success"], marker_line=dict(width=0)))
fig_doc.update_layout(
    margin=dict(l=0, r=0, t=30, b=0), height=260,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=t["text"]), barmode="group",
    xaxis=dict(showgrid=False), yaxis=dict(gridcolor=chart_cfg["grid_color"]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_doc, use_container_width=True, config={'displayModeBar': False})

doc_cols = st.columns(len(DOCTORS))
for i, (doc, col) in enumerate(zip(DOCTORS, doc_cols)):
    w, d = doc_waiting[i], doc_done[i]
    ns_here = now_serving and now_serving["doctor"] == doc["name"]
    border_color = t["accent"] if ns_here else t["border"]
    col.markdown(f"""
    <div style="padding:12px 14px;background:{t['card']};border:1px solid {border_color};border-radius:10px;text-align:center;">
        <div style="font-size:0.7rem;font-weight:700;color:{t['text_muted']};text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{doc['name'].replace('Dr. ','')}</div>
        <div style="font-size:0.75rem;color:{t['text_secondary']};margin-bottom:8px;">{doc['room']}</div>
        <div style="display:flex;justify-content:space-around;">
            <div style="text-align:center;"><div style="font-size:1.2rem;font-weight:700;color:{t['info']};">{w}</div><div style="font-size:0.65rem;color:{t['text_muted']};">Waiting</div></div>
            <div style="text-align:center;"><div style="font-size:1.2rem;font-weight:700;color:{t['success']};">{d}</div><div style="font-size:0.65rem;color:{t['text_muted']};">Done</div></div>
        </div>
        {f'<div style="font-size:0.65rem;margin-top:6px;color:{t["accent"]};font-weight:700;">● ACTIVE</div>' if ns_here else ''}
    </div>
    """, unsafe_allow_html=True)