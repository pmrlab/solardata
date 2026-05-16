import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Solar Power Dashboard", layout="wide")

# =====================================================
# AUTO REFRESH (10 MIN)
# =====================================================
st.markdown(
    "<meta http-equiv='refresh' content='600'>",
    unsafe_allow_html=True
)

# =====================================================
# TITLE
# =====================================================
st.title("☀️ Solar Power Plant Monitoring Dashboard")
st.caption(f"🔄 Last refreshed at: {pd.Timestamp.now().strftime('%H:%M:%S')}")

# =====================================================
# DATE SELECTION
# =====================================================
selected_date = st.date_input(
    "📅 Select Date",
    value=pd.Timestamp.now().date(),
    max_value=pd.Timestamp.now().date()
)

# =====================================================
# PATHS
# =====================================================
BASE_DIR = "isolar_data"

PLANTS = {
    "Electronic 1": os.path.join(BASE_DIR, "Electronic 1", "*"),
    "Electronic 2": os.path.join(BASE_DIR, "Electronic 2", "*"),
    "MIIC-1": os.path.join(BASE_DIR, "miic1", "*"),
    "MIIC-2": os.path.join(BASE_DIR, "miic2", "*"),
    "Multipath 1": os.path.join(BASE_DIR, "Multipath 1", "*"),
    "Multipath 2": os.path.join(BASE_DIR, "Multipath 2", "*"),
    "Multipath 3": os.path.join(BASE_DIR, "Multipath 3", "*"),
    "Multipath 4": os.path.join(BASE_DIR, "Multipath 4", "*"),
    "Multipath 5": os.path.join(BASE_DIR, "Multipath 5", "*"),
}

# =====================================================
# LOAD FILE BY DATE
# =====================================================
def load_file_by_date(path, label):
    files = sorted(glob.glob(path))

    if not files:
        st.warning(f"No files found for {label}")
        return None

    date_str = selected_date.strftime("%Y%m%d")

    matching_files = [
        f for f in files if date_str in os.path.basename(f)
    ]

    if not matching_files:
        st.warning(f"No data for {label} on {selected_date}")
        return None

    file = matching_files[-1]

    try:
        return pd.read_excel(file)
    except:
        try:
            return pd.read_csv(file)
        except:
            st.warning(f"Unable to read {label}")
            return None

# =====================================================
# NORMALIZE
# =====================================================
def normalize_df(df):
    df.columns = [str(c).strip().lower() for c in df.columns]

    time_col = next(c for c in df.columns if "time" in c)
    dc_col   = next(c for c in df.columns if "dc" in c)
    ac_col   = next(c for c in df.columns if "active" in c or "ac" in c)

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    df = df.sort_values(time_col)

    return df, time_col, dc_col, ac_col

# =====================================================
# PLOT
# =====================================================
def plot_curve(df, t, dc, ac, label):

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[t],
        y=df[dc],
        name="Total DC Power",
        mode="lines",
        line=dict(color="#FF8A00", width=2),
        fill="tozeroy",
        fillcolor="rgba(255,138,0,0.35)",
    ))

    fig.add_trace(go.Scatter(
        x=df[t],
        y=df[ac],
        name="Total active power",
        mode="lines",
        line=dict(color="#2F7BFF", width=3),
    ))

    fig.update_layout(
        height=400,
        title=f"{label} Power Curve",
        hovermode="x unified",
        xaxis_title="Time",
        yaxis_title="Power (kW)",
    )

    return fig

# =====================================================
# DISPLAY ALL PLANTS (2 PER ROW)
# =====================================================
plant_items = list(PLANTS.items())

for i in range(0, len(plant_items), 2):

    col1, col2 = st.columns(2)

    for col, plant in zip([col1, col2], plant_items[i:i+2]):

        plant_name, plant_path = plant

        with col:
            st.subheader(f"🔹 {plant_name}")

            df = load_file_by_date(plant_path, plant_name)

            if df is not None:
                df, t, dc, ac = normalize_df(df)
                st.plotly_chart(
                    plot_curve(df, t, dc, ac, plant_name),
                    use_container_width=True
                )
