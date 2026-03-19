import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from data_generator import (
    generate_all_products, generate_npi_timeline,
    generate_inline_control_chart, generate_excursion_log,
    PRODUCTS, PROCESS_STEPS, INLINE_METRICS, EXCURSION_RULES
)
import warnings
warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NPI Yield Learning Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }

.stApp { background-color: #060b14; color: #dde6f0; }

.kpi-card {
    background: linear-gradient(160deg, #0b1628 0%, #0e1e35 100%);
    border: 1px solid #1a3354;
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 18px 20px;
}
.kpi-label {
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a6fa5;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 4px;
}
.kpi-value {
    font-size: 30px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    color: var(--val-color, #e2e8f0);
}
.kpi-sub {
    font-size: 11px;
    color: #4a6fa5;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
}

.badge-open     { background:#2a0f0f; color:#ef4444; border:1px solid #ef444440; padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:11px; }
.badge-review   { background:#2a200a; color:#f59e0b; border:1px solid #f59e0b40; padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:11px; }
.badge-closed   { background:#0a2010; color:#22c55e; border:1px solid #22c55e40; padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:11px; }
.badge-critical { background:#2a0f0f; color:#ef4444; border:1px solid #ef444440; padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:11px; }
.badge-warning  { background:#2a200a; color:#f59e0b; border:1px solid #f59e0b40; padding:2px 8px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:11px; }

.section-header {
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a9eff;
    font-family: 'JetBrains Mono', monospace;
    border-bottom: 1px solid #112244;
    padding-bottom: 6px;
    margin: 20px 0 14px 0;
}
.ramp-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    margin: 2px;
}
.phase-ramp   { background:#1a1a3a; color:#8b5cf6; border:1px solid #8b5cf640; }
.phase-mid    { background:#1a2a1a; color:#22c55e; border:1px solid #22c55e40; }
.phase-hvm    { background:#1a2a3a; color:#38bdf8; border:1px solid #38bdf840; }

div[data-testid="stSidebar"] { background:#06101e; border-right:1px solid #0e1e35; }
h1 { color:#e8f4ff !important; font-weight:700 !important; font-family:'Rajdhani',sans-serif !important; }
h2, h3 { color:#b0c8e4 !important; font-family:'Rajdhani',sans-serif !important; }
</style>
""", unsafe_allow_html=True)

PLOT_DEFAULTS = dict(
    plot_bgcolor="#060b14",
    paper_bgcolor="#060b14",
    font=dict(color="#7a9cc4", family="JetBrains Mono"),
    margin=dict(l=0, r=0, t=10, b=0),
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ NPI Yield Platform")
    st.markdown("---")
    page = st.radio(
        "NAVIGATION",
        ["🏠 NPI Overview", "📉 Yield Ramp", "🔧 Inline Control", "🚨 Excursion Manager", "📋 NPI Config"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown('<div style="color:#4a6fa5;font-size:10px;font-family:JetBrains Mono,monospace;letter-spacing:2px">PRODUCT SELECTION</div>', unsafe_allow_html=True)
    selected_product = st.selectbox("Product", list(PRODUCTS.keys()))
    selected_step = st.selectbox("Process Step", ["All"] + PROCESS_STEPS)
    n_lots = st.slider("Lot History", 10, 50, 30)
    st.markdown("---")
    st.markdown('<div style="color:#2a4060;font-size:10px;font-family:JetBrains Mono,monospace">PTM Yield Systems<br>NPI Intelligence v3.0<br>© 2025</div>', unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_all(n):
    return generate_all_products(n_lots=n)

all_df = load_all(n_lots)
product_df = all_df[all_df["product_id"] == selected_product].copy()
exc_log = generate_excursion_log(all_df)

if selected_step != "All":
    product_df = product_df[product_df["process_step"] == selected_step]


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 — NPI OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
if page == "🏠 NPI Overview":
    st.markdown("# NPI Yield Learning Dashboard")
    st.markdown('<div style="color:#4a6fa5;font-family:JetBrains Mono,monospace;font-size:12px;margin-bottom:24px">New Product Introduction · Inline Monitoring · Excursion Detection</div>', unsafe_allow_html=True)

    prod_info = PRODUCTS[selected_product]
    avg_yield = product_df["yield_pct"].mean()
    excursions = product_df["excursion"].sum()
    hvm_yield = product_df[product_df["ramp_phase"] == "HVM"]["yield_pct"].mean()
    gap_to_target = hvm_yield - prod_info["target_yield"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        col = "#22c55e" if avg_yield >= prod_info["target_yield"] else "#f59e0b"
        st.markdown(f"""<div class="kpi-card" style="--accent:{prod_info['color']}">
            <div class="kpi-label">Avg Yield (All Lots)</div>
            <div class="kpi-value" style="color:{col}">{avg_yield:.1f}%</div>
            <div class="kpi-sub">Target: {prod_info['target_yield']}%</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        col = "#22c55e" if hvm_yield >= prod_info["target_yield"] else "#ef4444"
        st.markdown(f"""<div class="kpi-card" style="--accent:#22c55e">
            <div class="kpi-label">HVM Phase Yield</div>
            <div class="kpi-value" style="color:{col}">{hvm_yield:.1f}%</div>
            <div class="kpi-sub">Gap: {gap_to_target:+.1f}%</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        col = "#ef4444" if excursions > 5 else "#f59e0b" if excursions > 2 else "#22c55e"
        st.markdown(f"""<div class="kpi-card" style="--accent:#ef4444">
            <div class="kpi-label">Excursions Detected</div>
            <div class="kpi-value" style="color:{col}">{int(excursions)}</div>
            <div class="kpi-sub">{len(product_df)} lots analyzed</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card" style="--accent:#8b5cf6">
            <div class="kpi-label">Package Layers</div>
            <div class="kpi-value" style="color:#8b5cf6">{prod_info['layers']}</div>
            <div class="kpi-sub">Advanced Packaging</div>
        </div>""", unsafe_allow_html=True)

    # Multi-product yield comparison
    st.markdown('<div class="section-header">Yield Ramp Comparison — All Products</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for pid, pinfo in PRODUCTS.items():
        sub = all_df[all_df["product_id"] == pid].groupby("lot_index")["yield_pct"].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=sub["lot_index"], y=sub["yield_pct"],
            name=pid, mode="lines+markers",
            line=dict(color=pinfo["color"], width=2),
            marker=dict(size=5, color=pinfo["color"]),
        ))
        fig.add_hline(y=pinfo["target_yield"], line_dash="dot",
                      line_color=pinfo["color"], opacity=0.4)
    fig.update_layout(**PLOT_DEFAULTS,
        yaxis=dict(gridcolor="#0e1e35", range=[20, 100], title="Yield %"),
        xaxis=dict(showgrid=False, title="Lot Index"),
        legend=dict(bgcolor="#06101e", bordercolor="#112244", borderwidth=1, font=dict(size=10)),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Phase distribution
    st.markdown('<div class="section-header">Ramp Phase Distribution by Product</div>', unsafe_allow_html=True)
    phase_counts = all_df.groupby(["product_id", "ramp_phase"]).size().reset_index(name="count")
    fig2 = px.bar(phase_counts, x="product_id", y="count", color="ramp_phase",
                  color_discrete_map={"Ramp-Up": "#8b5cf6", "Ramp-Mid": "#22c55e", "HVM": "#38bdf8"},
                  barmode="stack")
    fig2.update_layout(**PLOT_DEFAULTS,
        yaxis=dict(gridcolor="#0e1e35"),
        xaxis=dict(showgrid=False),
        legend=dict(bgcolor="#06101e", bordercolor="#112244", borderwidth=1, font=dict(size=10)),
        height=240,
    )
    st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — YIELD RAMP
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📉 Yield Ramp":
    st.markdown(f"# Yield Ramp — {selected_product}")
    prod_info = PRODUCTS[selected_product]

    # Ramp curve with phases
    st.markdown('<div class="section-header">Lot-by-Lot Yield Ramp with Phase Boundaries</div>', unsafe_allow_html=True)

    full_product_df = all_df[all_df["product_id"] == selected_product].copy()
    ramp_up_end = int(n_lots * 0.4)
    mid_end = int(n_lots * 0.7)

    fig = go.Figure()
    fig.add_vrect(x0=0, x1=ramp_up_end, fillcolor="#8b5cf6", opacity=0.04, line_width=0)
    fig.add_vrect(x0=ramp_up_end, x1=mid_end, fillcolor="#22c55e", opacity=0.04, line_width=0)
    fig.add_vrect(x0=mid_end, x1=n_lots, fillcolor="#38bdf8", opacity=0.04, line_width=0)

    # Add phase labels
    for x, label, color in [
        (ramp_up_end / 2, "RAMP-UP", "#8b5cf6"),
        ((ramp_up_end + mid_end) / 2, "RAMP-MID", "#22c55e"),
        ((mid_end + n_lots) / 2, "HVM", "#38bdf8"),
    ]:
        fig.add_annotation(x=x, y=95, text=label, showarrow=False,
                           font=dict(color=color, size=10, family="JetBrains Mono"),
                           opacity=0.7)

    # Excursion markers
    exc_lots = full_product_df[full_product_df["excursion"]]
    fig.add_trace(go.Scatter(
        x=exc_lots["lot_index"], y=exc_lots["yield_pct"],
        mode="markers", name="Excursion",
        marker=dict(color="#ef4444", size=12, symbol="x", line=dict(width=2, color="#ef4444")),
    ))

    # Yield line
    fig.add_trace(go.Scatter(
        x=full_product_df["lot_index"], y=full_product_df["yield_pct"],
        mode="lines+markers", name="Yield %",
        line=dict(color=prod_info["color"], width=2.5),
        marker=dict(size=5, color=prod_info["color"]),
    ))

    # Rolling average
    rolling = full_product_df["yield_pct"].rolling(3, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=full_product_df["lot_index"], y=rolling,
        mode="lines", name="3-lot Rolling Avg",
        line=dict(color="#f59e0b", width=2, dash="dash"),
    ))

    fig.add_hline(y=prod_info["target_yield"], line_dash="dot",
                  line_color="#94a3b8", annotation_text=f"Target {prod_info['target_yield']}%",
                  annotation_font_color="#94a3b8")

    fig.update_layout(**PLOT_DEFAULTS,
        yaxis=dict(gridcolor="#0e1e35", range=[10, 105], title="Yield %"),
        xaxis=dict(showgrid=False, title="Lot Index"),
        legend=dict(bgcolor="#06101e", bordercolor="#112244", borderwidth=1, font=dict(size=10)),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Phase stats
    col1, col2, col3 = st.columns(3)
    for col, phase, label, badge in zip(
        [col1, col2, col3],
        ["Ramp-Up", "Ramp-Mid", "HVM"],
        ["Ramp-Up", "Ramp-Mid", "High Volume Mfg"],
        ["phase-ramp", "phase-mid", "phase-hvm"]
    ):
        sub = full_product_df[full_product_df["ramp_phase"] == phase]
        if sub.empty:
            continue
        with col:
            avg = sub["yield_pct"].mean()
            excs = sub["excursion"].sum()
            st.markdown(f"""<div class="kpi-card" style="--accent:#1a3354">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="font-size:24px;color:#e2e8f0">{avg:.1f}%</div>
                <div class="kpi-sub">{len(sub)} lots · {int(excs)} excursions</div>
            </div>""", unsafe_allow_html=True)

    # Metric correlations
    st.markdown('<div class="section-header">Inline Metrics vs Yield</div>', unsafe_allow_html=True)
    metric_cols = {
        "Defect Density": "defect_density",
        "Overlay Error (nm)": "overlay_error_nm",
        "CD Uniformity (%)": "cd_uniformity_pct",
    }
    fig2 = make_subplots(rows=1, cols=3, subplot_titles=list(metric_cols.keys()))
    colors_map = {True: "#ef4444", False: prod_info["color"]}
    for idx, (label, col_name) in enumerate(metric_cols.items(), 1):
        fig2.add_trace(go.Scatter(
            x=full_product_df[col_name],
            y=full_product_df["yield_pct"],
            mode="markers",
            marker=dict(
                size=6,
                color=[colors_map[e] for e in full_product_df["excursion"]],
                opacity=0.7,
            ),
            showlegend=False,
        ), row=1, col=idx)
    fig2.update_layout(**PLOT_DEFAULTS,
        height=280,
        yaxis=dict(gridcolor="#0e1e35", title="Yield %"),
        yaxis2=dict(gridcolor="#0e1e35"),
        yaxis3=dict(gridcolor="#0e1e35"),
    )
    for i in range(1, 4):
        fig2.update_xaxes(showgrid=False, row=1, col=i)
    st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 — INLINE CONTROL CHART
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🔧 Inline Control":
    st.markdown(f"# Inline Process Control — {selected_product}")
    st.markdown('<div style="color:#4a6fa5;font-family:JetBrains Mono,monospace;font-size:12px;margin-bottom:24px">SPC Control Charts · Excursion Detection · 3σ Limits</div>', unsafe_allow_html=True)

    metric = st.selectbox("Select Metric", INLINE_METRICS)
    ctrl_df = generate_inline_control_chart(selected_product, metric)
    rule = EXCURSION_RULES.get(metric, {})

    fig = go.Figure()

    # UCL / LCL / CL bands
    fig.add_hrect(y0=ctrl_df["LCL"].iloc[0], y1=ctrl_df["UCL"].iloc[0],
                  fillcolor="rgba(56,189,248,0.04)", line_width=0)

    for line_val, label, color, dash in [
        (ctrl_df["UCL"].iloc[0], "UCL", "#ef4444", "dash"),
        (ctrl_df["CL"].iloc[0],  "CL",  "#f59e0b", "solid"),
        (ctrl_df["LCL"].iloc[0], "LCL", "#ef4444", "dash"),
    ]:
        fig.add_hline(y=line_val, line_dash=dash, line_color=color, opacity=0.7,
                      annotation_text=label, annotation_font_color=color,
                      annotation_font_size=10)

    # In-control points
    in_ctrl = ctrl_df[~ctrl_df["out_of_control"]]
    fig.add_trace(go.Scatter(
        x=in_ctrl["sample"], y=in_ctrl["value"],
        mode="lines+markers", name="In Control",
        line=dict(color="#38bdf8", width=1.5),
        marker=dict(size=6, color="#38bdf8"),
    ))

    # Out-of-control points
    out_ctrl = ctrl_df[ctrl_df["out_of_control"]]
    fig.add_trace(go.Scatter(
        x=out_ctrl["sample"], y=out_ctrl["value"],
        mode="markers", name="Out of Control",
        marker=dict(size=10, color="#ef4444", symbol="diamond",
                    line=dict(width=1.5, color="#ff6b6b")),
    ))

    fig.update_layout(**PLOT_DEFAULTS,
        yaxis=dict(gridcolor="#0e1e35", title=metric),
        xaxis=dict(showgrid=False, title="Sample #"),
        legend=dict(bgcolor="#06101e", bordercolor="#112244", borderwidth=1, font=dict(size=10)),
        height=360,
    )
    st.plotly_chart(fig, use_container_width=True)

    # SPC Stats
    col1, col2, col3, col4 = st.columns(4)
    vals = ctrl_df["value"]
    n_ooc = ctrl_df["out_of_control"].sum()
    cp = (ctrl_df["UCL"].iloc[0] - ctrl_df["LCL"].iloc[0]) / (6 * vals.std()) if vals.std() > 0 else 0

    with col1:
        st.markdown(f"""<div class="kpi-card" style="--accent:#38bdf8">
            <div class="kpi-label">Mean</div>
            <div class="kpi-value" style="font-size:22px;color:#e2e8f0">{vals.mean():.4f}</div>
            <div class="kpi-sub">{metric}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="kpi-card" style="--accent:#8b5cf6">
            <div class="kpi-label">Std Dev (σ)</div>
            <div class="kpi-value" style="font-size:22px;color:#8b5cf6">{vals.std():.4f}</div>
            <div class="kpi-sub">Process Variation</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        col = "#ef4444" if n_ooc > 3 else "#f59e0b" if n_ooc > 1 else "#22c55e"
        st.markdown(f"""<div class="kpi-card" style="--accent:{col}">
            <div class="kpi-label">OOC Samples</div>
            <div class="kpi-value" style="font-size:22px;color:{col}">{int(n_ooc)}</div>
            <div class="kpi-sub">of {len(ctrl_df)} total</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        col = "#22c55e" if cp >= 1.33 else "#f59e0b" if cp >= 1.0 else "#ef4444"
        st.markdown(f"""<div class="kpi-card" style="--accent:{col}">
            <div class="kpi-label">Process Capability (Cp)</div>
            <div class="kpi-value" style="font-size:22px;color:{col}">{cp:.3f}</div>
            <div class="kpi-sub">≥1.33 = Capable</div>
        </div>""", unsafe_allow_html=True)

    # Distribution
    st.markdown('<div class="section-header">Value Distribution</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=ctrl_df["value"], nbinsx=20,
        marker_color="#38bdf8", opacity=0.7, name="Distribution",
    ))
    fig2.add_vline(x=ctrl_df["CL"].iloc[0], line_color="#f59e0b",
                   annotation_text="CL", annotation_font_color="#f59e0b")
    fig2.add_vline(x=ctrl_df["UCL"].iloc[0], line_color="#ef4444", line_dash="dash",
                   annotation_text="UCL", annotation_font_color="#ef4444")
    fig2.add_vline(x=ctrl_df["LCL"].iloc[0], line_color="#ef4444", line_dash="dash",
                   annotation_text="LCL", annotation_font_color="#ef4444")
    fig2.update_layout(**PLOT_DEFAULTS,
        yaxis=dict(gridcolor="#0e1e35"),
        xaxis=dict(showgrid=False, title=metric),
        height=220,
    )
    st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 — EXCURSION MANAGER
# ═══════════════════════════════════════════════════════════════════════════
elif page == "🚨 Excursion Manager":
    st.markdown("# Excursion Manager")
    st.markdown('<div style="color:#4a6fa5;font-family:JetBrains Mono,monospace;font-size:12px;margin-bottom:24px">Automated excursion detection · Rule-based alerting · Status tracking</div>', unsafe_allow_html=True)

    # Summary cards
    total_exc = len(exc_log)
    open_exc = (exc_log["status"] == "Open").sum()
    critical_exc = (exc_log["severity"] == "critical").sum()
    closed_exc = (exc_log["status"] == "Closed").sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="kpi-card" style="--accent:#ef4444">
            <div class="kpi-label">Total Excursions</div>
            <div class="kpi-value" style="color:#e2e8f0">{total_exc}</div>
            <div class="kpi-sub">All products</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card" style="--accent:#ef4444">
            <div class="kpi-label">Open</div>
            <div class="kpi-value" style="color:#ef4444">{int(open_exc)}</div>
            <div class="kpi-sub">Requires action</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card" style="--accent:#f59e0b">
            <div class="kpi-label">Critical Severity</div>
            <div class="kpi-value" style="color:#f59e0b">{int(critical_exc)}</div>
            <div class="kpi-sub">Immediate escalation</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card" style="--accent:#22c55e">
            <div class="kpi-label">Closed</div>
            <div class="kpi-value" style="color:#22c55e">{int(closed_exc)}</div>
            <div class="kpi-sub">Resolved</div>
        </div>""", unsafe_allow_html=True)

    # Excursion table
    st.markdown('<div class="section-header">Excursion Log</div>', unsafe_allow_html=True)

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        filter_product = st.multiselect("Product", list(PRODUCTS.keys()), default=list(PRODUCTS.keys()))
    with filter_col2:
        filter_status = st.multiselect("Status", ["Open", "In Review", "Closed"], default=["Open", "In Review", "Closed"])
    with filter_col3:
        filter_severity = st.multiselect("Severity", ["critical", "warning"], default=["critical", "warning"])

    filtered_exc = exc_log[
        exc_log["product_id"].isin(filter_product) &
        exc_log["status"].isin(filter_status) &
        exc_log["severity"].isin(filter_severity)
    ].copy()

    filtered_exc["date"] = filtered_exc["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(filtered_exc, use_container_width=True, height=280, hide_index=True)

    # Excursion breakdown charts
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="section-header">Excursions by Product</div>', unsafe_allow_html=True)
        by_prod = exc_log.groupby(["product_id", "severity"]).size().reset_index(name="count")
        fig = px.bar(by_prod, x="product_id", y="count", color="severity",
                     color_discrete_map={"critical": "#ef4444", "warning": "#f59e0b"},
                     barmode="group")
        fig.update_layout(**PLOT_DEFAULTS, height=240,
                          yaxis=dict(gridcolor="#0e1e35"),
                          xaxis=dict(showgrid=False),
                          legend=dict(bgcolor="#06101e", bordercolor="#112244", borderwidth=1, font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header">Excursions by Metric Triggered</div>', unsafe_allow_html=True)
        by_metric = exc_log["excursion_metric"].value_counts().reset_index()
        by_metric.columns = ["metric", "count"]
        fig2 = go.Figure(go.Bar(
            x=by_metric["count"], y=by_metric["metric"],
            orientation="h",
            marker_color=["#ef4444", "#f59e0b", "#8b5cf6", "#38bdf8"][:len(by_metric)],
            opacity=0.85,
        ))
        fig2.update_layout(**PLOT_DEFAULTS, height=240,
                           xaxis=dict(gridcolor="#0e1e35"),
                           yaxis=dict(showgrid=False))
        st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 — NPI CONFIG
# ═══════════════════════════════════════════════════════════════════════════
elif page == "📋 NPI Config":
    st.markdown("# NPI Product Configuration")
    st.markdown('<div style="color:#4a6fa5;font-family:JetBrains Mono,monospace;font-size:12px;margin-bottom:24px">Product onboarding · Threshold configuration · Rule management</div>', unsafe_allow_html=True)

    prod_info = PRODUCTS[selected_product]

    col_form, col_preview = st.columns([1, 1])
    with col_form:
        st.markdown('<div class="section-header">Product Parameters</div>', unsafe_allow_html=True)
        pkg_layers = st.number_input("Package Layers", value=prod_info["layers"], min_value=1, max_value=32)
        target_yield = st.slider("Target Yield (%)", 50, 99, prod_info["target_yield"])
        target_density = st.number_input("Target Defect Density (defects/cm²)", value=prod_info["target_density"], format="%.4f")

        st.markdown('<div class="section-header">Alert Rule Thresholds</div>', unsafe_allow_html=True)
        rules = {}
        for metric, rule in EXCURSION_RULES.items():
            col_m, col_s = st.columns([2, 1])
            with col_m:
                val = st.number_input(
                    metric,
                    value=float(rule["threshold"]),
                    format="%.3f",
                    key=f"rule_{metric}"
                )
            with col_s:
                sev = st.selectbox("", ["critical", "warning", "info"],
                                   index=["critical", "warning", "info"].index(rule["severity"]),
                                   key=f"sev_{metric}")
            rules[metric] = {"threshold": val, "severity": sev}

        if st.button("💾 Save Configuration", use_container_width=True):
            st.success(f"✅ Configuration for **{selected_product}** saved. {len(rules)} rules active.")

    with col_preview:
        st.markdown('<div class="section-header">Configuration Preview</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div style="background:#0b1628;border:1px solid #1a3354;border-radius:8px;padding:20px;font-family:JetBrains Mono,monospace;font-size:12px;color:#7aa2d4">
<div style="color:{prod_info['color']};font-weight:700;font-size:14px;margin-bottom:12px">▶ {selected_product}</div>
<div style="color:#4a6fa5;font-size:10px;letter-spacing:2px;margin-bottom:8px">PRODUCT SPEC</div>
<div>Package Layers: <span style="color:#e2e8f0">{pkg_layers}</span></div>
<div>Target Yield: <span style="color:#22c55e">{target_yield}%</span></div>
<div>Target Density: <span style="color:#38bdf8">{target_density:.4f} def/cm²</span></div>
<br>
<div style="color:#4a6fa5;font-size:10px;letter-spacing:2px;margin-bottom:8px">ALERT RULES</div>
{''.join([f'<div style="margin:4px 0">{m}: <span style="color:#f59e0b">≥ {r["threshold"]:.3f}</span> → <span style="color:#ef4444">{r["severity"].upper()}</span></div>' for m, r in rules.items()])}
<br>
<div style="color:#4a6fa5;font-size:10px;letter-spacing:2px;margin-bottom:8px">PROCESS STEPS</div>
{''.join([f'<div>· {step}</div>' for step in PROCESS_STEPS])}
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">Onboarding Checklist</div>', unsafe_allow_html=True)
        checklist_items = [
            ("Product ID registered", True),
            ("Process steps configured", True),
            ("Alert thresholds set", True),
            ("Metrology integration tested", True),
            ("NPI team notified", False),
            ("First lot released", False),
        ]
        for item, done in checklist_items:
            icon = "✅" if done else "⬜"
            color = "#22c55e" if done else "#4a6fa5"
            st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:12px;color:{color};margin:6px 0">{icon} {item}</div>', unsafe_allow_html=True)
