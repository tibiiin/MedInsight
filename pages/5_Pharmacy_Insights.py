import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from styles import get_chart_config
from components import setup_page, render_sidebar, render_header

# ═══════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SETUP
# ═══════════════════════════════════════════════════════════════
t         = setup_page("Pharmacy & Inventory", "💊", "pharmacy")
chart_cfg = get_chart_config()
render_sidebar("pharmacy", "💊")

# Pharmacy-specific CSS only (tabs, dataframe, download button)
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    padding: 8px 20px !important;
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}
[data-testid="stDataFrame"] { border-radius: 10px !important; }
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)

# Category colour map — consistent across all charts
CAT_COLORS = {
    "Analgesic":   t["info"],
    "Antibiotic":  t["success"],
    "Antiviral":   t["warning"],
    "Cardiology":  t["critical"],
    "Dermatology": "#a78bfa",
}

# ═══════════════════════════════════════════════════════════════
# 2. DATA LOAD
# ═══════════════════════════════════════════════════════════════
CSV_PATH = "medical_inventory.csv"

@st.cache_data(ttl=300)
def load_inventory(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["expiry_date"]    = pd.to_datetime(df["expiry_date"], dayfirst=True, errors="coerce")
    df["days_to_expiry"] = (df["expiry_date"] - datetime.now()).dt.days.astype("Int64")
    return df

try:
    df = load_inventory(CSV_PATH)
except FileNotFoundError:
    st.error(f"CSV file `{CSV_PATH}` not found. Place it in the same folder as this page.")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# 3. SIDEBAR FILTERS & THRESHOLDS
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;
                text-transform:uppercase;color:{t['text']};
                border-bottom:1px solid {t['border']};
                padding-bottom:0.4rem;margin-bottom:0.75rem;">
        Filters
    </div>
    """, unsafe_allow_html=True)

    categories   = ["All"] + sorted(df["category"].unique().tolist())
    sel_category = st.selectbox("Category", categories, key="filter_cat")

    storage_opts = ["All"] + sorted(df["storage_condition"].unique().tolist())
    sel_storage  = st.selectbox("Storage Condition", storage_opts, key="filter_storage")

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:0.8rem;font-weight:700;letter-spacing:0.1em;
                text-transform:uppercase;color:{t['text']};
                border-bottom:1px solid {t['border']};
                padding-bottom:0.4rem;margin-bottom:0.75rem;">
        Alert Thresholds
    </div>
    """, unsafe_allow_html=True)

    low_stock_limit  = st.slider("Low Stock — below (units)", 10, 300, 100, key="low_stock_slider")
    expiry_warn_days = st.slider("Expiry Warning (days)",     30, 180,  90, key="expiry_slider")

# ═══════════════════════════════════════════════════════════════
# 4. APPLY FILTERS
# ═══════════════════════════════════════════════════════════════
fdf = df.copy()
if sel_category != "All":
    fdf = fdf[fdf["category"] == sel_category]
if sel_storage != "All":
    fdf = fdf[fdf["storage_condition"] == sel_storage]

# ═══════════════════════════════════════════════════════════════
# 5. COMPUTE KPIs
# ═══════════════════════════════════════════════════════════════
total_meds    = len(fdf)
out_of_stock  = int((fdf["stock_quantity"] == 0).sum())
low_stock_cnt = int((fdf["stock_quantity"].between(1, low_stock_limit - 1)).sum())
expiring_soon = int(fdf["days_to_expiry"].between(0, expiry_warn_days).sum())
expired_cnt   = int((fdf["days_to_expiry"] < 0).sum())
total_value   = (fdf["price"] * fdf["stock_quantity"]).sum()
avg_stock     = fdf["stock_quantity"].mean()

# ═══════════════════════════════════════════════════════════════
# 6. PAGE HEADER
# ═══════════════════════════════════════════════════════════════
render_header(
    title="Pharmacy & Inventory",
    subtitle=f"Stock & Expiry Management · {sel_category if sel_category != 'All' else 'All Categories'} · Threshold: {low_stock_limit} units",
    icon="💊",
    right_badge=f"{len(fdf):,} RECORDS",
    right_color=t["accent"],
)

# Critical alert banner
if out_of_stock > 0 or expired_cnt > 0:
    alerts = []
    if out_of_stock > 0: alerts.append(f"🚨 {out_of_stock} medicines OUT OF STOCK")
    if expired_cnt  > 0: alerts.append(f"☠️ {expired_cnt} medicines EXPIRED")
    st.markdown(f"""
    <div class="critical-card" style="margin-bottom:1.25rem;">
        <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            {"".join(f'<span style="font-size:0.9rem;font-weight:700;color:{t["critical"]};">{a}</span>' for a in alerts)}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 7. KPI ROWS
# ═══════════════════════════════════════════════════════════════

# Row 1 — 5 count KPIs
k1, k2, k3, k4, k5 = st.columns(5)
for col, label, value, sub, color in [
    (k1, "Total Medicines", f"{total_meds:,}",  "in filtered view",                t["text"]),
    (k2, "Out of Stock",    str(out_of_stock),   "need reorder now",                t["critical"] if out_of_stock else t["success"]),
    (k3, "Low Stock",       str(low_stock_cnt),  f"below {low_stock_limit} units",  t["warning"]  if low_stock_cnt else t["success"]),
    (k4, "Expiring Soon",   str(expiring_soon),  f"within {expiry_warn_days} days", t["warning"]  if expiring_soon else t["success"]),
    (k5, "Expired",         str(expired_cnt),    "must be disposed",                t["critical"] if expired_cnt else t["success"]),
]:
    col.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}!important;font-size:2rem!important;">{value}</div>
        <div style="font-size:0.8rem;color:{t['text_secondary']};margin-top:4px;">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

# Row 2 — Inventory value (full-width, unique layout kept as-is)
st.markdown(f"""
<div class="kpi-box" style="display:flex;align-items:center;
            justify-content:space-between;padding:1.1rem 1.75rem;">
    <div>
        <div class="kpi-label">💰 Total Inventory Value</div>
        <div style="font-size:2.4rem;font-weight:700;letter-spacing:-0.03em;
                    color:{t['info']};line-height:1;margin-top:4px;">
            ₹{total_value:,.0f}
        </div>
    </div>
    <div style="display:flex;gap:2.5rem;">
        <div style="text-align:center;">
            <div style="font-size:0.78rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.07em;color:{t['text_muted']};">Avg Price / Med</div>
            <div style="font-size:1.35rem;font-weight:700;color:{t['text']};margin-top:2px;">
                ₹{fdf['price'].mean():,.2f}
            </div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:0.78rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.07em;color:{t['text_muted']};">Avg Stock / Med</div>
            <div style="font-size:1.35rem;font-weight:700;color:{t['text']};margin-top:2px;">
                {avg_stock:,.0f} units
            </div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:0.78rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.07em;color:{t['text_muted']};">Total Stock Units</div>
            <div style="font-size:1.35rem;font-weight:700;color:{t['text']};margin-top:2px;">
                {fdf['stock_quantity'].sum():,}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 8. TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📦  Stock Monitor",
    "⏰  Expiry Alerts",
    "📊  Category Analysis",
    "🗂️  Full Inventory",
])

def section_hdr(title: str):
    st.markdown(f"""
    <div style="font-size:0.82rem;font-weight:700;letter-spacing:0.08em;
                text-transform:uppercase;color:{t['text']};
                border-bottom:1px solid {t['border']};
                padding-bottom:0.5rem;margin:1.25rem 0 1rem;">
        {title}
    </div>
    """, unsafe_allow_html=True)

def empty_state(message: str):
    """Reusable green success card for empty table states."""
    st.markdown(f"""
    <div class="success-card" style="text-align:center;padding:1.5rem;">
        <div style="font-size:1.5rem;margin-bottom:6px;">✅</div>
        <div style="font-size:0.9rem;font-weight:600;color:{t['success']};">{message}</div>
    </div>
    """, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────
# TAB 1 — STOCK MONITOR
# ───────────────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2, gap="large")

    with c1:
        stock_cat = (fdf.groupby("category")["stock_quantity"]
                        .sum().reset_index()
                        .sort_values("stock_quantity"))
        stock_cat.columns = ["Category", "Total Stock"]
        bar_colors = [CAT_COLORS.get(c, t["info"]) for c in stock_cat["Category"]]
        annotations = [
            dict(x=v, y=cat, text=f"<b>{v:,}</b>", showarrow=False,
                 xanchor="left", xshift=6,
                 font=dict(size=12, color=bar_colors[i], family="Inter, sans-serif"))
            for i, (cat, v) in enumerate(zip(stock_cat["Category"], stock_cat["Total Stock"]))
        ]
        fig_stock = go.Figure(go.Bar(
            x=stock_cat["Total Stock"], y=stock_cat["Category"],
            orientation="h", marker_color=bar_colors, marker_line=dict(width=0),
            hovertemplate="<b>%{y}</b><br>Stock: %{x:,}<extra></extra>",
        ))
        fig_stock.update_layout(
            **chart_cfg["common_layout"], template=chart_cfg["template"],
            height=300, annotations=annotations,
            title=dict(text="Total Stock Units by Category", font=dict(size=13, color=t["text"]), x=0),
            xaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"])),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=t["text"], size=12)),
            margin=dict(l=10, r=80, t=40, b=10), showlegend=False,
        )
        st.plotly_chart(fig_stock, use_container_width=True)

    with c2:
        storage_grp = fdf.groupby("storage_condition")["stock_quantity"].sum().reset_index()
        storage_grp.columns = ["Storage", "Stock"]
        fig_pie = go.Figure(go.Pie(
            labels=storage_grp["Storage"], values=storage_grp["Stock"], hole=0.5,
            marker=dict(colors=[t["info"], t["success"], t["warning"]], line=dict(color=t["bg"], width=2)),
            textfont=dict(color=t["text"], size=12),
            hovertemplate="<b>%{label}</b><br>Stock: %{value:,}<br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            **chart_cfg["common_layout"], height=300,
            title=dict(text="Stock by Storage Condition", font=dict(size=13, color=t["text"]), x=0),
            legend=dict(font=dict(color=t["text"], size=11)),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    a1, a2 = st.columns(2, gap="large")

    with a1:
        section_hdr("🔴 Out of Stock")
        oos = fdf[fdf["stock_quantity"] == 0][
            ["medicine_name", "category", "batch_number", "manufacturer"]
        ]
        if oos.empty:
            empty_state("No medicines out of stock")
        else:
            st.dataframe(oos.rename(columns={
                "medicine_name": "Medicine", "category": "Category",
                "batch_number":  "Batch #",  "manufacturer": "Manufacturer",
            }), use_container_width=True, hide_index=True)

    with a2:
        section_hdr(f"🟠 Low Stock (below {low_stock_limit} units)")
        low = (fdf[fdf["stock_quantity"].between(1, low_stock_limit - 1)]
               [["medicine_name", "category", "stock_quantity", "price"]]
               .sort_values("stock_quantity"))
        if low.empty:
            empty_state("All medicines above threshold")
        else:
            st.dataframe(low.rename(columns={
                "medicine_name": "Medicine", "category": "Category",
                "stock_quantity": "Stock Units", "price": "Price (₹)",
            }), use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────
# TAB 2 — EXPIRY ALERTS
# ───────────────────────────────────────────────────────────────
with tab2:
    e1, e2 = st.columns(2, gap="large")

    with e1:
        section_hdr(f"🟡 Expiring Within {expiry_warn_days} Days")
        exp_soon = (fdf[fdf["days_to_expiry"].between(0, expiry_warn_days)]
                    [["medicine_name", "category", "stock_quantity",
                      "expiry_date", "days_to_expiry", "batch_number"]]
                    .sort_values("days_to_expiry"))
        if exp_soon.empty:
            empty_state(f"Nothing expiring in {expiry_warn_days} days")
        else:
            exp_soon = exp_soon.copy()
            exp_soon["expiry_date"] = exp_soon["expiry_date"].dt.strftime("%d %b %Y")
            st.dataframe(exp_soon.rename(columns={
                "medicine_name":  "Medicine",  "category":       "Category",
                "stock_quantity": "Stock",      "expiry_date":    "Expiry Date",
                "days_to_expiry": "Days Left",  "batch_number":   "Batch #",
            }), use_container_width=True, hide_index=True, height=360)
            st.download_button(
                "⬇️ Download Expiry Alert List",
                exp_soon.to_csv(index=False).encode("utf-8"),
                "expiry_alerts.csv", "text/csv",
            )

    with e2:
        section_hdr("🔴 Already Expired")
        expired = (fdf[fdf["days_to_expiry"] < 0]
                   [["medicine_name", "category", "stock_quantity",
                     "expiry_date", "days_to_expiry", "batch_number"]]
                   .sort_values("days_to_expiry"))
        if expired.empty:
            empty_state("No expired medicines")
        else:
            expired = expired.copy()
            expired["days_to_expiry"] = expired["days_to_expiry"].abs()
            expired["expiry_date"]    = expired["expiry_date"].dt.strftime("%d %b %Y")
            st.dataframe(expired.rename(columns={
                "medicine_name":  "Medicine",  "category":       "Category",
                "stock_quantity": "Stock",      "expiry_date":    "Expired On",
                "days_to_expiry": "Days Ago",   "batch_number":   "Batch #",
            }), use_container_width=True, hide_index=True, height=360)

    section_hdr("📅 Expiry Timeline Overview")

    BUCKET_ORDER  = ["Expired", "< 30 days", "30–90 days", "90–180 days", "Safe (>180d)"]
    BUCKET_COLORS = {
        "Expired":      t["critical"],
        "< 30 days":    t["warning"],
        "30–90 days":   "#ecc94b",
        "90–180 days":  t["info"],
        "Safe (>180d)": t["success"],
    }

    def expiry_bucket(d):
        if pd.isna(d): return "Unknown"
        if d < 0:      return "Expired"
        elif d <= 30:  return "< 30 days"
        elif d <= 90:  return "30–90 days"
        elif d <= 180: return "90–180 days"
        else:          return "Safe (>180d)"

    fdf2 = fdf.copy()
    fdf2["bucket"] = fdf2["days_to_expiry"].apply(expiry_bucket)
    bucket_ct = fdf2["bucket"].value_counts().reset_index()
    bucket_ct.columns = ["Status", "Count"]
    bucket_ct["Status"] = pd.Categorical(bucket_ct["Status"], categories=BUCKET_ORDER, ordered=True)
    bucket_ct = bucket_ct.sort_values("Status")
    b_colors  = [BUCKET_COLORS.get(s, t["info"]) for s in bucket_ct["Status"]]

    annots = [
        dict(x=s, y=v, text=f"<b>{v}</b>", showarrow=False,
             yanchor="bottom", yshift=5,
             font=dict(size=12, color=b_colors[i], family="Inter, sans-serif"))
        for i, (s, v) in enumerate(zip(bucket_ct["Status"], bucket_ct["Count"]))
    ]
    fig_bucket = go.Figure(go.Bar(
        x=bucket_ct["Status"], y=bucket_ct["Count"],
        marker_color=b_colors, marker_line=dict(width=0), width=0.55,
        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
    ))
    fig_bucket.update_layout(
        **chart_cfg["common_layout"], template=chart_cfg["template"],
        height=280, annotations=annots,
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=t["text"], size=12)),
        yaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"])),
        margin=dict(l=10, r=10, t=20, b=10), showlegend=False,
    )
    st.plotly_chart(fig_bucket, use_container_width=True)

# ───────────────────────────────────────────────────────────────
# TAB 3 — CATEGORY ANALYSIS
# ───────────────────────────────────────────────────────────────
with tab3:
    ca1, ca2 = st.columns(2, gap="large")

    with ca1:
        cat_count = fdf["category"].value_counts().reset_index()
        cat_count.columns = ["Category", "Count"]
        pie_colors = [CAT_COLORS.get(c, t["info"]) for c in cat_count["Category"]]
        fig_donut = go.Figure(go.Pie(
            labels=cat_count["Category"], values=cat_count["Count"], hole=0.5,
            marker=dict(colors=pie_colors, line=dict(color=t["bg"], width=2)),
            textfont=dict(color=t["text"], size=11),
            hovertemplate="<b>%{label}</b><br>%{value:,} medicines<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            **chart_cfg["common_layout"], height=300,
            title=dict(text="Medicines per Category", font=dict(size=13, color=t["text"]), x=0),
            legend=dict(font=dict(color=t["text"], size=11)),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with ca2:
        avg_price = (fdf.groupby("category")["price"]
                        .mean().round(2).reset_index()
                        .sort_values("price"))
        avg_price.columns = ["Category", "Avg Price"]
        ap_colors = [CAT_COLORS.get(c, t["info"]) for c in avg_price["Category"]]
        fig_avg = go.Figure(go.Bar(
            x=avg_price["Avg Price"], y=avg_price["Category"],
            orientation="h", marker_color=ap_colors, marker_line=dict(width=0),
            hovertemplate="<b>%{y}</b><br>Avg Price: ₹%{x:.2f}<extra></extra>",
        ))
        fig_avg.update_layout(
            **chart_cfg["common_layout"], template=chart_cfg["template"],
            height=300,
            title=dict(text="Average Price by Category (₹)", font=dict(size=13, color=t["text"]), x=0),
            xaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"]), tickprefix="₹"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=t["text"], size=12)),
            margin=dict(l=10, r=10, t=40, b=10), showlegend=False,
        )
        st.plotly_chart(fig_avg, use_container_width=True)

    section_hdr("📋 Category Summary")

    cat_summary = fdf.groupby("category").agg(
        Total_Medicines = ("medicine_name",  "count"),
        Total_Stock     = ("stock_quantity", "sum"),
        Avg_Price       = ("price",          "mean"),
        Low_Stock_Items = ("stock_quantity", lambda x: (x < low_stock_limit).sum()),
        Expiring_Soon   = ("days_to_expiry", lambda x: x.between(0, expiry_warn_days).sum()),
        Expired         = ("days_to_expiry", lambda x: (x < 0).sum()),
    ).reset_index()
    cat_summary["Avg_Price"] = cat_summary["Avg_Price"].round(2).apply(lambda x: f"₹{x:.2f}")

    st.dataframe(cat_summary.rename(columns={
        "category":        "Category",
        "Total_Medicines": "Total Medicines",
        "Total_Stock":     "Total Stock",
        "Avg_Price":       "Avg Price",
        "Low_Stock_Items": "⚠️ Low Stock",
        "Expiring_Soon":   "⏰ Expiring Soon",
        "Expired":         "☠️ Expired",
    }), use_container_width=True, hide_index=True)

    section_hdr("💰 Inventory Value by Category")

    val_cat = fdf.copy()
    val_cat["value"] = val_cat["price"] * val_cat["stock_quantity"]
    val_grp = val_cat.groupby("category")["value"].sum().reset_index().sort_values("value")
    val_grp.columns = ["Category", "Value"]
    vc_colors = [CAT_COLORS.get(c, t["info"]) for c in val_grp["Category"]]
    fig_val = go.Figure(go.Bar(
        x=val_grp["Value"], y=val_grp["Category"],
        orientation="h", marker_color=vc_colors, marker_line=dict(width=0),
        hovertemplate="<b>%{y}</b><br>Value: ₹%{x:,.0f}<extra></extra>",
    ))
    fig_val.update_layout(
        **chart_cfg["common_layout"], template=chart_cfg["template"],
        height=260,
        xaxis=dict(gridcolor=chart_cfg["grid_color"], tickfont=dict(color=chart_cfg["tick_color"]), tickprefix="₹"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=t["text"], size=12)),
        margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
    )
    st.plotly_chart(fig_val, use_container_width=True)

# ───────────────────────────────────────────────────────────────
# TAB 4 — FULL INVENTORY TABLE
# ───────────────────────────────────────────────────────────────
with tab4:
    section_hdr("🔍 Search & Export")

    s1, s2, s3 = st.columns([2, 1, 1])
    with s1:
        search = st.text_input(
            "Search medicine name, batch number or manufacturer",
            placeholder="e.g. Dolopril, BN-23547, Pharma...",
            key="search_input", label_visibility="collapsed",
        )
    with s2:
        sort_col = st.selectbox(
            "Sort by", ["medicine_name", "stock_quantity", "price", "days_to_expiry"],
            format_func=lambda x: {
                "medicine_name":  "Name",
                "stock_quantity": "Stock",
                "price":          "Price",
                "days_to_expiry": "Days to Expiry",
            }[x],
            key="sort_col",
        )
    with s3:
        sort_asc = st.selectbox("Order", ["Ascending", "Descending"], key="sort_order")

    table = fdf.copy()
    if search:
        mask = (
            table["medicine_name"].str.contains(search, case=False, na=False) |
            table["batch_number"].str.contains(search, case=False, na=False)  |
            table["manufacturer"].str.contains(search, case=False, na=False)
        )
        table = table[mask]

    table = table.sort_values(sort_col, ascending=(sort_asc == "Ascending"))
    table_display = table.copy()
    table_display["expiry_date"] = table_display["expiry_date"].dt.strftime("%d %b %Y")

    st.dataframe(
        table_display[[
            "medicine_id", "medicine_name", "category", "price",
            "stock_quantity", "expiry_date", "days_to_expiry",
            "batch_number", "manufacturer", "storage_condition",
        ]].rename(columns={
            "medicine_id":       "ID",
            "medicine_name":     "Medicine",
            "category":          "Category",
            "price":             "Price (₹)",
            "stock_quantity":    "Stock Units",
            "expiry_date":       "Expiry Date",
            "days_to_expiry":    "Days to Expiry",
            "batch_number":      "Batch #",
            "manufacturer":      "Manufacturer",
            "storage_condition": "Storage",
        }),
        use_container_width=True, height=480, hide_index=True,
    )

    rc1, rc2 = st.columns([1, 5])
    with rc1:
        st.markdown(f"""
        <div style="font-size:0.875rem;color:{t['text_secondary']};padding-top:0.5rem;">
            Showing <strong style="color:{t['text']};">{len(table):,}</strong> records
        </div>
        """, unsafe_allow_html=True)
    with rc2:
        st.download_button(
            "⬇ Export filtered view as CSV",
            table.to_csv(index=False).encode("utf-8"),
            "inventory_export.csv", "text/csv",
        )