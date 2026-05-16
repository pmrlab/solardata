import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import glob
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(layout="wide", page_title="Net Zero Dashboard")

# =====================================================
# VERSION-SAFE TRAPEZOID INTEGRATION
# =====================================================
_trapezoid = getattr(np, "trapezoid", None) or getattr(np, "trapz", None)

# =====================================================
# EMISSION FACTORS (per kWh of PV yield)
# =====================================================
CO2_PER_KWH    = 0.997
COAL_PER_KWH   = 0.404
TREES_PER_KWH  = 0.054

# =====================================================
# UI STYLING
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

header {visibility: hidden;}
footer {visibility: hidden;}

html, body, .stApp {
    background-color: #0D1117 !important;
    color: #E6EDF3 !important;
    font-family: 'Inter', sans-serif !important;
}

.block-container {
    padding-top: 130px !important;
    padding-bottom: 30px !important;
    max-width: 100% !important;
}

/* ── HEADER ── */
.fixed-header {
    position: fixed;
    top: 0; left: 0;
    width: 100%;
    height: 115px;
    background: linear-gradient(180deg, #161B22 0%, #0D1117 100%);
    z-index: 10000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-bottom: 1px solid #30363D;
    box-shadow: 0 2px 16px rgba(0,0,0,0.5);
}
.header-title {
    font-family: 'Inter', sans-serif;
    font-size: 40px;
    font-weight: 700;
    color: #E6EDF3;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.header-title span.accent { color: #58A6FF; }
.header-sub {
    font-size: 13px;
    font-weight: 400;
    color: #8B949E;
    letter-spacing: 0.3px;
}

/* ── DATE INPUT ── */
.stDateInput label { display: none; }
.stDateInput > div > div > input {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #58A6FF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
}

/* ── SECTION TITLE ── */
.section-title {
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 600;
    color: #E6EDF3;
    letter-spacing: 0.3px;
    margin-bottom: 4px;
}

/* ── PLANT TITLE ── */
.plant-title {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: #58A6FF;
    margin-bottom: -8px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── KPI CARD — POWER ── */
.kpi-card {
    background: #161B22;
    border: 1px solid #30363D;
    padding: 22px 28px;
    border-radius: 10px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #58A6FF, #1F6FEB);
    border-radius: 10px 10px 0 0;
}
/* KPI label — bright and bold */
.kpi-label {
    font-family: 'Inter', sans-serif;
    color: #C9D1D9;          /* was #7D8590 — now clearly visible */
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    color: #FFFFFF;
    font-size: 36px;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.kpi-unit {
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    color: #8B949E;
    font-weight: 500;
    margin-left: 5px;
}

/* ── ECO CARD ── */
.eco-card {
    background: #161B22;
    border: 1px solid #30363D;
    padding: 20px 20px;
    border-radius: 10px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.eco-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 10px 10px 0 0;
}
.eco-card.co2::after  { background: linear-gradient(90deg, #3FB950, #238636); }
.eco-card.coal::after { background: linear-gradient(90deg, #E3B341, #BB8009); }
.eco-card.tree::after { background: linear-gradient(90deg, #58A6FF, #1F6FEB); }

.eco-icon { font-size: 26px; margin-bottom: 6px; }

/* ECO label — bright and bold */
.eco-label {
    font-family: 'Inter', sans-serif;
    color: #C9D1D9;          /* was #7D8590 — now clearly visible */
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.eco-value {
    font-family: 'JetBrains Mono', monospace;
    color: #FFFFFF;
    font-size: 28px;
    font-weight: 700;
}
.eco-unit {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #8B949E;
    font-weight: 500;
    margin-left: 4px;
}

/* ── DIVIDER ── */
.section-divider {
    border: none;
    border-top: 1px solid #21262D;
    margin: 14px 0 10px 0;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0D1117; }
::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #58A6FF; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="fixed-header">
    <div class="header-title">🌍 Pathways to <span class="accent">Net Zero</span></div>
    <div class="header-sub">Bridging Industry and Academia for Sustainable Energy Solutions in India</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# PATHS
# =====================================================
BASE_DIR = "isolar_data"

PLANTS = {
    "Electronic 1": os.path.join(BASE_DIR, "Electronic 1", "*"),
    "Electronic 2": os.path.join(BASE_DIR, "Electronic 2", "*"),
    "MIIC-1":       os.path.join(BASE_DIR, "miic1", "*"),
    "MIIC-2":       os.path.join(BASE_DIR, "miic2", "*"),
    "Multipath 1":  os.path.join(BASE_DIR, "Multipath 1", "*"),
    "Multipath 2":  os.path.join(BASE_DIR, "Multipath 2", "*"),
    "Multipath 3":  os.path.join(BASE_DIR, "Multipath 3", "*"),
    "Multipath 4":  os.path.join(BASE_DIR, "Multipath 4", "*"),
    "Multipath 5":  os.path.join(BASE_DIR, "Multipath 5", "*"),
    "Prabha 01":    os.path.join(BASE_DIR, "Prabha 01", "*"),
    "Prabha 02":    os.path.join(BASE_DIR, "Prabha 02", "*"),
}

# =====================================================
# DATE SELECTION
# =====================================================
selected_date = st.date_input(
    "",
    value=pd.Timestamp.now().date(),
    max_value=pd.Timestamp.now().date(),
    label_visibility="collapsed"
)

# =====================================================
# HELPERS
# =====================================================
def load_file_by_date(path, target_date):
    files = sorted(glob.glob(path))
    if not files:
        return None
    date_str = target_date.strftime("%Y%m%d")
    matching = [f for f in files if date_str in os.path.basename(f)]
    if not matching:
        return None
    try:
        return pd.read_excel(matching[-1])
    except:
        try:
            return pd.read_csv(matching[-1])
        except:
            return None


def normalize(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    t  = [c for c in df.columns if "time" in c]
    dc = [c for c in df.columns if "dc" in c]
    ac = [c for c in df.columns if "active" in c or "ac" in c]
    if not (t and dc and ac):
        return None, None, None, None
    t, dc, ac = t[0], dc[0], ac[0]
    df[t]  = pd.to_datetime(df[t],  errors="coerce")
    df[dc] = pd.to_numeric(df[dc],  errors="coerce")
    df[ac] = pd.to_numeric(df[ac],  errors="coerce")
    df = df.dropna(subset=[t, dc, ac]).sort_values(t)
    if df.empty:
        return None, None, None, None
    return df, t, dc, ac


def compute_daily_energy_kwh(df, t, dc):
    if df is None or len(df) < 2:
        return 0.0
    times_h = (df[t] - df[t].iloc[0]).dt.total_seconds().values / 3600.0
    energy  = float(_trapezoid(df[dc].values, x=times_h))
    return max(energy, 0.0)


# ── AXIS COLORS (bright enough to read clearly) ──────
AXIS_TITLE_COLOR = "#C9D1D9"   # near-white, clearly readable
AXIS_TICK_COLOR  = "#8B949E"   # medium grey, readable
GRID_COLOR       = "#21262D"
LINE_COLOR       = "#30363D"


def small_plot(df, t, dc, ac, plant_name=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[t], y=df[dc], name="DC Power",
        line=dict(color="#E3B341", width=1.8),
        fill="tozeroy", fillcolor="rgba(227,179,65,0.12)",
        hovertemplate="<b>%{x|%H:%M}</b><br>DC: <b>%{y:.1f} kW</b><extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df[t], y=df[ac], name="AC Power",
        line=dict(color="#58A6FF", width=1.8),
        hovertemplate="<b>%{x|%H:%M}</b><br>AC: <b>%{y:.1f} kW</b><extra></extra>"
    ))
    fig.update_layout(
        height=130, showlegend=False, hovermode="x unified",
        plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
        margin=dict(l=44, r=4, t=4, b=32),
        font=dict(color=AXIS_TICK_COLOR, family="Inter", size=10),
        xaxis=dict(
            title=dict(text="Time", font=dict(color=AXIS_TITLE_COLOR, size=10, family="Inter")),
            gridcolor=GRID_COLOR, tickfont=dict(color=AXIS_TICK_COLOR, size=9),
            zeroline=False, linecolor=LINE_COLOR
        ),
        yaxis=dict(
            title=dict(text="kW", font=dict(color=AXIS_TITLE_COLOR, size=10, family="Inter")),
            gridcolor=GRID_COLOR, tickfont=dict(color=AXIS_TICK_COLOR, size=9),
            zeroline=False, linecolor=LINE_COLOR
        ),
        hoverlabel=dict(
            bgcolor="#161B22", bordercolor="#30363D",
            font=dict(color="#E6EDF3", size=11, family="JetBrains Mono")
        )
    )
    return fig


# =====================================================
# DASHBOARD CONTENT
# =====================================================
@st.fragment(run_every=180)
def render_dashboard_content(current_date):
    all_data          = []
    VALID_PLANTS_DATA = {}
    daily_energy_kwh  = 0.0

    for name, path in PLANTS.items():
        raw = load_file_by_date(path, current_date)
        if raw is not None:
            df, t, dc, ac = normalize(raw)
            if df is not None:
                VALID_PLANTS_DATA[name] = (df, t, dc, ac)
                daily_energy_kwh += compute_daily_energy_kwh(df, t, dc)
                all_data.append(pd.DataFrame({"time": df[t], "dc": df[dc], "ac": df[ac]}))

    total_dc, total_ac = 0, 0
    df_agg = None
    if all_data:
        df_agg   = pd.concat(all_data).groupby("time").sum().reset_index()
        total_dc = df_agg["dc"].max()
        total_ac = df_agg["ac"].max()

    co2_reduced_ton  = (daily_energy_kwh * CO2_PER_KWH)  / 1000
    coal_saved_ton   = (daily_energy_kwh * COAL_PER_KWH) / 1000
    trees_equivalent =  daily_energy_kwh * TREES_PER_KWH

    col_grid, col_main = st.columns([2, 3.5])

    # ── LEFT GRID ──
    with col_grid:
        g_cols = st.columns(2)
        if not VALID_PLANTS_DATA:
            st.warning(f"No data found for {current_date.strftime('%d %b %Y')}.")
        else:
            for i, (name, data) in enumerate(VALID_PLANTS_DATA.items()):
                df, t, dc, ac = data
                with g_cols[i % 2]:
                    st.markdown(f'<p class="plant-title">{name}</p>', unsafe_allow_html=True)
                    st.plotly_chart(
                        small_plot(df, t, dc, ac, plant_name=name),
                        use_container_width=True,
                        config={'displayModeBar': False}
                    )

    # ── RIGHT: CHART + KPIs ──
    with col_main:
        st.markdown('<div class="section-title">🔴 &nbsp;Aggregated Output</div>', unsafe_allow_html=True)

        if df_agg is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_agg["time"], y=df_agg["dc"],
                name="DC Power (All Plants)",
                line=dict(color="#E3B341", width=2.5),
                fill="tozeroy", fillcolor="rgba(227,179,65,0.10)",
                hovertemplate="DC Power: <b>%{y:.1f} kW</b><extra></extra>"
            ))
            fig.add_trace(go.Scatter(
                x=df_agg["time"], y=df_agg["ac"],
                name="AC Power (All Plants)",
                line=dict(color="#58A6FF", width=2.5),
                hovertemplate="AC Power: <b>%{y:.1f} kW</b><extra></extra>"
            ))
            fig.update_layout(
                height=380, hovermode="x unified",
                plot_bgcolor="#0D1117", paper_bgcolor="#0D1117",
                margin=dict(l=70, r=10, t=10, b=55),
                font=dict(color=AXIS_TICK_COLOR, family="Inter", size=11),
                xaxis=dict(
                    title=dict(
                        text="Time",
                        font=dict(color=AXIS_TITLE_COLOR, size=13, family="Inter")
                    ),
                    gridcolor=GRID_COLOR,
                    tickfont=dict(color=AXIS_TICK_COLOR, size=11),
                    tickformat="%H:%M",
                    zeroline=False, linecolor=LINE_COLOR
                ),
                yaxis=dict(
                    title=dict(
                        text="Power (kW)",
                        font=dict(color=AXIS_TITLE_COLOR, size=13, family="Inter")
                    ),
                    gridcolor=GRID_COLOR,
                    tickfont=dict(color=AXIS_TICK_COLOR, size=11),
                    zeroline=False, linecolor=LINE_COLOR
                ),
                hoverlabel=dict(
                    bgcolor="#161B22", bordercolor="#30363D",
                    font=dict(color="#E6EDF3", size=13, family="JetBrains Mono")
                ),
                legend=dict(
                    bgcolor="#161B22", bordercolor="#30363D", borderwidth=1,
                    font=dict(color="#C9D1D9", size=12),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Awaiting data for {current_date.strftime('%d %b %Y')}...")

        # ── POWER KPI CARDS ──
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        k1, k2 = st.columns(2)
        with k1:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">⚡ Peak DC Power</div>
                <div class="kpi-value">{total_dc:,.0f}<span class="kpi-unit">kW</span></div>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">🔌 Peak AC Power</div>
                <div class="kpi-value">{total_ac:,.0f}<span class="kpi-unit">kW</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)

        # ── DAILY ENERGY KPI ──
        st.markdown(f"""<div class="kpi-card" style="margin-bottom:14px;">
            <div class="kpi-label">☀️ Energy analysis — {current_date.strftime('%d %b %Y')}</div>
            <div class="kpi-value">{daily_energy_kwh:,.1f}<span class="kpi-unit">kWh</span></div>
        </div>""", unsafe_allow_html=True)

        # ── EMISSION KPI CARDS ──
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title" style="font-size:14px; color:#C9D1D9; margin-bottom:10px;">'
            '🌿 &nbsp;Emission Reduction — Daily Estimate</div>',
            unsafe_allow_html=True
        )

        e1, e2, e3 = st.columns(3)
        with e1:
            st.markdown(f"""<div class="eco-card co2">
                <div class="eco-icon">💨</div>
                <div class="eco-label">CO₂ Reduced</div>
                <div class="eco-value">{co2_reduced_ton:,.3f}<span class="eco-unit">ton</span></div>
            </div>""", unsafe_allow_html=True)
        with e2:
            st.markdown(f"""<div class="eco-card coal">
                <div class="eco-icon">🪨</div>
                <div class="eco-label">Coal Saved</div>
                <div class="eco-value">{coal_saved_ton:,.3f}<span class="eco-unit">ton</span></div>
            </div>""", unsafe_allow_html=True)
        with e3:
            st.markdown(f"""<div class="eco-card tree">
                <div class="eco-icon">🌳</div>
                <div class="eco-label">Equivalent trees planted</div>
                <div class="eco-value">{trees_equivalent:,.1f}<span class="eco-unit">trees</span></div>
            </div>""", unsafe_allow_html=True)


render_dashboard_content(selected_date)