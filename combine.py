import os
import glob
import json
import csv
import numpy as np
import pandas as pd
import streamlit as st

import streamlit.components.v1 as components
import base64
import threading
from ev_module import get_ev_html
from energy_map_module import get_energy_map_html

# ── STARTUP PRE-LOADER ──────────────────────────────────────────

# =====================================================
# PAGE CONFIGURATION & FULLSCREEN 
# =====================================================
st.set_page_config(
    layout="wide",
    page_title="SolarVeda — PMR Lab, MNIT Jaipur",
    page_icon="☀️",
    initial_sidebar_state="collapsed"
)
import shutil, os
os.makedirs("static", exist_ok=True)

# Hide Streamlit's default UI elements and make the HTML component take the entire screen
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding: 0 !important; margin: 0 !important; max-width: 100% !important;}
iframe {
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    border: none; z-index: 999999;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# EMISSION & CALCULATION CONSTANTS
# =====================================================
_trapezoid = getattr(np, "trapezoid", None) or getattr(np, "trapz", None)

CO2_PER_KWH   = 0.997
COAL_PER_KWH  = 0.404
TREES_PER_KWH = 0.054
COMMON_FREQ   = "15min"

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
    "VLTC 1":       os.path.join(BASE_DIR, "VLTC 1", "*"),
    "VLTC 2":       os.path.join(BASE_DIR, "VLTC 2", "*"),
    "VLTC 3":       os.path.join(BASE_DIR, "VLTC 3", "*"),
}

HAVELLS_BASE   = "havells_data"
HAVELLS_PLANTS = {
    "Computer Deptt":      os.path.join(HAVELLS_BASE, "computer_dept",  "*"),
    "Prabha Bhawan Inv 1": os.path.join(HAVELLS_BASE, "prabha_1",       "*"),
    "Prabha Bhawan Inv 2": os.path.join(HAVELLS_BASE, "prabha_2",       "*"),
    "Prabha Bhawan Inv 3": os.path.join(HAVELLS_BASE, "prabha_3",       "*"),
    "Electrical Deptt":    os.path.join(HAVELLS_BASE, "electrical",     "*"),
    "Metallurgical Dep.":  os.path.join(HAVELLS_BASE, "metallurgical",  "*"),
}

PLANT_CAPACITIES = {
    "Electronic 1": 15.0, "Electronic 2": 20.0, "MIIC-1": 30.0, "MIIC-2": 30.0,
    "Multipath 1": 15.0, "Multipath 2": 15.0, "Multipath 3": 15.0, "Multipath 4": 15.0, "Multipath 5": 15.0,
    "Prabha 01": 25.0, "Prabha 02": 25.0, "VLTC 1": 10.0, "VLTC 2": 10.0, "VLTC 3": 9.0,
    "Computer Deptt": 12.0, "Prabha Bhawan Inv 1": 15.0, "Prabha Bhawan Inv 2": 15.0, 
    "Prabha Bhawan Inv 3": 20.0, "Electrical Deptt": 8.0, "Metallurgical Dep.": 5.0
}

# =====================================================
# EWATCH FILE PATHS
# =====================================================
EWATCH_BASE = "ewatch_data"
# TEMPORARY DEBUG — remove after fixing



EWATCH_FILES = {
    "cg_daily":    os.path.join(EWATCH_BASE, "cons_gen_daily_*"),
    "cg_inst":     os.path.join(EWATCH_BASE, "cons_gen_saving_interval_institutional_*"),
    "cg_res":      os.path.join(EWATCH_BASE, "cons_gen_saving_interval_residential_*"),
    "dem_daily":   os.path.join(EWATCH_BASE, "max_demand_daily_*"),
    "dem_inst":    os.path.join(EWATCH_BASE, "max_demand_saving_interval_institutional_*"),
    "dem_res":     os.path.join(EWATCH_BASE, "max_demand_saving_interval_residential_*"),
    "meter_cg":    os.path.join(EWATCH_BASE, "meter_export_cons_gen_*"),
    "meter_lo":    os.path.join(EWATCH_BASE, "meter_export_load_off_*"),
    "meter_read":  os.path.join(EWATCH_BASE, "meter_export_reading_*"),
    "tva_daily":   os.path.join(EWATCH_BASE, "target_vs_actual_daily_*"),
    "tva_hourly":  os.path.join(EWATCH_BASE, "target_vs_actual_hourly_*"),
    "tva_monthly": os.path.join(EWATCH_BASE, "target_vs_actual_monthly_*"),
}
# TEMPORARY DIAGNOSTIC
# =====================================================
# =====================================================
# EWATCH PARSERS
# =====================================================

def _to_float(x):
    if x is None or (isinstance(x, float) and x != x):
        return 0.0
    try:
        return float(str(x).replace(',', '').strip())
    except (ValueError, TypeError):
        return 0.0

def _latest_file(path_pattern):
    files = [f for f in glob.glob(path_pattern)
             if f.endswith(('.xls', '.xlsx', '.csv'))]
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def _read_xls_or_xlsx(path):
    if path is None:
        return pd.DataFrame()
    try:
        if path.endswith('.xls'):
            return pd.read_excel(path, header=None, engine='xlrd')
        else:
            return pd.read_excel(path, header=None, engine='openpyxl')
    except Exception:
        return pd.DataFrame()

def parse_cg_daily(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[1] < 5:
        return 0.0, 0.0
    inst_val, res_val = 0.0, 0.0
    for _, row in df.iterrows():
        name = str(row.iloc[1]).upper().strip()
        val  = _to_float(row.iloc[4])
        if name == 'INSTITUTIONAL AREA' and val > 0:
            inst_val = val
        elif name == 'RESIDENTIAL AREA' and val > 0:
            res_val = val
    return inst_val, res_val

def parse_cg_interval(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[0] < 4:
        return "[]", "[]"
    times, vals = [], []
    for i in range(2, len(df) - 2):
        row = df.iloc[i]
        t_raw = str(row.iloc[1]).strip()
        v_raw = row.iloc[2]
        if '-' not in t_raw:
            continue
        t_label = t_raw.split('-')[-1].strip()
        val = _to_float(v_raw)
        if t_label and val >= 0:
            times.append(t_label)
            vals.append(round(val, 2))
    return json.dumps(times), json.dumps(vals)

def parse_dem_daily(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[1] < 5:
        return 0.0, 0.0
    inst_val, res_val = 0.0, 0.0
    for _, row in df.iterrows():
        name = str(row.iloc[1]).upper().strip()
        val  = _to_float(row.iloc[4])
        if name == 'INSTITUTIONAL AREA' and val > 0:
            inst_val = val
        elif name == 'RESIDENTIAL AREA' and val > 0:
            res_val = val
    return inst_val, res_val

def parse_dem_interval(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[0] < 4:
        return "[]", "[]"
    times, vals = [], []
    for i in range(2, len(df) - 2):
        row = df.iloc[i]
        t_raw = str(row.iloc[1]).strip()
        v_raw = row.iloc[2]
        if '-' not in t_raw:
            continue
        t_label = t_raw.split('-')[-1].strip()
        val = _to_float(v_raw)
        if t_label and val >= 0:
            times.append(t_label)
            vals.append(round(val, 2))
    return json.dumps(times), json.dumps(vals)

def parse_meter_cg_or_reading(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[0] < 3:
        return "[]", "[]", "[]"
    dates, inst_vals, res_vals = [], [], []
    for i in range(2, len(df)):
        row = df.iloc[i]
        d_raw = str(row.iloc[0]).strip()
        if not d_raw or 'total' in d_raw.lower() or d_raw.lower() == 'nan':
            continue
        if not any(c.isdigit() for c in d_raw):
            continue
        try:
            d_label = pd.Timestamp(d_raw).strftime('%d/%m/%Y')
        except Exception:
            d_label = d_raw.split(' ')[0]
        dates.append(d_label)
        inst_vals.append(round(_to_float(row.iloc[1]), 1))
        res_vals.append(round(_to_float(row.iloc[2]), 1))
    return json.dumps(dates), json.dumps(inst_vals), json.dumps(res_vals)

def parse_meter_load_off(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[0] < 3:
        return "[]", "[]", "[]"
    dates, inst_vals, res_vals = [], [], []
    for i in range(2, len(df)):
        row = df.iloc[i]
        d_raw = str(row.iloc[0]).strip()
        if not d_raw or 'total' in d_raw.lower() or d_raw.lower() == 'nan':
            continue
        if not any(c.isdigit() for c in d_raw):
            continue
        try:
            d_label = pd.Timestamp(d_raw).strftime('%d/%m/%Y')
        except Exception:
            d_label = d_raw.split(' ')[0]
        inst = _to_float(row.iloc[1]) if df.shape[1] > 1 else 0.0
        res  = _to_float(row.iloc[2]) if df.shape[1] > 2 else 0.0
        dates.append(d_label)
        inst_vals.append(round(inst, 1))
        res_vals.append(round(res, 1))
    return json.dumps(dates), json.dumps(inst_vals), json.dumps(res_vals)

def parse_tva(path_pattern):
    df = _read_xls_or_xlsx(_latest_file(path_pattern))
    if df.empty or df.shape[0] < 3 or df.shape[1] < 5:
        return "[]", "[]", "[]", "[]", "[]"
    data_rows = []
    for i in range(2, len(df)):
        row = df.iloc[i]
        d_str = str(row.iloc[0]).strip()
        if d_str in ('', 'nan') or not any(c.isdigit() for c in d_str):
            continue
        data_rows.append((row, row.iloc[0]))
    is_interval = len(data_rows) > 5
    times, i_tgt, i_act, r_tgt, r_act = [], [], [], [], []
    for row, d_raw in data_rows:
        try:
            ts = pd.Timestamp(d_raw)
            if is_interval:
                t_label = ts.strftime('%H:%M')
            elif len(data_rows) > 1:
                t_label = ts.strftime('%b %Y')
            else:
                t_label = ts.strftime('%d/%m/%Y')
        except Exception:
            t_label = str(d_raw).strip().split(' ')[0]
        times.append(t_label)
        i_tgt.append(round(_to_float(row.iloc[1]), 1))
        i_act.append(round(_to_float(row.iloc[2]), 1))
        r_tgt.append(round(_to_float(row.iloc[3]), 1))
        r_act.append(round(_to_float(row.iloc[4]), 1))
    return (json.dumps(times),
            json.dumps(i_tgt), json.dumps(i_act),
            json.dumps(r_tgt), json.dumps(r_act))
# =====================================================
# ORIGINAL SOLAR DATA FETCHING
# =====================================================

def load_file_by_date_solar(path, target_date_str=None):
    files = sorted(glob.glob(path))
    valid_files = [f for f in files if f.endswith(('.csv', '.xlsx', '.xls'))]
    if not valid_files: return None
    
    if target_date_str:
        target_date = pd.Timestamp(target_date_str)
        date_str1 = target_date.strftime("%Y%m%d")
        date_str2 = target_date.strftime("%Y-%m-%d")
        matching = [f for f in valid_files if date_str1 in os.path.basename(f) or date_str2 in os.path.basename(f)]
        target_file = matching[-1] if matching else max(valid_files, key=os.path.getmtime)
    else:
        target_file = max(valid_files, key=os.path.getmtime)
    
    try: 
        return pd.read_excel(target_file)
    except Exception:
        try: 
            return pd.read_csv(target_file, on_bad_lines='skip')
        except Exception:
            return None

def normalize(df, target_date_str=None):
    if df is None or df.empty: return None, None, None, None
    df = df.copy()
    cols = [str(c).strip().lower() for c in df.columns]

    # 1. Bypass potential metadata rows at the top of the file
    if not any("time" in c for c in cols):
        for i in range(min(15, len(df))):
            row_vals = [str(x).lower() for x in df.iloc[i].values]
            if any("time" in x for x in row_vals):
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break

    df.columns = [str(c).strip().lower() for c in df.columns]

    # 2. Identify Time column
    t_col = next((c for c in df.columns if "time" in c), None)
    if not t_col: return None, None, None, None

    # 3. Specifically target "Total DC power" exactly like the iSolar website
    dc_col = next((c for c in df.columns if "total dc power" in c), None)
    if not dc_col: dc_col = next((c for c in df.columns if "dc power" in c), None)
    if not dc_col:
        dc_cands = [c for c in df.columns if "dc" in c]
        dc_col = dc_cands[0] if dc_cands else None

    # 4. Specifically target "Total active power" exactly like the iSolar website
    ac_col = next((c for c in df.columns if "total active power" in c), None)
    if not ac_col: ac_col = next((c for c in df.columns if "active" in c), None)
    if not ac_col: ac_col = next((c for c in df.columns if "ac " in c or "ac_" in c), None)
    if not ac_col:
        ac_cands = [c for c in df.columns if "ac" in c]
        ac_col = ac_cands[0] if ac_cands else None

    if not (dc_col and ac_col): return None, None, None, None

    df = df[~df[t_col].astype(str).str.contains("time|Time", case=False, na=False)].copy()

    # Assign standard internal names
    df["_time"] = pd.to_datetime(df[t_col], errors="coerce")
    df["_dc"] = pd.to_numeric(df[dc_col].astype(str).str.replace(',',''), errors="coerce").fillna(0)
    df["_ac"] = pd.to_numeric(df[ac_col].astype(str).str.replace(',',''), errors="coerce").fillna(0)

    # 5. Automatically convert Watts to kW if the column header indicates (W)
    if "(w)" in dc_col or "[w]" in dc_col:
        df["_dc"] = df["_dc"] / 1000.0
    if "(w)" in ac_col or "[w]" in ac_col:
        df["_ac"] = df["_ac"] / 1000.0

    df = df.dropna(subset=["_time"])
    df["_time"] = df["_time"].dt.tz_localize(None)

    if target_date_str:
        start_date = pd.Timestamp(target_date_str)
        end_date = start_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["_time"] >= start_date) & (df["_time"] <= end_date)]

    df = df.sort_values("_time")
    return (None, None, None, None) if df.empty else (df, "_time", "_dc", "_ac")

def normalize_havells(df, target_date_str=None):
    if df is None or df.empty: return None, None, None, None
    df = df.copy()
    cols = [str(c).strip().lower() for c in df.columns]
    if not any("time" in c for c in cols):
        for i in range(min(15, len(df))):
            row_vals = [str(x).lower() for x in df.iloc[i].values]
            if any("time" in x for x in row_vals):
                df.columns = df.iloc[i]
                df = df.iloc[i+1:].reset_index(drop=True)
                break
                
    t_col = next((c for c in df.columns if "time" in str(c).lower()), None)
    if not t_col: return None, None, None, None

    df = df[~df[t_col].astype(str).str.contains("time|Time", case=False, na=False)].copy()

    df["_time"] = pd.to_datetime(df[t_col], errors="coerce")
    df["_time"] = df["_time"].dt.tz_localize(None)
    
    dc_cols = [c for c in df.columns if str(c).startswith("DC Power PV") and str(c).endswith("(W)")]
    if dc_cols:
        for c in dc_cols:
            df[c] = df[c].astype(str).str.replace(',', '')
    df["_dc_kw"] = (df[dc_cols].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1) / 1000.0 if dc_cols else 0.0)
    
    ac_src = "Total AC Output Power (Active)(W)"
    if ac_src not in df.columns:
        ac_cols = [c for c in df.columns if "ac output power" in str(c).lower() or "active" in str(c).lower()]
        if ac_cols: ac_src = ac_cols[0]
        else: return None, None, None, None
            
    df["_ac_kw"] = pd.to_numeric(df[ac_src].astype(str).str.replace(',', ''), errors="coerce").fillna(0) / 1000.0
    df = df.dropna(subset=["_time"])
    
    if target_date_str:
        start_date = pd.Timestamp(target_date_str)
        end_date = start_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["_time"] >= start_date) & (df["_time"] <= end_date)]
        
    df = df.sort_values("_time")
    return (None, None, None, None) if df.empty else (df, "_time", "_dc_kw", "_ac_kw")

def compute_daily_energy_kwh(df, t, dc):
    if df is None or len(df) < 2: return 0.0
    times_h = (df[t] - df[t].iloc[0]).dt.total_seconds().values / 3600.0
    return max(float(_trapezoid(df[dc].values, x=times_h)), 0.0)

def resample_to_grid(df_raw, time_col="time", freq=COMMON_FREQ):
    df = df_raw.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.set_index(time_col).sort_index()
    df = df.resample(freq).mean(numeric_only=True)
    return df.ffill(limit=2).fillna(0).reset_index()

def aggregate_plants_iso(target_date_str):
    valid_data = {}
    device_frames = []
    daily_energy = 0.0
    for name, path in PLANTS.items():
        raw = load_file_by_date_solar(path, target_date_str)
        if raw is None: continue
        df, t, dc, ac = normalize(raw, target_date_str) 
        if df is None: continue
        valid_data[name] = (df, t, dc, ac)
        daily_energy += compute_daily_energy_kwh(df, t, dc)
        frame = pd.DataFrame({"time": df[t], "dc": df[dc], "ac": df[ac]})
        device_frames.append(resample_to_grid(frame, "time"))
    
    df_agg = None
    if device_frames:
        df_agg = pd.concat(device_frames).groupby("time").sum().reset_index().sort_values("time")
        df_agg = df_agg[(df_agg["dc"] + df_agg["ac"]) > 0.01]
    return df_agg, valid_data, daily_energy

def aggregate_plants_hav(target_date_str):
    valid_data = {}
    device_frames = []
    daily_energy = 0.0
    for name, path in HAVELLS_PLANTS.items():
        raw = load_file_by_date_solar(path, target_date_str)
        if raw is None: continue
        df, t, dc, ac = normalize_havells(raw, target_date_str) 
        if df is None: continue
        valid_data[name] = (df, t, dc, ac)
        daily_energy += compute_daily_energy_kwh(df, t, dc)
        frame = pd.DataFrame({"time": df[t], "dc": df[dc], "ac": df[ac]})
        device_frames.append(resample_to_grid(frame, "time"))
    
    df_agg = None
    if device_frames:
        df_agg = pd.concat(device_frames).groupby("time").sum().reset_index().sort_values("time")
        df_agg = df_agg[(df_agg["dc"] + df_agg["ac"]) > 0.01]
    return df_agg, valid_data, daily_energy

def get_historical_aggregation(plant_dict, norm_fn):
    monthly_totals = {}
    yearly_totals = {}
    for name, path in plant_dict.items():
        all_files = [f for f in glob.glob(path) if f.endswith(('.csv','.xlsx','.xls'))]
        for file in all_files:
            try:
                if file.endswith('.csv'): raw = pd.read_csv(file)
                else: raw = pd.read_excel(file)
                df, t, dc, ac = norm_fn(raw, target_date_str=None)
                if df is not None and not df.empty:
                    df['_month'] = df[t].dt.strftime("%b %Y")
                    df['_year'] = df[t].dt.strftime("%Y")
                    for m, grp in df.groupby('_month'):
                        monthly_totals[m] = monthly_totals.get(m, 0) + compute_daily_energy_kwh(grp, t, dc)
                    for y, grp in df.groupby('_year'):
                        yearly_totals[y] = yearly_totals.get(y, 0) + compute_daily_energy_kwh(grp, t, dc)
            except Exception:
                continue
    return monthly_totals, yearly_totals

@st.cache_data(ttl=86400)
def cached_historical_iso():
    return get_historical_aggregation(PLANTS, normalize)

@st.cache_data(ttl=86400)
def cached_historical_hav():
    return get_historical_aggregation(HAVELLS_PLANTS, normalize_havells)


@st.cache_data(ttl=86400)
def get_combined_historical():
    iso_m, iso_y = cached_historical_iso()
    hav_m, hav_y = cached_historical_hav()
    total_m = {k: iso_m.get(k,0) + hav_m.get(k,0) for k in set(iso_m)|set(hav_m)}
    total_y = {k: iso_y.get(k,0) + hav_y.get(k,0) for k in set(iso_y)|set(hav_y)}
    return total_m, total_y

# Use empty dicts for now — filled only when needed
total_monthly, total_yearly = {}, {}

current_date = pd.Timestamp.now().date()
current_date_str = current_date.strftime("%Y-%m-%d")
display_date_str = current_date.strftime('%d %b %Y')
yesterday_date = current_date - pd.Timedelta(days=1)
display_yesterday_str = yesterday_date.strftime('%d %b %Y')

@st.cache_data(ttl=900)
def cached_aggregate_iso(date_str):
    return aggregate_plants_iso(date_str)

@st.cache_data(ttl=900)
def cached_aggregate_hav(date_str):
    return aggregate_plants_hav(date_str)

@st.cache_data(ttl=900)
def cached_tables(date_str):
    _, iso_valid, _ = cached_aggregate_iso(date_str)
    _, hav_valid, _ = cached_aggregate_hav(date_str)
    return generate_table(iso_valid), generate_table(hav_valid)

@st.cache_data(ttl=900)
def load_all_ewatch():
    base = EWATCH_BASE
    cg_inst, cg_res = parse_cg_daily(os.path.join(base, "cons_gen_daily*"))
    return {
        "cg_daily":  json.dumps([cg_inst, cg_res]),
        "cg_inst_t": parse_cg_interval(os.path.join(base, "cons_gen_saving_interval_institutional*")),
        "cg_res_t":  parse_cg_interval(os.path.join(base, "cons_gen_saving_interval_residential*")),
        "dem_daily": parse_dem_daily(os.path.join(base, "max_demand_daily*")),
        "dem_inst":  parse_dem_interval(os.path.join(base, "max_demand_saving_interval_institutional*")),
        "dem_res":   parse_dem_interval(os.path.join(base, "max_demand_saving_interval_residential*")),
        "m_cg":      parse_meter_cg_or_reading(os.path.join(base, "meter_export_cons_gen*")),
        "m_lo":      parse_meter_load_off(os.path.join(base, "meter_export_load_off*")),
        "m_rd":      parse_meter_cg_or_reading(os.path.join(base, "meter_export_reading*")),
        "tva_d":     parse_tva(os.path.join(base, "target_vs_actual_daily*")),
        "tva_h":     parse_tva(os.path.join(base, "target_vs_actual_hourly*")),
        "tva_m":     parse_tva(os.path.join(base, "target_vs_actual_monthly*")),
    }
@st.cache_data(ttl=3600)
def get_weekly_data(today_str):
    weekly_iso, weekly_hav, weekly_dates = [], [], []
    today = pd.Timestamp(today_str).date()
    for i in range(6, -1, -1):
        d = today - pd.Timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        weekly_dates.append(d.strftime("%a"))
        _, _, d_iso = cached_aggregate_iso(d_str)
        _, _, d_hav = cached_aggregate_hav(d_str)
        weekly_iso.append(round(d_iso, 1))
        weekly_hav.append(round(d_hav, 1))
    return weekly_iso, weekly_hav, weekly_dates

# ── BACKGROUND PRELOADER (fires once on server start) ───────────
if 'preload_fired' not in st.session_state:
    st.session_state['preload_fired'] = True
    def _preload():
        try:
            with concurrent.futures.ThreadPoolExecutor() as ex:
                ex.submit(cached_aggregate_iso, current_date_str)
                ex.submit(cached_aggregate_hav, current_date_str)
                ex.submit(load_all_ewatch)
                ex.submit(get_weekly_data, current_date_str)
        except Exception:
            pass
    threading.Thread(target=_preload, daemon=True).start()

# ── PARALLEL DATA LOADING (all 4 sources at same time) ──────────
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor() as ex:
    fut_iso = ex.submit(cached_aggregate_iso, current_date_str)
    fut_hav = ex.submit(cached_aggregate_hav, current_date_str)
    fut_ew  = ex.submit(load_all_ewatch)
    fut_wk  = ex.submit(get_weekly_data, current_date_str)
    df_iso, valid_iso, iso_kwh = fut_iso.result()
    df_hav, valid_hav, hav_kwh = fut_hav.result()
    ew = fut_ew.result()
    weekly_iso_data, weekly_hav_data, weekly_dates = fut_wk.result()



tot_kwh = iso_kwh + hav_kwh

iso_pk_dc = df_iso["dc"].max() if (df_iso is not None and not df_iso.empty) else 0
iso_pk_ac = df_iso["ac"].max() if (df_iso is not None and not df_iso.empty) else 0
hav_pk_dc = df_hav["dc"].max() if (df_hav is not None and not df_hav.empty) else 0
hav_pk_ac = df_hav["ac"].max() if (df_hav is not None and not df_hav.empty) else 0

parts = []
if df_iso is not None and not df_iso.empty: parts.append(df_iso[["time","dc","ac"]].copy())
if df_hav is not None and not df_hav.empty: parts.append(df_hav[["time","dc","ac"]].copy())
df_total = None
if parts:
    df_total = pd.concat(parts).groupby("time").sum().reset_index().sort_values("time")
tot_pk_ac = df_total["ac"].max() if (df_total is not None and not df_total.empty) else 0

js_hours, js_iso_dc, js_iso_ac, js_hav_dc, js_hav_ac, js_tot_ac = "[]", "[]", "[]", "[]", "[]", "[]"
if df_total is not None and not df_total.empty:
    js_hours = json.dumps(df_total["time"].dt.strftime("%H:%M").tolist())
    df_merged = df_total[['time', 'ac']].rename(columns={'ac': 'tot_ac'})
    if df_iso is not None and not df_iso.empty:
        df_merged = pd.merge(df_merged, df_iso[['time','dc','ac']].rename(columns={'dc':'iso_dc', 'ac':'iso_ac'}), on='time', how='left')
    else: df_merged['iso_dc'], df_merged['iso_ac'] = 0, 0
    if df_hav is not None and not df_hav.empty:
        df_merged = pd.merge(df_merged, df_hav[['time','dc','ac']].rename(columns={'dc':'hav_dc', 'ac':'hav_ac'}), on='time', how='left')
    else: df_merged['hav_dc'], df_merged['hav_ac'] = 0, 0
        
    df_merged = df_merged.fillna(0)
    js_iso_dc = json.dumps(df_merged['iso_dc'].round(2).tolist())
    js_iso_ac = json.dumps(df_merged['iso_ac'].round(2).tolist())
    js_hav_dc = json.dumps(df_merged['hav_dc'].round(2).tolist())
    js_hav_ac = json.dumps(df_merged['hav_ac'].round(2).tolist())
    js_tot_ac = json.dumps(df_merged['tot_ac'].round(2).tolist())

js_iso_names, js_iso_kwh = [], []
if valid_iso:
    for name, (df, t, dc, ac) in valid_iso.items():
        js_iso_names.append(name)
        js_iso_kwh.append(compute_daily_energy_kwh(df, t, dc))

js_hav_names, js_hav_kwh = [], []
if valid_hav:
    for name, (df, t, dc, ac) in valid_hav.items():
        js_hav_names.append(name)
        js_hav_kwh.append(compute_daily_energy_kwh(df, t, dc))


def _latest_nonzero(series):
    nonz = series[series > 0]
    return float(nonz.iloc[-1]) if not nonz.empty else 0.0

js_iso_plant_dc = json.dumps([_latest_nonzero(v[0][v[2]]) for v in valid_iso.values()]) if valid_iso else "[]"
js_iso_plant_ac = json.dumps([_latest_nonzero(v[0][v[3]]) for v in valid_iso.values()]) if valid_iso else "[]"
js_hav_plant_dc = json.dumps([_latest_nonzero(v[0][v[2]]) for v in valid_hav.values()]) if valid_hav else "[]"
js_hav_plant_ac = json.dumps([_latest_nonzero(v[0][v[3]]) for v in valid_hav.values()]) if valid_hav else "[]"

def generate_table(valid_data_dict):
    rows = ""
    # Get the current time to check against your 9 AM checkpoint
    now_naive = pd.Timestamp.now().tz_localize(None) 
    
    if valid_data_dict:
        for name, (df, t, dc, ac) in valid_data_dict.items():
            # Get the last non-zero value for the table
            dc_nonz = df[dc][df[dc] > 0]
            ac_nonz = df[ac][df[ac] > 0]
            c_dc = float(dc_nonz.iloc[-1]) if not dc_nonz.empty else 0.0
            c_ac = float(ac_nonz.iloc[-1]) if not ac_nonz.empty else 0.0
            
            today_kwh = compute_daily_energy_kwh(df, t, dc)
            cap = PLANT_CAPACITIES.get(name, 10.0)
            
            # --- NEW CHECKPOINT LOGIC ---
            # 1. By default, assume every machine is Online
            is_offline = False
            
            # 2. Checkpoint: If it is 9:00 AM or later...
            if now_naive.hour >= 9:
                # ...and it has generated absolutely zero power all day
                if today_kwh == 0.0 and c_dc == 0.0:
                    is_offline = True
            # ----------------------------
            
            status_html = "<span style='color:#F97316; font-weight:bold;'>Offline</span>" if is_offline else "<span style='color:#10B981; font-weight:bold;'>Online</span>"
            
            eff = (c_ac / c_dc * 100) if c_dc > 0 else 0
            plf = (today_kwh / (cap * 24) * 100) if cap > 0 else 0
            
            rows += f"<tr><td>{name}</td><td>{cap} kW</td><td>{c_dc:.1f} kW</td><td>{c_ac:.1f} kW</td><td>{eff:.1f}%</td><td>{today_kwh:.1f}</td><td>{plf:.1f}%</td><td>{status_html}</td></tr>"
    else:
        rows = "<tr><td colspan='8'>No data available for today.</td></tr>"
    return rows

iso_table_rows, hav_table_rows = cached_tables(current_date_str)

def generate_indiv_charts(valid_data_dict, prefix):
    html = '<div class="fourcol">'
    js_data = {}
    for name, (df, t, dc, ac) in valid_data_dict.items():
        cid = f"c-{prefix}-{name.replace(' ', '').replace('-', '').replace('.', '')}"
        html += f'<div class="cw" style="padding:16px; margin-bottom:0;"><div class="ch" style="margin-bottom:8px;"><div><div class="ct" style="font-size:14px;">{name}</div></div></div><div style="position: relative; height:180px; width:100%;"><canvas id="{cid}"></canvas></div></div>'
        df_res = resample_to_grid(pd.DataFrame({"time": df[t], "dc": df[dc], "ac": df[ac]}), "time")
        js_data[cid] = {"dc": df_res["dc"].round(2).tolist(), "ac": df_res["ac"].round(2).tolist()}
    html += '</div>'
    return html, js_data

@st.cache_data(ttl=900)
def cached_indiv_iso(date_str):
    _, valid, _ = cached_aggregate_iso(date_str)
    return generate_indiv_charts(valid, "iso")

@st.cache_data(ttl=900)
def cached_indiv_hav(date_str):
    _, valid, _ = cached_aggregate_hav(date_str)
    return generate_indiv_charts(valid, "hav")

iso_indiv_html, js_iso_indiv_data = cached_indiv_iso(current_date_str)
hav_indiv_html, js_hav_indiv_data = cached_indiv_hav(current_date_str)


weekly_iso_data, weekly_hav_data, weekly_dates = get_weekly_data(current_date_str)

# --- NEW FULLY ISOLATED EWATCH CALLS ---

# 1. Cons / Gen
# ─── eWatch Parsers (new, format-specific) ───────────────────────

# 1. Cons / Gen
# 1. Cons / Gen
# ─── eWatch Calls ───────────────────────────────────────────────
ew = load_all_ewatch()
ew_cg_daily = ew["cg_daily"]
ew_cg_inst_t, ew_cg_inst_v = ew["cg_inst_t"]
ew_cg_res_t,  ew_cg_res_v  = ew["cg_res_t"]
ew_dem_daily_inst, ew_dem_daily_res = ew["dem_daily"]
ew_dem_daily = json.dumps([ew_dem_daily_inst, ew_dem_daily_res])
ew_dem_inst_t, ew_dem_inst_v = ew["dem_inst"]
ew_dem_res_t,  ew_dem_res_v  = ew["dem_res"]
m_cg_t, m_cg_i, m_cg_r = ew["m_cg"]
m_lo_t, m_lo_i, m_lo_r = ew["m_lo"]
m_rd_t, m_rd_i, m_rd_r = ew["m_rd"]
tva_d_t, tva_d_it, tva_d_ia, tva_d_rt, tva_d_ra = ew["tva_d"]
tva_h_t, tva_h_it, tva_h_ia, tva_h_rt, tva_h_ra = ew["tva_h"]
tva_m_t, tva_m_it, tva_m_ia, tva_m_rt, tva_m_ra = ew["tva_m"]
ev_section_html = get_ev_html()
energy_map_html = get_energy_map_html()

# =====================================================
# MASTER HTML TEMPLATE
# =====================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SolarVeda — PMR Lab, MNIT Jaipur</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {
  --sun:#0d9488; --sun-l:#14b8a6; --sun-p:#f0fdfa;
  --leaf:#22C55E; --sky:#0EA5E9; --sky2:#0369A1;
  --dark:#111827; --mid:#1F2937; --slate:#374151;
  --muted:#6B7280; --pale:#9CA3AF;
  --border:#E5E7EB; --bg:#F9FAFB; --white:#FFFFFF;
  --r:16px; --hh:90px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;font-size:16px}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--dark);overflow-x:hidden}

/* ══ HEADER ══ */
#hdr {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000; height: var(--hh);
  background: rgba(255, 255, 255, 0.20) !important; 
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px;
  box-shadow: 0 4px 24px rgba(13,148,136,.10), 0 1px 6px rgba(0,0,0,.04);
  transition: transform .4s cubic-bezier(.4,0,.2,1);
}
#hdr.hide{transform:translateY(-100%)}

/* left logo block */
.hdr-left{display:flex;align-items:center;gap:14px;flex:0 0 auto;min-width:160px}
.logo-box{
  width:72px;height:72px;border-radius:14px;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
.logo-box img{width:100%;height:100%;object-fit:contain}
.logo-box .fb{font-size:9px;font-weight:800;color:#fff;text-align:center;line-height:1.4;padding:4px}

/* centre brand */
.hdr-centre{flex:1;text-align:center;padding:0 20px;position:relative}
.brand-wrap{display:inline-flex;flex-direction:column;align-items:center;gap:0}
.brand-sun-ring{
  position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:200px;height:200px;border-radius:50%;
  background:radial-gradient(circle,rgba(13,148,136,.06) 0%,transparent 70%);
  pointer-events:none
}
.brand-name{
  font-family:'Syne',sans-serif;font-size:32px;font-weight:900;
  color:var(--white);letter-spacing:-0.5px;line-height:1;position:relative
}
.brand-name span{color:#FBBF24;}
.brand-name .sun-icon {
  display: inline-block;
  font-size: 26px; /* Size of the sun emoji */
  line-height: 1;
  margin-left: 6px;
  vertical-align: middle;
  background: none; /* Removes the green circle */
  box-shadow: none; /* Removes the green glow */
  animation: spin-slow 10s linear infinite; /* Controls the rotation speed */
}
@keyframes spin-slow{to{transform:rotate(360deg)}}
.brand-tagline{font-size:10.5px;font-weight:600;color:var(--white);letter-spacing:.4px;margin-top:2px}
.brand-dept{font-size:9px;font-weight:700;color:var(--white);letter-spacing:1.5px;text-transform:uppercase;margin-top:1px
}

/* right logo block */
.hdr-right{display:flex;align-items:center;gap:12px;flex:0 0 auto;min-width:160px;justify-content:flex-end}
.hefa-box{
  height:40px;background:#fff;border:1.5px solid var(--border);
  border-radius:12px;padding:4px 4px;display:flex;align-items:center;justify-content:center;
  min-width:90px;box-shadow:0 2px 8px rgba(0,0,0,.05)
}
.hefa-box img{height:100%;width:auto;object-fit:contain}
.hefa-box .fb2{font-size:11px;font-weight:800;color:var(--slate)}
.hefa-labels{text-align:right}
.hefa-labels .l1{font-size:9px;font-weight:700;color:var(--pale);letter-spacing:1.2px;text-transform:uppercase}
.hefa-labels .l2{font-size:11px;font-weight:800;color:var(--dark)}
.hefa-labels .l3{font-size:9px;font-weight:600;color:var(--pale)}

/* live badge */
.live-dot{width:8px;height:8px;background:#22C55E;border-radius:50%;animation:blink 1.8s ease-in-out infinite;display:inline-block}
@keyframes blink{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.6)}}

/* ══ FLOATING NAV ══ */
#fnav{
  position:fixed;top:104px;right:26px;z-index:2000;
  background: rgba(255, 255, 255, 0.35); /* Same glass as header */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius:50px;
  padding:7px 20px;
  display:flex;align-items:center;gap:2px;
  border:1.5px solid rgba(13,148,136,.15);
  box-shadow:0 6px 28px rgba(0,0,0,.10),0 2px 8px rgba(13,148,136,.08);
  transition:top .4s cubic-bezier(.4,0,.2,1), background .3s, box-shadow .3s;
}
#fnav.scrolled {
  top: 20px !important; /* Moves the navbar to the top of the screen */
  background: rgba(255, 255, 255, 0.45) !important; /* Elegant light glass */
  border-color: rgba(255,255,255,.3);
  box-shadow: 0 8px 32px rgba(0,0,0,.15);
}

.ni{position:relative}
.nb{
  background:none;border:none;cursor:pointer;
  font-family:'DM Sans',sans-serif;font-size:13px;font-weight:600;
  color:var(--black);
  padding:8px 16px;border-radius:30px;
  transition:all .22s ease;letter-spacing:.2px;white-space:nowrap
}
.nb:hover,.nb.act{color:var(--sun);background:rgba(13,148,136,.10)}
#fnav.scrolled .nb:hover,#fnav.scrolled .nb.act{color:var(--black);background:rgba(13,148,136,.15)}
.nb.cta{background:var(--sun);color:#fff !important;font-weight:700;box-shadow:0 2px 12px rgba(13,148,136,.4)}
.nb.cta:hover{background:#0f766e;transform:translateY(-1px)}

.nd{
  position:absolute;top:calc(100% + 0px);left:50%;
  transform:translateX(-50%);
  background:#fff;
  border:1.5px solid var(--border);
  border-radius:16px;padding:8px;
  min-width:210px;
  opacity:0;visibility:hidden;pointer-events:none;
  transition:all .2s ease;
  box-shadow:0 16px 44px rgba(0,0,0,.12);
  z-index:9999;
}
.nd::before{content:'';position:absolute;bottom:100%;left:0;right:0;height:12px}
.ni:hover .nd,
.ni.dd-open .nd{opacity:1;visibility:visible;pointer-events:all}

.ndi{
  display:block;padding:10px 14px;border-radius:10px;
  color:var(--slate);font-size:13px;font-weight:600;
  text-decoration:none;cursor:pointer;
  transition:all .18s;border:none;background:none;width:100%;text-align:left
}
.ndi:hover{background:var(--sun-p);color:var(--sun)}
.ndi .ndi-sub{display:block;font-size:10.5px;color:var(--pale);font-weight:400;margin-top:1px}

/* ══ SUB-PAGES ══ */
.spage{
  position:fixed;inset:0;z-index:800;
  background:var(--bg);
  transform:translateX(110%);
  transition:transform .45s cubic-bezier(.4,0,.2,1);
  overflow-y:auto
}
.spage.open{transform:translateX(0)}
.sph{
  background:#fff;border-bottom:2px solid var(--border);
  padding:18px 40px;display:flex;align-items:center;gap:16px;
  position:sticky;top:0;z-index:10;
  box-shadow:0 2px 8px rgba(0,0,0,.04)
}
.sp-back{
  background:var(--dark);color:#fff;border:none;cursor:pointer;
  padding:8px 20px;border-radius:30px;font-size:13px;font-weight:700;
  font-family:'DM Sans',sans-serif;transition:all .2s;
  display:flex;align-items:center;gap:7px
}
.sp-back:hover{background:var(--sun)}
.sp-title{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:var(--dark)}
.spc{max-width:1440px;margin:0 auto;padding:32px 40px 80px}

/* ══ HERO SLIDER ══ */
#home { padding-top: 0 !important; }
.hslider{position:relative;height:100vh;overflow:hidden}
.hslide{
  position:absolute;inset:0;opacity:0;
  transition:opacity 1.3s ease;
  display:flex;align-items:center;justify-content:center
}
.hslide.on{opacity:1}
.hsbg{position:absolute;inset:0;background-size:cover;background-position:center}
.hsov{
  position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(12,17,23,.78) 0%,rgba(12,17,23,.32) 55%,transparent 100%)
}
.hsc{position:relative;z-index:2;text-align:center;color:#fff;padding:0 40px;max-width:860px}
.hs-tag{
  display:inline-block;background:rgba(13,148,136,.88);backdrop-filter:blur(8px);
  color:#fff;font-size:10px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;padding:5px 18px;border-radius:20px;margin-bottom:22px;
  border:1px solid rgba(13,148,136,.5)
}
.hs-title{
  font-family:'Syne',sans-serif;font-size:clamp(34px,6vw,72px);
  font-weight:900;line-height:1.06;margin-bottom:20px;
  text-shadow:0 2px 24px rgba(0,0,0,.3)
}
.hs-title em{color:var(--sun-l);font-style:normal}
.hs-sub{font-size:16px;font-weight:400;opacity:.84;max-width:560px;margin:0 auto 36px;line-height:1.72}
.hs-btn{
  display:inline-flex;align-items:center;gap:10px;
  background:var(--sun);color:#fff;
  font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;
  padding:14px 34px;border-radius:50px;border:none;cursor:pointer;
  box-shadow:0 8px 32px rgba(13,148,136,.45);
  transition:all .3s ease;letter-spacing:.3px;text-decoration:none
}
.hs-btn:hover{transform:translateY(-2px);box-shadow:0 14px 42px rgba(13,148,136,.55)}

/* slide backgrounds */
.s1 .hsbg{background: url('assets/solar.png') center/cover no-repeat, linear-gradient(135deg,#0c1117 0%,#1a3a2e 40%,#0c1117 100%)}
.s1 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 60% 55% at 65% 42%,rgba(13,148,136,.26) 0%,transparent 72%),
             radial-gradient(ellipse 40% 60% at 30% 72%,rgba(34,197,94,.14) 0%,transparent 72%)}
.s2 .hsbg{background: url('assets/solar2.jpeg') center/cover no-repeat, linear-gradient(160deg,#0c1e33 0%,#0c1117 50%,#1a1a0c 100%)}
.s2 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 70% 60% at 50% 34%,rgba(14,165,233,.22) 0%,transparent 72%)}
.s3 .hsbg{background: url('assets/solar3.jpg') center/cover no-repeat, linear-gradient(135deg,#1a0c1a 0%,#0c1117 50%,#0c1a0c 100%)}
.s3 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 50% 70% at 72% 52%,rgba(13,148,136,.2) 0%,transparent 72%),
             radial-gradient(ellipse 60% 42% at 22% 34%,rgba(34,197,94,.14) 0%,transparent 72%)}
.s4 .hsbg{background: url('assets/solar4.avif') center/cover no-repeat, linear-gradient(135deg,#0c1117 0%,#1a3a2e 40%,#0c1117 100%)}
.s4 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 60% 55% at 65% 42%,rgba(13,148,136,.26) 0%,transparent 72%),
             radial-gradient(ellipse 40% 60% at 30% 72%,rgba(34,197,94,.14) 0%,transparent 72%)}
.s5 .hsbg{background: url('assets/solar5.jpg') center/cover no-repeat, linear-gradient(160deg,#0c1e33 0%,#0c1117 50%,#1a1a0c 100%)}
.s5 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 70% 60% at 50% 34%,rgba(14,165,233,.22) 0%,transparent 72%)}
.s6 .hsbg{background: url('assets/solar6.jpeg') center/cover no-repeat, linear-gradient(135deg,#1a0c1a 0%,#0c1117 50%,#0c1a0c 100%)}
.s6 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 50% 70% at 72% 52%,rgba(13,148,136,.2) 0%,transparent 72%),
             radial-gradient(ellipse 60% 42% at 22% 34%,rgba(34,197,94,.14) 0%,transparent 72%)}
.s7 .hsbg{background: url('assets/solar7.jpeg') center/cover no-repeat, linear-gradient(135deg,#0c1117 0%,#1a3a2e 40%,#0c1117 100%)}
.s7 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 60% 55% at 65% 42%,rgba(13,148,136,.26) 0%,transparent 72%),
             radial-gradient(ellipse 40% 60% at 30% 72%,rgba(34,197,94,.14) 0%,transparent 72%)}

.s8 .hsbg{background: url('assets/solar8.jpeg') center/cover no-repeat, linear-gradient(160deg,#0c1e33 0%,#0c1117 50%,#1a1a0c 100%)}
.s8 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 70% 60% at 50% 34%,rgba(14,165,233,.22) 0%,transparent 72%)}

.s9 .hsbg{background: url('assets/solar9.jpeg') center/cover no-repeat, linear-gradient(135deg,#1a0c1a 0%,#0c1117 50%,#0c1a0c 100%)}
.s9 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 50% 70% at 72% 52%,rgba(13,148,136,.2) 0%,transparent 72%),
             radial-gradient(ellipse 60% 42% at 22% 34%,rgba(34,197,94,.14) 0%,transparent 72%)}

.s10 .hsbg{background: url('assets/solar10.jpeg') center/cover no-repeat, linear-gradient(135deg,#0c1117 0%,#0c1e33 40%,#0c1117 100%)}
.s10 .hsbg::after{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 65% 50% at 40% 60%,rgba(14,165,233,.18) 0%,transparent 72%),
             radial-gradient(ellipse 45% 65% at 70% 30%,rgba(13,148,136,.2) 0%,transparent 72%)}             

.sdots{position:absolute;bottom:32px;left:50%;transform:translateX(-50%);display:flex;gap:10px;z-index:10}
.sdot{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.38);cursor:pointer;transition:all .3s}
.sdot.on{background:var(--sun);width:28px;border-radius:4px}
.sstats{position:absolute;bottom:72px;right:40px;z-index:10;display:flex;gap:12px}
.sstat{
  background:rgba(255,255,255,.09);backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,.14);border-radius:14px;padding:14px 20px;text-align:center;color:#fff
}
.sstat-v{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:var(--sun-l)}
.sstat-l{font-size:10px;opacity:.62;margin-top:3px;letter-spacing:.5px}

/* ══ SHARED CARD/SECTION STYLES ══ */
.sec-lbl{
  display:inline-flex;align-items:center;gap:8px;
  font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
  color:var(--sun);background:var(--sun-p);padding:5px 14px;border-radius:20px;margin-bottom:14px
}
.sec-title{
  font-family:'Syne',sans-serif;font-size:clamp(26px,4vw,42px);
  font-weight:900;color:var(--dark);line-height:1.1;margin-bottom:12px;letter-spacing:-.5px
}
.sec-title span{color:var(--sun)}

/* stat card */
.kcard{
  background:#fff;border:1px solid var(--border);
  border-radius:var(--r);padding:22px 24px;
  position:relative;overflow:hidden;
  box-shadow:0 2px 10px rgba(0,0,0,.04);transition:all .25s ease
}
.kcard:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.09)}
.kcard::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--sun),var(--sun-l));border-radius:var(--r) var(--r) 0 0}
.kcard.bl::before{background:linear-gradient(90deg,var(--sky),#38BDF8)}
.kcard.gr::before{background:linear-gradient(90deg,var(--leaf),#4ADE80)}
.kcard.am::before{background:linear-gradient(90deg,#F59E0B,#FCD34D)}
.kc-icon{width:40px;height:40px;border-radius:10px;background:var(--sun-p);
  display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:14px}
.kc-icon.bl{background:#E0F2FE} .kc-icon.gr{background:#DCFCE7} .kc-icon.am{background:#FEF3C7}
.kc-lbl{font-size:11px;font-weight:600;color:var(--pale);letter-spacing:1.1px;text-transform:uppercase;margin-bottom:8px}
.kc-val{font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:800;color:var(--dark);letter-spacing:-.5px}
.kc-val small{font-size:14px;font-weight:500;color:var(--pale);margin-left:4px}
.kc-sub{font-size:11px;color:var(--pale);margin-top:5px}
.kgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin-bottom:26px}

/* NEW: 4 Column Layout for Individual Charts */
.fourcol { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }

/* chart wrap */
.cw{background:#fff;border:1px solid var(--border);border-radius:var(--r);padding:24px;
  box-shadow:0 2px 10px rgba(0,0,0,.04);margin-bottom:20px;height:100%;}
.ch{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap;gap:12px}
.ct{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;color:var(--dark)}
.cs{font-size:12px;color:var(--muted);margin-top:3px}
.cleg{display:flex;gap:14px;flex-wrap:wrap}
.cli{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:500;color:var(--muted)}
.cld{width:10px;height:10px;border-radius:50%}
.twocol{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;}
.threecol{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
@media(max-width:1100px){.fourcol{grid-template-columns:1fr 1fr;}}
@media(max-width:900px){.twocol,.threecol,.fourcol{grid-template-columns:1fr;}}

/* plant table */
.ptbl{width:100%;border-collapse:collapse;font-size:13px}
.ptbl th{padding:12px 16px;text-align:left;font-size:10px;font-weight:700;letter-spacing:1px;
  text-transform:uppercase;color:var(--pale);border-bottom:1.5px solid var(--border)}
.ptbl td{padding:13px 16px;border-bottom:1px solid var(--bg);font-weight:500;color:var(--dark)}
.ptbl tr:last-child td{border-bottom:none}
.ptbl tr:hover td{background:var(--bg)}
.sdot2{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600}
.sdot2::before{content:'';width:8px;height:8px;border-radius:50%;background:var(--leaf);
  box-shadow:0 0 0 3px rgba(34,197,94,.2);animation:pd 2s ease-in-out infinite}
.sdot2.off::before{background:#EF4444;box-shadow:0 0 0 3px rgba(239,68,68,.2);animation:none}
@keyframes pd{0%,100%{box-shadow:0 0 0 3px rgba(34,197,94,.2)}50%{box-shadow:0 0 0 6px rgba(34,197,94,.08)}}
.ebar{background:var(--bg);border-radius:4px;height:6px;width:76px;overflow:hidden;display:inline-block;vertical-align:middle;margin-left:8px}
.ef{height:100%;background:linear-gradient(90deg,var(--sun),var(--sun-l));border-radius:4px}

/* data tabs */
.dtabs{display:flex;gap:8px;margin-bottom:22px;flex-wrap:wrap}
.dtab{padding:9px 22px;border-radius:30px;font-size:13px;font-weight:600;
  border:1.5px solid var(--border);background:#fff;cursor:pointer;
  color:var(--muted);transition:all .25s;font-family:'DM Sans',sans-serif}
.dtab.on{background:var(--dark);color:#fff;border-color:var(--dark)}

/* mode toggle */
.mtw{display:flex;justify-content:center;gap:16px;padding-bottom:28px}
.mb{font-family:'Syne',sans-serif;font-size:17px;font-weight:700;
  padding:15px 50px;border-radius:50px;border:2px solid var(--border);
  background:#fff;color:var(--muted);cursor:pointer;transition:all .3s ease;
  box-shadow:0 2px 10px rgba(0,0,0,.04)}
.mb.on{background:var(--sun);color:#fff;border-color:var(--sun);box-shadow:0 8px 30px rgba(13,148,136,.35)}
.mb:hover:not(.on){border-color:var(--sun);color:var(--sun)}

/* source selector */
.ssw{display:flex;gap:0;border:1.5px solid var(--border);border-radius:12px;
  overflow:hidden;background:#fff;width:fit-content;box-shadow:0 2px 8px rgba(0,0,0,.04)}
.ssb{padding:11px 28px;font-size:13px;font-weight:600;border:none;background:none;
  cursor:pointer;color:var(--muted);transition:all .25s;
  font-family:'DM Sans',sans-serif;border-right:1.5px solid var(--border)}
.ssb:last-child{border-right:none}
.ssb.on{background:var(--sun);color:#fff}

/* eco cards */
.eco-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-top:20px}
.eco-c{background:#fff;border:1px solid var(--border);border-radius:var(--r);
  padding:20px;text-align:center;position:relative;overflow:hidden;
  box-shadow:0 2px 8px rgba(0,0,0,.04);transition:all .2s}
.eco-c:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.08)}
.eco-c::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:var(--r) var(--r) 0 0}
.eco-c.co2::before{background:linear-gradient(90deg,#10B981,#34D399)}
.eco-c.coal::before{background:linear-gradient(90deg,#475569,#94A3B8)}
.eco-c.tree::before{background:linear-gradient(90deg,var(--sun),var(--sun-l))}
.eco-icon{font-size:24px;margin-bottom:8px;display:block}
.eco-lbl{font-size:10px;font-weight:700;color:var(--pale);letter-spacing:1.2px;text-transform:uppercase;margin-bottom:8px}
.eco-val{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:800;color:var(--dark)}
.eco-u{font-size:11px;color:var(--pale);font-weight:600;margin-left:3px}
.eco-d{font-size:10px;color:var(--pale);margin-top:4px}

/* grid stat */
.gc{background:var(--dark);color:#fff;border-radius:var(--r);padding:20px;position:relative;overflow:hidden}
.gc::before{content:'';position:absolute;top:-30px;right:-30px;width:100px;height:100px;
  border-radius:50%;background:rgba(13,148,136,.08)}
.gc-l{font-size:10px;color:rgba(255,255,255,.5);letter-spacing:1px;text-transform:uppercase;margin-bottom:10px}
.gc-v{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;color:var(--sun-l)}
.gc-u{font-size:13px;color:rgba(255,255,255,.5);margin-left:3px}
.gcgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px;margin-bottom:24px}

/* map */
.maptab-row{display:flex;gap:8px;margin-bottom:22px}
.maptab{padding:10px 26px;border-radius:30px;font-size:13px;font-weight:600;
  border:1.5px solid var(--border);background:#fff;
  cursor:pointer;color:var(--muted);transition:all .25s;font-family:'DM Sans',sans-serif}
.maptab.on{background:var(--sky2);color:#fff;border-color:var(--sky2)}
.mapph{background:linear-gradient(135deg,#0c1e33,#0c1117);border-radius:var(--r);height:420px;
  display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden;
  margin-bottom:24px;border:1px solid rgba(14,165,233,.2)}
.mapgrid{position:absolute;inset:0;opacity:.08;
  background-image:linear-gradient(rgba(14,165,233,.5) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(14,165,233,.5) 1px,transparent 1px);
  background-size:40px 40px}
.mapnode{position:absolute;width:14px;height:14px;border-radius:50%;background:var(--sun);cursor:pointer;
  box-shadow:0 0 0 4px rgba(13,148,136,.3),0 0 20px rgba(13,148,136,.5);
  animation:np 2s ease-in-out infinite}
@keyframes np{0%,100%{box-shadow:0 0 0 4px rgba(13,148,136,.3),0 0 20px rgba(13,148,136,.5)}
  50%{box-shadow:0 0 0 8px rgba(13,148,136,.1),0 0 35px rgba(13,148,136,.3)}}
.mapph-txt{text-align:center;color:rgba(255,255,255,.5);z-index:2}
.mapph-txt h3{font-family:'Syne',sans-serif;font-size:22px;font-weight:700;margin-bottom:8px}
.map-stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}

.cb-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:16px}
.cb{background:var(--bg);border:1.5px solid var(--border);border-radius:12px;
  padding:16px;text-align:center;cursor:pointer;transition:all .25s;position:relative;overflow:hidden}
.cb:hover,.cb.on{border-color:var(--sun);background:var(--sun-p)}
.cb::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--sun);
  opacity:0;transition:opacity .25s}
.cb:hover::before,.cb.on::before{opacity:1}
.cb-n{font-weight:700;font-size:13px;color:var(--dark);margin-bottom:6px}
.cb-kw{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:var(--sun)}
.cb-lbl{font-size:10px;color:var(--muted);margin-top:2px}

/* transport */
.th{background:linear-gradient(135deg,#022c22 0%,#0c1117 60%,#052e16 100%);
  border-radius:var(--r);padding:48px 40px;color:#fff;position:relative;overflow:hidden;margin-bottom:28px}
.th::before{content:'';position:absolute;top:-60px;right:-60px;width:300px;height:300px;
  border-radius:50%;background:radial-gradient(circle,rgba(34,197,94,.2) 0%,transparent 70%)}
.th-title{font-family:'Syne',sans-serif;font-size:38px;font-weight:900;margin-bottom:12px;position:relative}
.th-title span{color:#4ADE80}
.th-sub{font-size:15px;opacity:.75;max-width:500px;line-height:1.72;position:relative}
.ev-stats{display:flex;gap:22px;margin-top:30px;flex-wrap:wrap;position:relative}
.ev-si{text-align:center;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:16px 24px}
.ev-sv{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;color:#4ADE80}
.ev-sl{font-size:11px;opacity:.6;margin-top:4px}

.ev-feats{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:28px}
.ev-fc{background:#fff;border:1px solid var(--border);border-radius:var(--r);padding:24px;
  box-shadow:0 2px 10px rgba(0,0,0,.04);transition:all .25s}
.ev-fc:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.09)}
.ev-fi{width:48px;height:48px;border-radius:12px;background:#DCFCE7;
  display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:14px}
.ev-ft{font-family:'Syne',sans-serif;font-size:17px;font-weight:700;margin-bottom:8px}
.ev-fd{font-size:13px;color:var(--muted);line-height:1.6}

.trip-card{background:linear-gradient(135deg,#052e16,#0c1117);border-radius:var(--r);padding:32px;color:#fff;margin-bottom:28px}
.trip-title{font-family:'Syne',sans-serif;font-size:22px;font-weight:700;margin-bottom:6px}
.trip-sub{font-size:13px;opacity:.65;margin-bottom:24px}
.trip-row{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.tinp{flex:1;min-width:180px;padding:12px 16px;border-radius:10px;
  background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.13);
  color:#fff;font-size:14px;font-family:'DM Sans',sans-serif;outline:none;transition:border-color .25s}
.tinp::placeholder{color:rgba(255,255,255,.4)}
.tinp:focus{border-color:#4ADE80}
.tbtn{background:#22C55E;color:#fff;border:none;cursor:pointer;
  padding:12px 28px;border-radius:10px;font-weight:700;font-size:14px;
  font-family:'Syne',sans-serif;transition:all .25s;white-space:nowrap}
.tbtn:hover{background:#16A34A}

.sc{background:#fff;border:1px solid var(--border);border-radius:var(--r);padding:20px 24px;
  display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;
  transition:all .2s;box-shadow:0 1px 6px rgba(0,0,0,.04)}
.sc:hover{border-color:#22C55E;box-shadow:0 4px 20px rgba(34,197,94,.12)}
.sc-name{font-weight:700;font-size:15px;margin-bottom:4px}
.sc-addr{font-size:12px;color:var(--muted)}
.sc-tags{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.stag{font-size:10px;font-weight:600;padding:3px 10px;border-radius:20px;background:#DCFCE7;color:#166534}
.stag.w{background:#FEF3C7;color:#92400E}
.sc-acts{display:flex;gap:8px;flex-shrink:0;margin-left:16px}
.sab{padding:8px 14px;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;
  transition:all .2s;border:1.5px solid var(--border);background:#fff;color:var(--muted);font-family:'DM Sans',sans-serif}
.sab:hover{border-color:#22C55E;color:#22C55E}
.sab.p{background:#22C55E;color:#fff;border-color:#22C55E}
.sab.p:hover{background:#16A34A}

.ev-map{background:linear-gradient(135deg,#022c22,#0c1117);border-radius:var(--r);height:380px;
  display:flex;align-items:center;justify-content:center;
  position:relative;overflow:hidden;margin-bottom:24px;border:1px solid rgba(34,197,94,.2)}
.ev-mgrid{position:absolute;inset:0;
  background-image:linear-gradient(rgba(34,197,94,.15) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(34,197,94,.15) 1px,transparent 1px);
  background-size:40px 40px;opacity:.5}
.ev-mn{position:absolute;width:14px;height:14px;border-radius:50%;background:#22C55E;cursor:pointer;
  box-shadow:0 0 0 4px rgba(34,197,94,.3),0 0 20px rgba(34,197,94,.5);animation:np 2s ease-in-out infinite}
.ev-mt{text-align:center;color:rgba(255,255,255,.55);z-index:2}
.ev-mt h3{font-family:'Syne',sans-serif;font-size:22px;font-weight:700;margin-bottom:8px;color:rgba(255,255,255,.82)}

/* about */
.abt-grid{display:grid;grid-template-columns:1.2fr 1fr;gap:60px;align-items:start}
.abt-title{font-family:'Syne',sans-serif;font-size:38px;font-weight:900;color:var(--dark);margin-bottom:20px;line-height:1.1}
.abt-title span{color:var(--sun)}
.abt-body{font-size:15px;color:var(--muted);line-height:1.8;margin-bottom:14px}
.abt-feats{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:22px}
.abt-f{background:var(--bg);border-radius:12px;padding:16px;border-left:3px solid var(--sun)}
.abt-ft{font-weight:700;font-size:14px;margin-bottom:4px}
.abt-fd{font-size:12px;color:var(--muted);line-height:1.5}
.team-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.team-c{background:var(--bg);border-radius:var(--r);padding:22px;text-align:center;border:1px solid var(--border)}
.t-av{width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,var(--sun),var(--sun-l));
  margin:0 auto 14px;display:flex;align-items:center;justify-content:center;
  font-size:24px;color:#fff;font-weight:700;font-family:'Syne',sans-serif}
.t-n{font-weight:700;font-size:15px;margin-bottom:3px}
.t-r{font-size:12px;color:var(--muted)}

/* contact */
.cnt-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px}
.cnt-title{font-family:'Syne',sans-serif;font-size:34px;font-weight:900;color:var(--dark);margin-bottom:10px}
.cnt-title span{color:var(--sun)}
.cnt-sub{font-size:14px;color:var(--muted);margin-bottom:28px;line-height:1.65}
.fg{margin-bottom:18px}
.fl{display:block;font-size:12px;font-weight:600;letter-spacing:.5px;color:var(--slate);margin-bottom:7px}
.fi,.fta{width:100%;padding:12px 16px;border-radius:10px;border:1.5px solid var(--border);
  background:#fff;font-size:14px;font-family:'DM Sans',sans-serif;color:var(--dark);
  outline:none;transition:all .25s}
.fi:focus,.fta:focus{border-color:var(--sun);box-shadow:0 0 0 3px rgba(13,148,136,.1)}
.fta{height:110px;resize:vertical}
.fsub{background:linear-gradient(135deg,var(--sun),var(--sun-l));color:#fff;border:none;
  cursor:pointer;padding:14px 36px;border-radius:50px;font-weight:700;font-size:15px;
  font-family:'Syne',sans-serif;transition:all .3s;
  box-shadow:0 6px 24px rgba(13,148,136,.35);letter-spacing:.3px}
.fsub:hover{transform:translateY(-2px);box-shadow:0 10px 32px rgba(13,148,136,.45)}
.fok{display:none;background:#DCFCE7;border:1px solid #86EFAC;border-radius:12px;
  padding:14px;color:#166534;font-weight:600;font-size:14px;text-align:center;margin-top:14px}

.ci-card{background:var(--dark);color:#fff;border-radius:var(--r);padding:28px;margin-bottom:14px}
.ci-title{font-family:'Syne',sans-serif;font-size:16px;font-weight:700;margin-bottom:18px}
.ci-row{display:flex;align-items:center;gap:14px;padding:12px 0;
  border-bottom:1px solid rgba(255,255,255,.08)}
.ci-row:last-child{border-bottom:none}
.ci-ico{width:38px;height:38px;border-radius:10px;background:rgba(13,148,136,.2);
  display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
.ci-lbl{font-size:10px;color:rgba(255,255,255,.45);letter-spacing:.5px;text-transform:uppercase}
.ci-v{font-size:13px;color:var(--sun-l);font-weight:500;text-decoration:none}
.ci-v:hover{color:var(--sun)}

/* footer */
footer {
  background: #0d9488; 
  color: rgba(255, 255, 255, 0.9); 
  padding: 10px 10px;
  text-align: center;
  font-size: 13px;
  line-height: 1.0;
  border-top: 0px solid rgba(255, 255, 255, 0.15);
  position: relative; 
  z-index: 10;
}
footer strong { color: #fff; } 
footer a { color: #fff; text-decoration: underline; }

/* utils */
.hr{border:none;border-top:1px solid var(--border);margin:20px 0}
.hidden{display:none!important}
@media(max-width:768px){
  .abt-grid,.cnt-grid{grid-template-columns:1fr;gap:32px}
  .ev-feats,.threecol{grid-template-columns:1fr}
  .cb-grid{grid-template-columns:repeat(2,1fr)}
  .sstats{display:none}
  .spc{padding:20px 16px 60px}
}
</style>
</head>
<body>
<div id="loader-screen" style="position:fixed;inset:0;z-index:9999999;background:#0c1117;display:flex;flex-direction:column;align-items:center;justify-content:center;">
  <style>
    @keyframes lspin{to{transform:rotate(360deg)}}
    @keyframes lbar{0%{width:0%}20%{width:15%}40%{width:38%}60%{width:62%}80%{width:85%}100%{width:100%}}
    #loader-screen{transition:opacity .5s ease;}
  </style>
  <div style="position:relative;width:90px;height:90px;margin-bottom:18px;">
    <div style="position:absolute;inset:0;border-radius:50%;border:2px solid rgba(13,148,136,.15);"></div>
    <div style="position:absolute;inset:0;border-radius:50%;border:2px solid transparent;border-top-color:#0d9488;animation:lspin 1.2s linear infinite;"></div>
    <div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:38px;animation:lspin 10s linear infinite;">☀️</div>
  </div>
  <div style="font-family:'Syne',sans-serif;font-size:38px;font-weight:900;color:#fff;letter-spacing:-1px;line-height:1;">
    Sol<span style="color:#FBBF24;">Urja</span>
  </div>
  <div style="font-size:11px;color:rgba(255,255,255,.45);margin-top:8px;letter-spacing:1.5px;text-transform:uppercase;text-align:center;line-height:1.8;">
    by PMR Lab &nbsp;·&nbsp; Electrical Department<br>MNIT Jaipur
  </div>
  <div style="margin-top:32px;width:180px;height:3px;background:rgba(255,255,255,.08);border-radius:10px;overflow:hidden;">
    <div id="ls-bar" style="height:100%;width:0%;background:linear-gradient(90deg,#0d9488,#14b8a6);border-radius:10px;animation:lbar 4s ease forwards;"></div>
  </div>
  <div id="ls-txt" style="font-size:11px;color:rgba(255,255,255,.3);margin-top:10px;letter-spacing:.5px;">Loading solar data...</div>
</div>
<header id="hdr">
  <div class="hdr-left">
    <div class="logo-box" id="mnit-logo">
      <img src="assets/mnit.png" alt="MNIT Logo" style="width:100%;height:100%;object-fit:contain;">
    </div>
<div style="width:72px;height:72px;border-radius:50%;overflow:hidden;border:2px solid rgba(255,255,255,0.3);background:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
      <img src="assets/pmr_logo.jpeg" alt="PMR Logo" style="width:110%;height:110%;object-fit:contain;">
    </div>
  </div>

  <div class="hdr-centre">
    <div class="brand-sun-ring"></div>
    <div class="brand-wrap">
      <div class="brand-name">
        Sol<span>Urja</span>
        <span class="sun-icon">☀️</span>
      </div>
      <div class="brand-tagline">Powered by PMR Lab  ·  <span class="live-dot"></span>  Live Solar Dashboard</div>
      <div class="brand-dept">Electrical Engineering Department  ·  MNIT Jaipur</div>
    </div>
  </div>

  <div class="hdr-right">
    <div class="hefa-box" id="hefa-logo">
      <img src="assets/hefa_logo.png" alt="HEFA Logo" style="height:100%;width:auto;object-fit:contain;">
    </div>
    <div class="hefa-labels">
      <div class="l1">Supported By</div>
      <div class="l2">HEFA Scheme</div>
    </div>
  </div>
</header>

<nav id="fnav">
  <div class="ni">
    <button class="nb act" onclick="goHomeAndScroll('home')">Home</button>
  </div>
  <div class="ni" id="dd-wrap">
    <button class="nb" id="dd-btn">Dashboard ▾</button>
    <div class="nd" id="dd-menu">
      <button class="ndi" onclick="openSP('power-statistics')">
        ⚡ Power Statistics
        <span class="ndi-sub">iSolar, Havells & Combined data</span>
      </button>
      <button class="ndi" onclick="openSP('energy-map')">
        🗺️ Energy Map
        <span class="ndi-sub">Block & real campus map</span>
      </button>
      <button class="ndi" onclick="openSP('transport')">
        🚗 EV Transport
        <span class="ndi-sub">Charging stations & trip planner</span>
      </button>
    </div>
  </div>
  <div class="ni">
    <button class="nb" onclick="goHomeAndScroll('pabout')">About Us</button>
  </div>
  <div class="ni">
    <button class="nb" onclick="goHomeAndScroll('pcontact')">Contact Us</button>
  </div>
</nav>

<div id="page-home">
  <section id="home">
    <div class="hslider" id="hslider">
      <div class="hslide on s1">
        <div class="hsbg"></div><div class="hsov"></div>
        <div class="hsc">
          <h1 class="hs-title">Pathways to <em>Net Zero</em><br>by PMR Lab</h1>
          <p class="hs-sub">Real-time distributed solar monitoring across MNIT Jaipur campus — 250+ kW of clean energy, tracked every 15 minutes.</p>
          <button class="hs-btn" onclick="openSP('power-statistics')">View Dashboard →</button>
        </div>
      </div>
      <div class="hslide s2">
        <div class="hsbg"></div><div class="hsov"></div>
        <div class="hsc">
          <h1 class="hs-title">Every Kilowatt,<br><em>Mapped & Monitored</em></h1>
          <p class="hs-sub">Visualise solar generation across all campus buildings with our interactive block and real-time energy maps.</p>
          <button class="hs-btn" onclick="openSP('energy-map')">Explore Map →</button>
        </div>
      </div>
      <div class="hslide s3">
        <div class="hsbg"></div><div class="hsov"></div>
        <div class="hsc">
          <h1 class="hs-title">Green Campus,<br><em>Greener Mobility</em></h1>
          <p class="hs-sub">Find EV charging stations, plan smart trips, and explore how solar powers the future of campus transportation.</p>
          <button class="hs-btn" onclick="openSP('transport')">EV Transport →</button>
        </div>
      </div>
      <div class="hslide s4">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">Live Analytics</div>
    <h1 class="hs-title">Smart Energy,<br><em>Smarter Campus</em></h1>
    <p class="hs-sub">AI-powered analytics help optimise every watt generated across MNIT Jaipur's distributed solar network in real time.</p>
    <button class="hs-btn" onclick="openSP('power-statistics')">View Analytics →</button>
  </div>
</div>

<div class="hslide s5">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">Emission Tracking</div>
    <h1 class="hs-title">Zero Emissions,<br><em>Maximum Impact</em></h1>
    <p class="hs-sub">Track CO₂ savings, coal offset, and tree equivalents in real time across all 20 campus solar installations.</p>
    <button class="hs-btn" onclick="openSP('power-statistics')">See Impact →</button>
  </div>
</div>

<div class="hslide s6">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">Future Campus</div>
    <h1 class="hs-title">Campus of the<br><em>Future, Today</em></h1>
    <p class="hs-sub">From rooftop panels to EV chargers — MNIT Jaipur is building India's greenest and most connected campus ecosystem.</p>
    <button class="hs-btn" onclick="openSP('transport')">EV Transport →</button>
  </div>
</div>

<div class="hslide s7">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">Net Zero Initiative</div>
    <h1 class="hs-title">Powered by<br><em>Pure Sunlight</em></h1>
    <p class="hs-sub">250+ kW of installed solar capacity generates clean electricity every day, powering labs, classrooms and hostels across MNIT Jaipur.</p>
    <button class="hs-btn" onclick="openSP('power-statistics')">Dashboard →</button>
  </div>
</div>

<div class="hslide s8">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">Campus Energy Map</div>
    <h1 class="hs-title">Every Building,<br><em>Every Watt</em></h1>
    <p class="hs-sub">Explore our interactive campus energy map — see which buildings generate the most solar power and track live output per block.</p>
    <button class="hs-btn" onclick="openSP('energy-map')">Open Map →</button>
  </div>
</div>

<div class="hslide s9">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">HEFA Funded</div>
    <h1 class="hs-title">Research Driving<br><em>Real Change</em></h1>
    <p class="hs-sub">Backed by the HEFA Scheme, PMR Lab's Pathways to Net Zero initiative is translating cutting-edge research into campus-scale impact.</p>
    <button class="hs-btn" onclick="goHomeAndScroll('pabout')">About Us →</button>
  </div>
</div>

<div class="hslide s10">
  <div class="hsbg"></div><div class="hsov"></div>
  <div class="hsc">
    <div class="hs-tag">Join Our Mission</div>
    <h1 class="hs-title">Collaborate With<br><em>PMR Lab</em></h1>
    <p class="hs-sub">Partner with us on India's most ambitious campus sustainability project. Reach out to the team at MNIT Jaipur's Electrical Engineering Department.</p>
    <button class="hs-btn" onclick="goHomeAndScroll('pcontact')">Contact Us →</button>
  </div>
</div>
      <div class="sdots">
  <div class="sdot on" onclick="goSlide(0)"></div>
  <div class="sdot" onclick="goSlide(1)"></div>
  <div class="sdot" onclick="goSlide(2)"></div>
  <div class="sdot" onclick="goSlide(3)"></div>
  <div class="sdot" onclick="goSlide(4)"></div>
  <div class="sdot" onclick="goSlide(5)"></div>
  <div class="sdot" onclick="goSlide(6)"></div>
  <div class="sdot" onclick="goSlide(7)"></div>
  <div class="sdot" onclick="goSlide(8)"></div>
  <div class="sdot" onclick="goSlide(9)"></div>
</div>
      <div class="sstats">
        <div class="sstat"><div class="sstat-v">250+</div><div class="sstat-l">kW Installed</div></div>
        <div class="sstat"><div class="sstat-v">__TOT_ACTIVE__</div><div class="sstat-l">Inverters Live</div></div>
        <div class="sstat"><div class="sstat-v">6</div><div class="sstat-l">EV Chargers</div></div>
      </div>
    </div>
  </section>

  <section id="pabout" style="padding: 100px 40px; background: #ffffff; position: relative; z-index: 10; border-bottom: 1px solid var(--border);">
    <div style="max-width:1200px;margin:0 auto">
      <div class="abt-grid">
        <div>
          <div class="sec-lbl">About PMR Lab</div>
          <h2 class="abt-title">Powering India's <span>Net Zero</span> Future</h2>
          <p class="abt-body">The Power & Machines Research (PMR) Lab at MNIT Jaipur is at the forefront of sustainable energy research. Our Pathways to Net Zero initiative monitors and optimises distributed solar generation across the entire MNIT Jaipur campus using real-time IoT data from iSolarCloud and Havells inverters.</p>
          <p class="abt-body">Supported by the Higher Education Funding Agency (HEFA) scheme, we are building India's most comprehensive campus-scale solar monitoring and analytics platform, providing actionable insights for energy management, emission reduction, and EV integration.</p>
          <div class="abt-feats">
            <div class="abt-f"><div class="abt-ft"> Real-time Monitoring</div><div class="abt-fd">14 iSolarCloud + 6 Havells inverters monitored live every 5 minutes</div></div>
            <div class="abt-f"><div class="abt-ft">Emission Tracking</div><div class="abt-fd">Daily CO₂, coal & tree-equivalent calculations using CEA emission factors</div></div>
            <div class="abt-f"><div class="abt-ft">EV Integration</div><div class="abt-fd">Smart EV charging infrastructure planning for campus ecosystem</div></div>
            <div class="abt-f"><div class="abt-ft">Analytics Engine</div><div class="abt-fd">Hourly, daily, weekly & annual generation trend analysis</div></div>
          </div>
        </div>
        <div>
          <div class="cw" style="margin-bottom:14px">
            <div class="ct" style="margin-bottom:16px">Our Team</div>
            <div class="team-grid">
              <div class="team-c"><div class="t-av">RB</div><div class="t-n">Prof. Rohit Bhakar</div><div class="t-r">Head</div></div>
              <div class="team-c"><div class="t-av" style="background:linear-gradient(135deg,var(--sky),var(--sky2))">AV</div><div class="t-n">Ajay Kumar Verma</div><div class="t-r">Team Lead</div></div>
              <div class="team-c"><div class="t-av" style="background:linear-gradient(135deg,var(--leaf),#16A34A)">Team</div><div class="t-n">Utkarsh Vikram Singh<br>Kunal Sharma</div><div class="t-r"></div></div>
              <div class="team-c"><div class="t-av" style="background:linear-gradient(135deg,#8B5CF6,#6D28D9)">H</div><div class="t-n">HEFA Scheme</div><div class="t-r">Funding & Support</div></div>
            </div>
          </div>
          <div style="background:var(--sun-p);border-radius:var(--r);padding:20px;border:1px solid rgba(13,148,136,.2)">
            <div style="font-weight:700;font-size:14px;color:var(--sun);margin-bottom:10px">Project Highlights</div>
            <div style="font-size:13px;color:var(--slate);line-height:1.8">
              ✅ 250+ kW total installed solar capacity<br>
              ✅ __ISO_TOTAL__ + __HAV_TOTAL__ inverters monitored in real-time<br>
              ✅ 6 EV charging stations on campus<br>
              ✅ HEFA-funded Net Zero initiative<br>
              ✅ Live data updated every 15 minutes
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section id="pcontact" style="padding: 100px 40px; background: var(--bg); position: relative; z-index: 10;">
    <div style="max-width:1200px;margin:0 auto">
      <div class="cnt-grid">
        <div>
          <h2 class="cnt-title">Get In <span>Touch</span></h2>
          <p class="cnt-sub">Have questions about our solar monitoring system or research? Fill out the form and our team will get back to you promptly.</p>
          <form id="cform" onsubmit="sendContact(event)">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
              <div class="fg"><label class="fl">Full Name *</label><input type="text" class="fi" name="name" placeholder="Your name" required></div>
              <div class="fg"><label class="fl">Email Address *</label><input type="email" class="fi" name="email" placeholder="your@email.com" required></div>
            </div>
            <div class="fg"><label class="fl">Institution / Organisation</label><input type="text" class="fi" name="org" placeholder="Your organisation"></div>
            <div class="fg"><label class="fl">Subject *</label><input type="text" class="fi" name="subject" placeholder="What's this about?" required></div>
            <div class="fg"><label class="fl">Message *</label><textarea class="fta" name="message" placeholder="Tell us more about your query..." required></textarea></div>
            <button type="submit" class="fsub">Send Message →</button>
            <div id="fok" class="fok">✅ Message sent! We'll reply to pmrmnit@gmail.com shortly.</div>
          </form>
        </div>
        <div>
          <div class="ci-card">
            <div class="ci-title">Contact Information</div>
            <div class="ci-row"><div class="ci-ico">📧</div><div><div class="ci-lbl">Email</div><a class="ci-v" href="mailto:pmrmnit@gmail.com">pmrmnit@gmail.com</a></div></div>
            <div class="ci-row"><div class="ci-ico">🔗</div><div><div class="ci-lbl">LinkedIn</div><a class="ci-v" href="https://www.linkedin.com/in/pmr-lab-mnit-jaipur" target="_blank">PMR Lab · MNIT Jaipur</a></div></div>
            <div class="ci-row"><div class="ci-ico">📍</div><div><div class="ci-lbl">Address</div><div class="ci-v" style="color:rgba(255,255,255,.7)">Dept. of Electrical Engineering, MNIT Jaipur, Rajasthan – 302017, India</div></div></div>
          </div>
          <div style="background:var(--sun-p);border-radius:var(--r);padding:20px;border:1px solid rgba(13,148,136,.2)">
            <div style="font-weight:700;font-size:14px;color:var(--sun);margin-bottom:8px">⏰ Response Time</div>
            <div style="font-size:13px;color:var(--muted);line-height:1.7">We typically respond within 24–48 hours on working days. For urgent technical queries regarding the solar dashboard, please use the email address above.</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>

<div id="sp-power-statistics" class="spage">
  <div class="sph">
    <button class="sp-back" onclick="closeSP('power-statistics')">← Back</button>
    <div class="sp-title">⚡ Power Statistics Dashboard</div>
  </div>
  <div class="spc">

    <div class="mtw">
      <button class="mb on" id="mb-prod" onclick="switchMode('prod')">☀️ Production</button>
      <button class="mb" id="mb-cons" onclick="switchMode('cons')">⚡ Consumption</button>
    </div>

    <div id="sec-prod">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;margin-bottom:20px">
        <div>
          <div style="font-size:11px;font-weight:700;color:var(--sun);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px">Source</div>
          <div class="ssw">
            <button class="ssb on" onclick="switchSrc('solar',this)">☀️ Solar</button>
            <button class="ssb" onclick="switchSrc('grid',this)">🔌 Grid</button>
          </div>
        </div>
      </div>

      <div id="sec-solar">
        <div class="dtabs">
          <button class="dtab on" onclick="switchDTab('isolar',this)">📡 iSolar Data</button>
          <button class="dtab" onclick="switchDTab('havells',this)">⚡ Havells Data</button>
          <button class="dtab" onclick="switchDTab('combined',this)">🌐 Combined Data</button>
        </div>

        <div id="tab-isolar">
          <div class="kgrid">
            <div class="kcard"><div class="kc-icon">⚡</div><div class="kc-lbl">Peak DC Power</div><div class="kc-val">__ISO_PK_DC__ <small>kW</small></div></div>
            <div class="kcard bl"><div class="kc-icon bl">🔌</div><div class="kc-lbl">Peak AC Power</div><div class="kc-val">__ISO_PK_AC__ <small>kW</small></div></div>
            <div class="kcard gr"><div class="kc-icon gr">☀️</div><div class="kc-lbl">Daily Energy</div><div class="kc-val">__ISO_KWH__ <small>kWh</small></div><div class="kc-sub">__DATE_TODAY__</div></div>
            <div class="kcard"><div class="kc-icon">📡</div><div class="kc-lbl">Active Plants</div><div class="kc-val">__ISO_ACTIVE__ <small>/ __ISO_TOTAL__</small></div><div class="kc-sub">Online Status</div></div>
          </div>

          <div class="cw">
            <div class="ch">
              <div><div class="ct">Per-Plant Power Output — iSolarCloud</div><div class="cs">Individual DC/AC generation per inverter</div></div>
              <div class="cleg"><span class="cli"><span class="cld" style="background:var(--sun)"></span>DC Power</span><span class="cli"><span class="cld" style="background:var(--sky)"></span>AC Power</span></div>
            </div>
            <div style="position:relative; height:220px; width:100%;"><canvas id="c-isolar-bar"></canvas></div>
          </div>

          __ISO_INDIV_CHARTS_HTML__

          <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:20px">
            <div class="cw" style="margin-bottom:0">
              <div class="ch"><div><div class="ct">Aggregated Output — iSolarCloud Plants</div><div class="cs">Real-time DC and AC power curve</div></div></div>
              <div style="position:relative; height:250px; width:100%;"><canvas id="c-isolar-line"></canvas></div>
            </div>
            <div class="cw" style="margin-bottom:0">
              <div class="ch"><div><div class="ct">Plant-wise Energy Share</div><div class="cs">% total kWh contribution</div></div></div>
              <div style="position:relative; height:250px; width:100%;"><canvas id="c-isolar-pie"></canvas></div>
            </div>
          </div>

          <div class="cw">
            <div class="ch"><div class="ct">📋 Plant Status Overview</div></div>
            <div style="overflow-x:auto">
              <table class="ptbl">
                <thead><tr><th>Plant</th><th>Capacity</th><th>DC Power</th><th>AC Power</th><th>Efficiency</th><th>Today kWh</th><th>PLF %</th><th>Status</th></tr></thead>
                <tbody>
                  __ISO_TABLE_BODY__
                </tbody>
              </table>
            </div>
          </div>

          <div class="cw">
            <div class="ch"><div><div class="ct">Weekly Generation (kWh)</div><div class="cs">Last 7 days output</div></div></div>
            <div style="position:relative; height:200px; width:100%;"><canvas id="c-weekly"></canvas></div>
          </div>

          <div style="font-size:11px;font-weight:700;color:var(--leaf);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:7px">🌿 Daily Emission Reduction Estimate</div>
          <div class="eco-row">
            <div class="eco-c co2"><span class="eco-icon">💨</span><div class="eco-lbl">CO₂ Reduced</div><div class="eco-val">__ISO_CO2__<span class="eco-u"> ton</span></div><div class="eco-d">__ISO_KWH_INT__ kWh × 0.997 kg/kWh</div></div>
            <div class="eco-c coal"><span class="eco-icon">🪨</span><div class="eco-lbl">Coal Saved</div><div class="eco-val">__ISO_COAL__<span class="eco-u"> ton</span></div><div class="eco-d">__ISO_KWH_INT__ kWh × 0.404 kg/kWh</div></div>
            <div class="eco-c tree"><span class="eco-icon">🌳</span><div class="eco-lbl">Equivalent Trees</div><div class="eco-val">__ISO_TREE__<span class="eco-u"> trees</span></div><div class="eco-d">__ISO_KWH_INT__ kWh × 0.054 trees/kWh</div></div>
          </div>
        </div>

        <div id="tab-havells" class="hidden">
          <div class="kgrid">
            <div class="kcard"><div class="kc-icon">⚡</div><div class="kc-lbl">Peak DC Power</div><div class="kc-val">__HAV_PK_DC__ <small>kW</small></div></div>
            <div class="kcard bl"><div class="kc-icon bl">🔌</div><div class="kc-lbl">Peak AC Power</div><div class="kc-val">__HAV_PK_AC__ <small>kW</small></div></div>
            <div class="kcard gr"><div class="kc-icon gr">☀️</div><div class="kc-lbl">Daily Energy</div><div class="kc-val">__HAV_KWH__ <small>kWh</small></div></div>
            <div class="kcard"><div class="kc-icon">📡</div><div class="kc-lbl">Active Inverters</div><div class="kc-val">__HAV_ACTIVE__ <small>/ __HAV_TOTAL__</small></div></div>
          </div>
          <div class="cw">
            <div class="ch"><div><div class="ct">Havells Inverter Output</div><div class="cs">Per-inverter DC and AC power</div></div>
            <div class="cleg"><span class="cli"><span class="cld" style="background:#F59E0B"></span>DC</span><span class="cli"><span class="cld" style="background:var(--sky)"></span>AC</span></div></div>
            <div style="position:relative; height:220px; width:100%;"><canvas id="c-hav-bar"></canvas></div>
          </div>

          __HAV_INDIV_CHARTS_HTML__

          <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:20px">
            <div class="cw" style="margin-bottom:0">
              <div class="ch"><div><div class="ct">Aggregated Output — Havells</div></div></div>
              <div style="position:relative; height:250px; width:100%;"><canvas id="c-hav-line"></canvas></div>
            </div>
            <div class="cw" style="margin-bottom:0">
              <div class="ch"><div><div class="ct">Plant-wise Energy Share</div><div class="cs">% total kWh contribution</div></div></div>
              <div style="position:relative; height:250px; width:100%;"><canvas id="c-hav-pie"></canvas></div>
            </div>
          </div>

          <div class="cw">
            <div class="ch"><div class="ct">📋 Plant Status Overview</div></div>
            <div style="overflow-x:auto">
              <table class="ptbl">
                <thead><tr><th>Plant</th><th>Capacity</th><th>DC Power</th><th>AC Power</th><th>Efficiency</th><th>Today kWh</th><th>PLF %</th><th>Status</th></tr></thead>
                <tbody>
                  __HAV_TABLE_BODY__
                </tbody>
              </table>
            </div>
          </div>

          <div class="cw">
            <div class="ch"><div><div class="ct">Weekly Generation (kWh)</div><div class="cs">Last 7 days output</div></div></div>
            <div style="position:relative; height:200px; width:100%;"><canvas id="c-hav-weekly"></canvas></div>
          </div>
          <div style="font-size:11px;font-weight:700;color:var(--leaf);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:7px">🌿 Daily Emission Reduction Estimate</div>
          <div class="eco-row">
            <div class="eco-c co2"><span class="eco-icon">💨</span><div class="eco-lbl">CO₂ Reduced</div><div class="eco-val">__HAV_CO2__<span class="eco-u"> ton</span></div><div class="eco-d">__HAV_KWH_INT__ kWh × 0.997 kg/kWh</div></div>
            <div class="eco-c coal"><span class="eco-icon">🪨</span><div class="eco-lbl">Coal Saved</div><div class="eco-val">__HAV_COAL__<span class="eco-u"> ton</span></div><div class="eco-d">__HAV_KWH_INT__ kWh × 0.404 kg/kWh</div></div>
            <div class="eco-c tree"><span class="eco-icon">🌳</span><div class="eco-lbl">Equivalent Trees</div><div class="eco-val">__HAV_TREE__<span class="eco-u"> trees</span></div><div class="eco-d">__HAV_KWH_INT__ kWh × 0.054 trees/kWh</div></div>
          </div>
        </div>

        <div id="tab-combined" class="hidden">
          <div class="kgrid">
            <div class="kcard"><div class="kc-icon">🔵</div><div class="kc-lbl">iSolarCloud Energy</div><div class="kc-val">__ISO_KWH__ <small>kWh</small></div></div>
            <div class="kcard am"><div class="kc-icon am">🟠</div><div class="kc-lbl">Havells Energy</div><div class="kc-val">__HAV_KWH__ <small>kWh</small></div></div>
            <div class="kcard gr"><div class="kc-icon gr">🟢</div><div class="kc-lbl">Total Daily Energy</div><div class="kc-val">__TOT_KWH__ <small>kWh</small></div></div>
            <div class="kcard bl"><div class="kc-icon bl">🔝</div><div class="kc-lbl">Combined Peak AC</div><div class="kc-val">__TOT_PK_AC__ <small>kW</small></div></div>
            
          </div>
          <div class="cw">
            <div class="ch">
              <div><div class="ct">Combined Solar Generation — iSolarCloud + Havells</div></div>
              <div class="cleg"><span class="cli"><span class="cld" style="background:var(--sun)"></span>iSolar AC</span><span class="cli"><span class="cld" style="background:#F59E0B"></span>Havells AC</span><span class="cli"><span class="cld" style="background:var(--leaf)"></span>Total AC</span></div>
            </div>
            <div style="position:relative; height:250px; width:100%;"><canvas id="c-comb-line"></canvas></div>
          </div>
          <div class="twocol">
            <div class="cw"><div class="ch"><div><div class="ct">Total Production Rate</div><div class="cs">Hourly generation profile</div></div></div><div style="position:relative; height:250px; width:100%;"><canvas id="c-rate"></canvas></div></div>
            <div class="cw"><div class="ch"><div><div class="ct">Total Plant Share</div><div class="cs">Current Energy Output Share (kWh)</div></div></div><div style="position:relative; height:250px; width:100%;"><canvas id="c-all-pie"></canvas></div></div>
          </div>
          <div style="font-size:11px;font-weight:700;color:var(--leaf);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:7px">🌿 Total Daily Emission Reduction</div>
          <div class="eco-row" style="margin-bottom:20px;">
            <div class="eco-c co2"><span class="eco-icon">💨</span><div class="eco-lbl">CO₂ Reduced</div><div class="eco-val">__TOT_CO2__<span class="eco-u"> ton</span></div><div class="eco-d">__TOT_KWH_INT__ kWh × 0.997 kg/kWh</div></div>
            <div class="eco-c coal"><span class="eco-icon">🪨</span><div class="eco-lbl">Coal Saved</div><div class="eco-val">__TOT_COAL__<span class="eco-u"> ton</span></div><div class="eco-d">__TOT_KWH_INT__ kWh × 0.404 kg/kWh</div></div>
            <div class="eco-c tree"><span class="eco-icon">🌳</span><div class="eco-lbl">Equivalent Trees</div><div class="eco-val">__TOT_TREE__<span class="eco-u"> trees</span></div><div class="eco-d">__TOT_KWH_INT__ kWh × 0.054 trees/kWh</div></div>
          </div>
          <div class="cw">
            <div class="ch">
                <div>
                    <div class="ct">Historical Generation</div>
                    <div class="cs">Monthly & Yearly Yield (kWh)</div>
                </div>
            </div>
            <div class="twocol">
                <div><div style="position:relative; height:250px; width:100%;"><canvas id="monthlyChart"></canvas></div></div>
                <div><div style="position:relative; height:250px; width:100%;"><canvas id="yearlyChart"></canvas></div></div>
            </div>
          </div>
        </div>
      </div>

      <div id="sec-grid" class="hidden">
        <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:var(--dark);margin-bottom:20px">🔌 Grid Information</div>
        <div class="gcgrid">
          <div class="gc"><div class="gc-l">Grid Voltage (R)</div><div class="gc-v">231.4<span class="gc-u">V</span></div></div>
          <div class="gc"><div class="gc-l">Grid Voltage (Y)</div><div class="gc-v">229.8<span class="gc-u">V</span></div></div>
          <div class="gc"><div class="gc-l">Grid Voltage (B)</div><div class="gc-v">232.1<span class="gc-u">V</span></div></div>
          <div class="gc"><div class="gc-l">Grid Frequency</div><div class="gc-v">49.98<span class="gc-u">Hz</span></div></div>
          <div class="gc"><div class="gc-l">Grid Current (R)</div><div class="gc-v">42.3<span class="gc-u">A</span></div></div>
          
          <div class="gc"><div class="gc-l">Self-Sufficiency</div><div class="gc-v" id="val-grid-ss">--<span class="gc-u">%</span></div></div>
          <div class="gc"><div class="gc-l">Grid Import Today</div><div class="gc-v" id="val-grid-imp">--<span class="gc-u">kWh</span></div></div>
          <div class="gc"><div class="gc-l">Grid Export Today</div><div class="gc-v" id="val-grid-exp">--<span class="gc-u">kWh</span></div></div>
        </div>
        
        <div class="twocol">
          <div class="cw"><div class="ch"><div><div class="ct">Solar vs Grid Draw</div><div class="cs">Capacity source breakdown</div></div></div><div style="position:relative; height:250px; width:100%;"><canvas id="c-sg-pie"></canvas></div></div>
          <div class="cw"><div class="ch"><div><div class="ct">Grid Power Timeline</div><div class="cs">Import throughout the day</div></div></div><div style="position:relative; height:250px; width:100%;"><canvas id="c-grid-t"></canvas></div></div>
        </div>

        <div class="threecol">
          <div class="cw"><div class="ch"><div><div class="ct">Demand vs Solar Gen</div><div class="cs">Total Daily Energy (kWh)</div></div></div><div style="position:relative; height:200px; width:100%;"><canvas id="c-grid-bar"></canvas></div></div>
          <div class="cw"><div class="ch"><div><div class="ct">Net Grid Flow</div><div class="cs">Above 0 = Import, Below 0 = Export (kW)</div></div></div><div style="position:relative; height:200px; width:100%;"><canvas id="c-grid-net"></canvas></div></div>
          <div class="cw"><div class="ch"><div><div class="ct">Self-Sufficiency Gauge</div><div class="cs">% of load covered by solar</div></div></div><div style="position:relative; height:200px; width:100%;"><canvas id="c-grid-gauge"></canvas></div></div>
        </div>
      </div>
    </div>

    <div id="sec-cons" class="hidden">
      <div class="dtabs" style="margin-bottom:24px;">
        <button class="dtab ewtab on" onclick="switchEWTab('cg',this)">⚡ Cons / Gen</button>
        <button class="dtab ewtab" onclick="switchEWTab('demand',this)">📈 Demand</button>
        <button class="dtab ewtab" onclick="switchEWTab('meter',this)">📊 Meter Data</button>
        <button class="dtab ewtab" onclick="switchEWTab('target',this)">🎯 Target vs Actual</button>
      </div>

      <div id="ew-cg">
        <div class="cw" style="margin-bottom:20px;">
          <div class="ch"><div class="ct">Daily Summary</div><div class="cs">Total Absolute Active Energy (kWh)</div></div>
          <div style="position:relative; height:200px; width:100%;"><canvas id="c-ew-cg-daily"></canvas></div>
        </div>
        
        <div class="cw" style="margin-bottom:20px;">
          <div class="ch">
            <div><div class="ct">Interval Saving Overview (kWh)</div><div class="cs">15-min tracking for __DATE_YESTERDAY__</div></div>
            <div class="cleg">
              <span class="cli"><span class="cld" style="background:var(--sky)"></span>Institutional</span>
              <span class="cli"><span class="cld" style="background:var(--sun)"></span>Residential</span>
            </div>
          </div>
          <div style="position:relative; height:250px; width:100%;"><canvas id="c-ew-cg-interval"></canvas></div>
        </div>
      </div>

      <div id="ew-demand" class="hidden">
        <div class="cw" style="margin-bottom:20px;">
          <div class="ch"><div class="ct">Daily Max Demand</div><div class="cs">Highest Peak Demand (kW)</div></div>
          <div style="position:relative; height:200px; width:100%;"><canvas id="c-ew-dem-daily"></canvas></div>
        </div>
        <div class="cw" style="margin-bottom:20px;">
          <div class="ch">
<div><div class="ct">Demand Interval Profile (kW)</div><div class="cs">Demand over time for __DATE_YESTERDAY__</div></div>
            <div class="cleg">
              <span class="cli"><span class="cld" style="background:var(--leaf)"></span>Institutional</span>
              <span class="cli"><span class="cld" style="background:#F59E0B"></span>Residential</span>
            </div>
          </div>
          <div style="position:relative; height:250px; width:100%;"><canvas id="c-ew-dem-interval"></canvas></div>
        </div>
      </div>

      <div id="ew-meter" class="hidden">
        <div class="cw" style="margin-bottom:20px;">
          <div class="ch"><div class="ct">Cons/Gen Export</div><div class="cs">Active Energy (kWh) directly mapped from Meter</div></div>
          <div style="position:relative; height:200px; width:100%;"><canvas id="c-ew-meter-cg"></canvas></div>
        </div>
        <div class="twocol">
          <div class="cw" style="margin-bottom:0;">
            <div class="ch"><div class="ct">Load Off Export</div><div class="cs">Downtime Tracking (kWh)</div></div>
            <div style="position:relative; height:250px; width:100%;"><canvas id="c-ew-meter-lo"></canvas></div>
          </div>
          <div class="cw" style="margin-bottom:0;">
            <div class="ch"><div class="ct">Meter Reading</div><div class="cs">Total Accumulated Readings</div></div>
            <div style="position:relative; height:250px; width:100%;"><canvas id="c-ew-meter-rd"></canvas></div>
          </div>
        </div>
      </div>

      <div id="ew-target" class="hidden">
        <div class="cw" style="margin-bottom:20px;">
          <div class="ch"><div class="ct">Daily View</div><div class="cs">Total Target vs Actual Energy (kWh)</div></div>
          <div style="position:relative; height:200px; width:100%;"><canvas id="c-ew-tva-d"></canvas></div>
        </div>
        <div class="twocol">
          <div class="cw" style="margin-bottom:0;">
            <div class="ch"><div class="ct">Hourly Profile</div><div class="cs">Tracking intraday target alignment</div></div>
            <div style="position:relative; height:250px; width:100%;"><canvas id="c-ew-tva-h"></canvas></div>
          </div>
          <div class="cw" style="margin-bottom:0;">
            <div class="ch"><div class="ct">Monthly Trends</div><div class="cs">Macro evaluation over past months</div></div>
            <div style="position:relative; height:250px; width:100%;"><canvas id="c-ew-tva-m"></canvas></div>
          </div>
        </div>
      </div>

    </div>

  </div>
</div>

<div id="sp-energy-map" class="spage">
  <div class="sph">
    <button class="sp-back" onclick="closeSP('energy-map')">← Back</button>
    <div class="sp-title">🗺️ Campus Energy Map</div>
  </div>
  
    <div class="spc">
    __ENERGY_MAP_HTML__
  </div>
</div>
</div>

<div id="sp-transport" class="spage">
  <div class="sph">
    <button class="sp-back" onclick="closeSP('transport')">← Back</button>
    <div class="sp-title">🚗 EV Transport Hub</div>
  </div>
  <div class="spc">
    __EV_TRANSPORT_HTML__
  </div>
</div>


<footer>
  <div>© 2026 <strong>SolarVeda — PMR Lab, MNIT Jaipur</strong>. All rights reserved.</div>
  <div style="margin-top:6px">Electrical Engineering Department · Malaviya National Institute of Technology Jaipur, Rajasthan – 302017</div>
  <div style="margin-top:6px">Supported by <strong>HEFA Scheme, Govt. of India</strong> · Built for the <em>Pathways to Net Zero</em> Initiative</div>
  <div style="margin-top:8px"><a href="mailto:pmrmnit@gmail.com">📧 pmrmnit@gmail.com</a> · <a href="https://www.linkedin.com/in/pmr-lab-mnit-jaipur" target="_blank">🔗 LinkedIn</a></div>
</footer>

<script>
// ── INJECTED DATA FROM PYTHON ────────────────────────────────────────────────
const HOURS = __JS_HOURS__;

// iSolarCloud Data
const plantN = __JS_ISO_NAMES__;
const plantDC = __JS_ISO_DC__;
const plantAC = __JS_ISO_AC__;
const isoLineDC = __JS_ISO_LINE_DC__;
const isoLineAC = __JS_ISO_LINE_AC__;

// Havells Data
const hn = __JS_HAV_NAMES__;
const hdC = __JS_HAV_DC__;
const haC = __JS_HAV_AC__;
const havLineDC = __JS_HAV_LINE_DC__;
const havLineAC = __JS_HAV_LINE_AC__;

// Combined Data
const totLineAC = __JS_TOT_LINE_AC__;

// ==========================================
// EWATCH DATA INJECTIONS
// ==========================================

// 1. Cons / Gen
const cgDData = __JS_CG_DAILY__;
const cgIT = __JS_CG_INST_T__, cgIV = __JS_CG_INST_V__;
const cgRT = __JS_CG_RES_T__, cgRV = __JS_CG_RES_V__;

// 2. Max Demand
const demDData = __JS_DEM_DAILY__;
const demIT = __JS_DEM_INST_T__, demIV = __JS_DEM_INST_V__;
const demRT = __JS_DEM_RES_T__, demRV = __JS_DEM_RES_V__;

// 3. Meter Data
const mCgT = __JS_M_CG_T__, mCgI = __JS_M_CG_I__, mCgR = __JS_M_CG_R__;
const mLoT = __JS_M_LO_T__, mLoI = __JS_M_LO_I__, mLoR = __JS_M_LO_R__;
const mRdT = __JS_M_RD_T__, mRdI = __JS_M_RD_I__, mRdR = __JS_M_RD_R__;

// 4. Target vs Actual
const tvaDT = __JS_TVA_D_T__, tvaDIT = __JS_TVA_D_IT__, tvaDIA = __JS_TVA_D_IA__, tvaDRT = __JS_TVA_D_RT__, tvaDRA = __JS_TVA_D_RA__;
const tvaHT = __JS_TVA_H_T__, tvaHIT = __JS_TVA_H_IT__, tvaHIA = __JS_TVA_H_IA__, tvaHRT = __JS_TVA_H_RT__, tvaHRA = __JS_TVA_H_RA__;
const tvaMT = __JS_TVA_M_T__, tvaMIT = __JS_TVA_M_IT__, tvaMIA = __JS_TVA_M_IA__, tvaMRT = __JS_TVA_M_RT__, tvaMRA = __JS_TVA_M_RA__;


// ── LOADING SCREEN CONTROLLER ────────────────────────────────────────────────
(function(){
  const ls = document.getElementById('loader-screen');
  const bar = document.getElementById('ls-bar');
  const txt = document.getElementById('ls-txt');
  const msgs = ['Loading solar data...','Fetching plant stats...','Rendering charts...','Almost ready...'];
  let si = 0;
  const iv = setInterval(()=>{
    if(si >= msgs.length){ clearInterval(iv); return; }
    txt.textContent = msgs[si]; si++;
  }, 900);
 const startTime = Date.now();
window.addEventListener('load', ()=>{
    clearInterval(iv);
    txt.textContent = 'Done!';
    bar.style.animation = 'none';
    bar.style.width = '100%';
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, 2000 - elapsed);
    setTimeout(()=>{
      ls.style.opacity = '0';
      setTimeout(()=>ls.remove(), 550);
    }, remaining);
  });
})();

// ── Slide show ──────────────────────────────────────────────────────────────
let cs=0;const slides=document.querySelectorAll('.hslide'),dots=document.querySelectorAll('.sdot');
function goSlide(n){slides[cs].classList.remove('on');dots[cs].classList.remove('on');cs=n;slides[cs].classList.add('on');dots[cs].classList.add('on')}
setInterval(()=>goSlide((cs+1)%slides.length),5000);

// ── Header hide on scroll ───────────────────────────────────────────────────
let lastY=0;
window.addEventListener('scroll', () => {
  const h = document.getElementById('hdr');
  const n = document.getElementById('fnav');
  const y = window.scrollY;
  if (y > 80) {
    h.classList.add('hide');
    n.classList.add('scrolled');
  } else {
    h.classList.remove('hide');
    n.classList.remove('scrolled');
  }
  document.querySelectorAll('.fade-in').forEach(e => {
    if(e.getBoundingClientRect().top < window.innerHeight*.9) e.classList.add('visible');
  });
});

// ── Nav: dropdown stable on hover + click outside to close ──────────────────
const ddWrap=document.getElementById('dd-wrap');
ddWrap.addEventListener('mouseleave',()=>ddWrap.classList.remove('dd-open'));
ddWrap.addEventListener('mouseenter',()=>ddWrap.classList.add('dd-open'));
document.addEventListener('click',e=>{if(!ddWrap.contains(e.target))ddWrap.classList.remove('dd-open')});

// ── Smooth Scroll for Sections ──────────────────────────────────────────────
function goHomeAndScroll(id) {
  gHome();
  setTimeout(() => {
    const el = document.getElementById(id);
    if(el) {
     const y = el.getBoundingClientRect().top + window.scrollY; 
     window.scrollTo({top: y, behavior: 'smooth'});
    }
  }, 50);
}

function openSP(id){
  // Close ALL sub-pages first, then open the requested one
  ['power-statistics','energy-map','transport'].forEach(x=>{
    document.getElementById('sp-'+x).classList.remove('open');
  });
  document.getElementById('sp-'+id).classList.add('open');
  ddWrap.classList.remove('dd-open');
  if(id==='power-statistics') setTimeout(initCharts,120);
  if(id==='transport') setTimeout(initEVMap, 300);
  if(id==='energy-map') setTimeout(initMapCharts,120);
}
function closeSP(id){document.getElementById('sp-'+id).classList.remove('open')}

function gHome(){
  ['power-statistics','energy-map','transport'].forEach(x=>document.getElementById('sp-'+x).classList.remove('open'));
}

function switchMode(m){
  document.getElementById('mb-prod').classList.toggle('on',m==='prod');
  document.getElementById('mb-cons').classList.toggle('on',m==='cons');
  document.getElementById('sec-prod').classList.toggle('hidden',m==='cons');
  document.getElementById('sec-cons').classList.toggle('hidden',m==='prod');
  if(m==='cons')setTimeout(initConsCharts,80);
}

function switchSrc(s,btn){
  document.querySelectorAll('.ssb').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById('sec-solar').classList.toggle('hidden',s==='grid');
  document.getElementById('sec-grid').classList.toggle('hidden',s==='solar');
  if(s==='grid')setTimeout(initGridCharts,80);
}

function switchDTab(t,btn){
  document.querySelectorAll('.dtab:not(.ewtab)').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  ['isolar','havells','combined'].forEach(id=>document.getElementById('tab-'+id).classList.toggle('hidden',id!==t));
  if(t==='havells')setTimeout(initHavellsCharts,80);
  if(t==='combined')setTimeout(initCombinedCharts,80);
}

function switchMapTab(t,btn){
  document.querySelectorAll('.maptab').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById('map-block').classList.toggle('hidden',t==='real');
  document.getElementById('map-real').classList.toggle('hidden',t==='block');
}

function switchEWTab(t, btn){
  document.querySelectorAll('.ewtab').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  ['cg','demand','meter','target'].forEach(id=>{
    document.getElementById('ew-'+id).classList.toggle('hidden', id!==t);
  });
  // Trigger chart re-renders based on tab
  setTimeout(initConsCharts,80);
}

function selBlock(el){document.querySelectorAll('.cb').forEach(b=>b.classList.remove('on'));el.classList.add('on')}

function planTrip(){
  const s=document.getElementById('t-start').value,d=document.getElementById('t-dest').value,r=document.getElementById('t-result');
  if(!s||!d){alert('Please enter both starting point and destination.');return}
  r.style.display='block';
  r.innerHTML=`⚡ Planning route from <strong>${s}</strong> to <strong>${d}</strong>...<br>
  🛣️ Estimated distance: ~42 km  |  ⏱ ~55 min<br>
  🔋 Charging stop: Adani Station, Malviya Nagar (recommended)<br>
  <a href="http://googleusercontent.com/maps.google.com/4{encodeURIComponent(s)}/${encodeURIComponent(d)}" target="_blank" style="color:#4ADE80;font-weight:700">📍 Open in Google Maps →</a>`;
}
function openDir(lat,lng){window.open(`http://googleusercontent.com/maps.google.com/5{lat},${lng}`,'_blank')}

function sendContact(e){
  e.preventDefault();
  const fd=new FormData(document.getElementById('cform'));
  window.open(`mailto:pmrmnit@gmail.com?subject=${encodeURIComponent(fd.get('subject'))}&body=${encodeURIComponent('Name: '+fd.get('name')+'\\nEmail: '+fd.get('email')+'\\nOrg: '+fd.get('org')+'\\n\\n'+fd.get('message'))}`);
  document.getElementById('fok').style.display='block';
  document.getElementById('cform').reset();
}

// ══════════════════════════════════════════════════════════════════
//  CHARTS (DYNAMICALLY LINKED TO PYTHON)
// ══════════════════════════════════════════════════════════════════
const ORG='#0d9488',ORGA='rgba(13,148,136,.14)',SKY='#0EA5E9',SKYA='rgba(14,165,233,.1)',
      LEAF='#22C55E',LEAFA='rgba(34,197,94,.1)',AMB='#F59E0B',AMBA='rgba(245,158,11,.1)',
      MUT='#9CA3AF',DRK='#111827',BRD='#E5E7EB';

const tooltip={mode:'index',intersect:false,backgroundColor:DRK,titleColor:'#F9FAFB',bodyColor:'#D1D5DB',borderColor:'#374151',borderWidth:1};
const axX={grid:{color:'#F3F4F6'},ticks:{color:MUT,font:{size:10}}};
const axY={grid:{color:'#F3F4F6'},ticks:{color:MUT,font:{size:10}},beginAtZero:true};
const leg={display:true,position:'top',labels:{color:MUT,font:{size:11},usePointStyle:true,padding:16}};
const baseOpts=(h)=>({responsive:true,plugins:{legend:{...leg},tooltip},scales:{x:{...axX},y:{...axY}}, maintainAspectRatio: false});
const PIE_COL=['#0d9488','#0EA5E9','#22C55E','#F59E0B','#8B5CF6','#EC4899','#14B8A6','#6366F1','#EF4444','#A3E635','#2dd4bf','#06B6D4','#84CC16','#F43F5E'];

// Universal Chart Renderer - Prevents "Canvas already in use" errors on tab clicks
let chartRefs = {};
function mkChart(id,type,data,opts){
  const ctx = document.getElementById(id);
  if(!ctx) return;
  if(chartRefs[id]) chartRefs[id].destroy();
  chartRefs[id] = new Chart(ctx, {type, data, options: opts});
}

let chartsInited=false;
function initCharts(){
  if(chartsInited || plantN.length === 0)return;chartsInited=true;

  const isoBarMax = Math.ceil(Math.max(...plantDC, ...plantAC, 1) * 1.3);
mkChart('c-isolar-bar','bar',{labels:plantN,datasets:[
  {label:'DC kW',data:plantDC,backgroundColor:ORG,borderRadius:5,barPercentage:.55,categoryPercentage:.8},
  {label:'AC kW',data:plantAC,backgroundColor:SKY,borderRadius:5,barPercentage:.55,categoryPercentage:.8}
]},{...baseOpts(), scales:{x:{...axX},y:{...axY, max:isoBarMax}}});

  mkChart('c-isolar-line','line',{labels:HOURS,datasets:[
    {label:'DC kW',data:isoLineDC,borderColor:ORG,backgroundColor:ORGA,fill:true,tension:.4,borderWidth:2,pointRadius:0},
    {label:'AC kW',data:isoLineAC,borderColor:SKY,backgroundColor:SKYA,fill:true,tension:.4,borderWidth:2,pointRadius:0}
  ]},baseOpts());

  mkChart('c-isolar-pie','doughnut',{labels:plantN,datasets:[{data:__JS_ISO_PIE_KWH__,backgroundColor:PIE_COL,borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    {responsive:true,plugins:{legend:{position:'bottom',labels:{color:DRK,font:{size:9},padding:6,usePointStyle:true}},tooltip},cutout:'58%', maintainAspectRatio: false});

  const days=__JS_WEEKLY_DATES__;
  mkChart('c-weekly','bar',{labels:days,datasets:[
    {label:'kWh',data:__JS_WEEKLY_ISO__,backgroundColor:ORG,borderRadius:6,borderSkipped:false}
  ]},{...baseOpts(),plugins:{...baseOpts().plugins,legend:{display:false}}});

  const isoIndiv = __JS_ISO_INDIV_DATA__;
for(const [id, data] of Object.entries(isoIndiv)) {
  const allVals = [...data.dc, ...data.ac].filter(v => v > 0);
  const maxVal = allVals.length ? Math.ceil(Math.max(...allVals) * 1.2) : 5;
  mkChart(id, 'line', {labels: HOURS, datasets:[
    {label:'DC kW', data:data.dc, borderColor:ORG, backgroundColor:ORGA, fill:true, tension:.4, pointRadius:0, borderWidth:2},
    {label:'AC kW', data:data.ac, borderColor:SKY, backgroundColor:SKYA, fill:true, tension:.4, pointRadius:0, borderWidth:2}
  ]}, {...baseOpts(), scales:{x:{...axX},y:{...axY, max:maxVal}}});
}
}

let havInited=false;
function initHavellsCharts(){
  if(havInited || hn.length === 0)return;havInited=true;
  
  mkChart('c-hav-bar','bar',{labels:hn,datasets:[
    {label:'DC kW',data:hdC,backgroundColor:AMB,borderRadius:5,barPercentage:.55},
    {label:'AC kW',data:haC,backgroundColor:SKY,borderRadius:5,barPercentage:.55}
  ]},baseOpts());
  
  mkChart('c-hav-line','line',{labels:HOURS,datasets:[
    {label:'DC kW',data:havLineDC,borderColor:AMB,backgroundColor:AMBA,fill:true,tension:.4,borderWidth:2,pointRadius:0},
    {label:'AC kW',data:havLineAC,borderColor:SKY,backgroundColor:SKYA,fill:true,tension:.4,borderWidth:2,pointRadius:0}
  ]},baseOpts());
  
  mkChart('c-hav-pie','doughnut',{labels:hn,datasets:[{data:__JS_HAV_PIE_KWH__,backgroundColor:PIE_COL,borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    {responsive:true,plugins:{legend:{position:'bottom',labels:{color:DRK,font:{size:9},padding:6,usePointStyle:true}},tooltip},cutout:'58%', maintainAspectRatio: false});
    
  const days=__JS_WEEKLY_DATES__;
  mkChart('c-hav-weekly','bar',{labels:days,datasets:[
    {label:'kWh',data:__JS_WEEKLY_HAV__,backgroundColor:AMB,borderRadius:6,borderSkipped:false}
  ]},{...baseOpts(),plugins:{...baseOpts().plugins,legend:{display:false}}});

  const havIndiv = __JS_HAV_INDIV_DATA__;
  for(const [id, data] of Object.entries(havIndiv)) {
    mkChart(id, 'line', {labels: HOURS, datasets:[
      {label:'DC kW', data:data.dc, borderColor:AMB, backgroundColor:AMBA, fill:true, tension:.4, pointRadius:0},
      {label:'AC kW', data:data.ac, borderColor:SKY, backgroundColor:SKYA, fill:true, tension:.4, pointRadius:0}
    ]}, baseOpts());
  }
}

let combInited=false;
function initCombinedCharts(){
  if(combInited || HOURS.length === 0)return;combInited=true;

  mkChart('c-comb-line','line',{labels:HOURS,datasets:[
    {label:'iSolar AC',data:isoLineAC,borderColor:ORG,backgroundColor:ORGA,fill:true,tension:.4,borderWidth:2,pointRadius:0},
    {label:'Havells AC',data:havLineAC,borderColor:AMB,backgroundColor:AMBA,fill:true,tension:.4,borderWidth:2,pointRadius:0,borderDash:[4,3]},
    {label:'Total AC',data:totLineAC,borderColor:LEAF,fill:false,tension:.4,borderWidth:3,pointRadius:0}
  ]},baseOpts());
  
  mkChart('c-rate','line',{labels:HOURS,datasets:[
    {label:'Total kW',data:totLineAC,borderColor:LEAF,backgroundColor:LEAFA,fill:true,tension:.4,borderWidth:2,pointRadius:0}
  ]},baseOpts());
  
  mkChart('c-all-pie','doughnut',{labels:__JS_ALL_PIE_NAMES__,datasets:[{data:__JS_ALL_PIE_KWH__,backgroundColor:PIE_COL,borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    {responsive:true,plugins:{legend:{position:'right',labels:{color:DRK,font:{size:10},usePointStyle:true}},tooltip},cutout:'55%', maintainAspectRatio: false});

  const mLab = __JS_MONTHLY_LABELS__;
  const mDat = __JS_MONTHLY_DATA__;
  mkChart('monthlyChart', 'bar', {labels: mLab, datasets: [{label: 'kWh', data: mDat, backgroundColor: ORG, borderRadius: 5}]}, baseOpts());

  const yLab = __JS_YEARLY_LABELS__;
  const yDat = __JS_YEARLY_DATA__;
  mkChart('yearlyChart', 'bar', {labels: yLab, datasets: [{label: 'kWh', data: yDat, backgroundColor: LEAF, borderRadius: 5}]}, baseOpts());
}

let gridInited=false;
function initGridCharts(){
  if(gridInited)return;gridInited=true;

  // 1. Core Variables for Power Balance
  let totalGridImportKwh = 0;
  let totalGridExportKwh = 0;
  let solarUsedKwh = 0;
  let totalDemandKwh = 0;
  let totalSolarKwh = 0;
  let gridImportTimeline = [];
  let netGridTimeline = [];

  // Map eWatch Building Consumption (Demand kW) by timestamp
  let consMap = {};
  for(let i=0; i < demIT.length; i++) {
    let tStr = demIT[i].padStart(5, '0'); // normalizes "9:15" to "09:15"
    let instKw = parseFloat(demIV[i]) || 0;
    let resKw = parseFloat(demRV[i]) || 0;
    consMap[tStr] = instKw + resKw; // Total Building Demand (C)
  }

  // 2. Iterate over Solar Hours to calculate exact power flow
  for(let i=0; i < HOURS.length; i++) {
    let time = HOURS[i].padStart(5, '0');
    let s = parseFloat(totLineAC[i]) || 0;  // Solar Generated (kW)
    let c = consMap[time] || 0;             // Building Consumption (kW)

    totalDemandKwh += c * 0.25; // 15 mins = 0.25 hours
    totalSolarKwh += s * 0.25;

    let netGrid = c - s; // Net Grid Equation
    netGridTimeline.push(netGrid);

    if(netGrid > 0) {
      // Consumption > Solar -> IMPORT
      gridImportTimeline.push(netGrid);
      totalGridImportKwh += netGrid * 0.25;
      solarUsedKwh += s * 0.25;
    } else {
      // Solar > Consumption -> EXPORT
      gridImportTimeline.push(0);
      totalGridExportKwh += Math.abs(netGrid) * 0.25;
      solarUsedKwh += c * 0.25;
    }
  }

// Fallback: if no solar data at all, show 100% grid
  const noSolarData = (totLineAC.length === 0 || totLineAC.every(v => v === 0));
  if (noSolarData || (totalGridImportKwh === 0 && totalGridExportKwh === 0 && solarUsedKwh === 0 && totalDemandKwh === 0)) {
    solarUsedKwh = 0;
    totalGridImportKwh = 100;
    totalDemandKwh = 100;
    totalSolarKwh = 0;
    totalGridExportKwh = 0;
    gridImportTimeline = Array.from({length: Math.max(HOURS.length, 1)}, () => 10);
    netGridTimeline = Array.from({length: Math.max(HOURS.length, 1)}, () => 10);
  }

  // Calculate percentage of demand met by solar (capped at 100%)
  let selfSufficiencyRate = totalDemandKwh > 0 ? Math.min(100, Math.round((solarUsedKwh / totalDemandKwh) * 100)) : 0;

  // 3. Inject calculated numbers into the HTML dashboard widgets
  document.getElementById('val-grid-ss').innerHTML = `${selfSufficiencyRate}<span class="gc-u">%</span>`;
  document.getElementById('val-grid-imp').innerHTML = `${totalGridImportKwh.toFixed(1)}<span class="gc-u">kWh</span>`;
  document.getElementById('val-grid-exp').innerHTML = `${totalGridExportKwh.toFixed(1)}<span class="gc-u">kWh</span>`;

  // 4. Render all 5 visual charts using your mkChart wrapper
  
  // A. Solar vs Grid Draw (Pie)
  mkChart('c-sg-pie','pie',{
    labels:['Solar Used','Grid Imported'],
    datasets:[{ data:[solarUsedKwh.toFixed(1), totalGridImportKwh.toFixed(1)], backgroundColor:[ORG,SKY], borderWidth:3, borderColor:'#fff', hoverOffset:6 }]
  }, {responsive:true,plugins:{legend:{position:'top',labels:{color:DRK,font:{size:12},usePointStyle:true}},tooltip}, maintainAspectRatio: false});

  // B. Grid Import Timeline (Line)
  mkChart('c-grid-t','line',{
    labels:HOURS,
    datasets:[{ label:'Grid Import (kW)', data:gridImportTimeline, borderColor:SKY, backgroundColor:SKYA, fill:true, tension:.4, borderWidth:2, pointRadius:0 }]
  },baseOpts());

  // C. Demand vs Solar Gen (Bar Chart)
  mkChart('c-grid-bar','bar',{
    labels:['Total Demand', 'Total Solar'],
    datasets:[{ label:'Energy (kWh)', data:[totalDemandKwh.toFixed(1), totalSolarKwh.toFixed(1)], backgroundColor:[SKY, ORG], borderRadius:5 }]
  },baseOpts());

  // D. Net Grid Flow (Line Chart: Positive=Import, Negative=Export)
  mkChart('c-grid-net','line',{
    labels:HOURS,
    datasets:[{ label:'Net Grid Flow (kW)', data:netGridTimeline, borderColor:'#f59e0b', backgroundColor:'rgba(245,158,11,0.1)', fill:true, tension:.4, borderWidth:2, pointRadius:0 }]
  },baseOpts());

  // E. Self-Sufficiency Gauge (Half-Doughnut Chart)
  mkChart('c-grid-gauge','doughnut',{
    labels:['Self-Sufficient', 'Grid Reliant'],
    datasets:[{ data:[selfSufficiencyRate, 100 - selfSufficiencyRate], backgroundColor:[LEAF, BRD], borderWidth:0, hoverOffset:0, circumference:180, rotation:-90 }]
  }, {responsive:true,plugins:{legend:{display:false},tooltip}, cutout:'75%', maintainAspectRatio: false});
}

  

// Draw dynamic charts across the eWatch menus
function initConsCharts(){
  // 1. Cons / Gen 
  mkChart('c-ew-cg-daily','bar',{labels:['Institutional', 'Residential'],datasets:[{label:'Energy (kWh)',data:cgDData,backgroundColor:[SKY,ORG],borderRadius:4}]},baseOpts());
  
  const cgLabels = cgIT.length >= cgRT.length ? cgIT : cgRT;
  mkChart('c-ew-cg-interval','line',{labels:cgLabels,datasets:[
    {label:'Institutional (kWh)',data:cgIV,borderColor:SKY,backgroundColor:SKYA,fill:true,tension:.3,pointRadius:0},
    {label:'Residential (kWh)',data:cgRV,borderColor:ORG,backgroundColor:ORGA,fill:true,tension:.3,pointRadius:0}
  ]},baseOpts());

  // 2. Max Demand 
  mkChart('c-ew-dem-daily','bar',{labels:['Institutional', 'Residential'],datasets:[{label:'Max Demand (kW)',data:demDData,backgroundColor:[LEAF,AMB],borderRadius:4}]},baseOpts());
  
  const demLabels = demIT.length >= demRT.length ? demIT : demRT;
  mkChart('c-ew-dem-interval','line',{labels:demLabels,datasets:[
    {label:'Institutional (kW)',data:demIV,borderColor:LEAF,backgroundColor:LEAFA,fill:true,tension:.3,pointRadius:0},
    {label:'Residential (kW)',data:demRV,borderColor:AMB,backgroundColor:AMBA,fill:true,tension:.3,pointRadius:0}
  ]},baseOpts());

  // 3. Meter Data 
  mkChart('c-ew-meter-cg','bar',{labels:mCgT,datasets:[{label:'Institutional',data:mCgI,backgroundColor:SKY},{label:'Residential',data:mCgR,backgroundColor:ORG}]},baseOpts());
  mkChart('c-ew-meter-lo','bar',{labels:mLoT,datasets:[{label:'Institutional (Load Off)',data:mLoI,backgroundColor:SKY},{label:'Residential (Load Off)',data:mLoR,backgroundColor:ORG}]},baseOpts());
  mkChart('c-ew-meter-rd','bar',{labels:mRdT,datasets:[{label:'Inst Reading',data:mRdI,backgroundColor:SKY},{label:'Res Reading',data:mRdR,backgroundColor:ORG}]},baseOpts());

  // 4. Target vs Actual 
  mkChart('c-ew-tva-d','bar',{labels:tvaDT,datasets:[{label:'Inst Target',data:tvaDIT,backgroundColor:'rgba(14,165,233,.3)'},{label:'Inst Actual',data:tvaDIA,backgroundColor:SKY},{label:'Res Target',data:tvaDRT,backgroundColor:'rgba(13,148,136,.3)'},{label:'Res Actual',data:tvaDRA,backgroundColor:ORG}]},baseOpts());
  mkChart('c-ew-tva-h','line',{labels:tvaHT,datasets:[{label:'Inst Target',data:tvaHIT,borderColor:SKY,borderDash:[5,5],tension:.3,pointRadius:0},{label:'Inst Actual',data:tvaHIA,borderColor:SKY,backgroundColor:SKYA,fill:true,tension:.3,pointRadius:0},{label:'Res Target',data:tvaHRT,borderColor:ORG,borderDash:[5,5],tension:.3,pointRadius:0},{label:'Res Actual',data:tvaHRA,borderColor:ORG,backgroundColor:ORGA,fill:true,tension:.3,pointRadius:0}]},baseOpts());
  mkChart('c-ew-tva-m','bar',{labels:tvaMT,datasets:[{label:'Inst Target',data:tvaMIT,backgroundColor:'rgba(14,165,233,.3)'},{label:'Inst Actual',data:tvaMIA,backgroundColor:SKY},{label:'Res Target',data:tvaMRT,backgroundColor:'rgba(13,148,136,.3)'},{label:'Res Actual',data:tvaMRA,backgroundColor:ORG}]},baseOpts());
}

let mapChartsInited=false;
function initMapCharts(){
  if(mapChartsInited)return;mapChartsInited=true;
  const bldN=['Elec Dept','MIIC','Multipath','Prabha','Comp Dept','VLTC','Metallurgy'];
  const bldKW=[35,60,75,50,12,29,5];
  mkChart('c-block-bar','bar',{labels:bldN,datasets:[{label:'kW',data:bldKW,backgroundColor:ORG,borderRadius:6,borderSkipped:false}]},
    {responsive:true,plugins:{legend:{display:false},tooltip},scales:{x:{...axX},y:{...axY}}});
  mkChart('c-block-pie','doughnut',{labels:bldN,datasets:[{data:bldKW,backgroundColor:PIE_COL.slice(0,7),borderWidth:2,borderColor:'#fff',hoverOffset:6}]},
    {responsive:true,plugins:{legend:{position:'bottom',labels:{color:DRK,font:{size:10},usePointStyle:true,padding:6}},tooltip},cutout:'55%', maintainAspectRatio: false});
}

</script>
</body>
</html>
"""

# =====================================================
# INJECT DYNAMIC DATA & RENDER HTML
# =====================================================
def get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode()}"
    except FileNotFoundError:
        return "" 

@st.cache_data
def get_all_images():
    paths = {
        "solar":   "assets/solar.png",
        "solar2":  "assets/solar2.jpeg",
        "solar3":  "assets/solar3.jpg",
        "solar4":  "assets/solar4.avif",
        "solar5":  "assets/solar5.jpg",
        "solar6":  "assets/solar6.jpeg",
        "solar7":  "assets/solar7.jpeg",
        "solar8":  "assets/solar8.jpeg",
        "solar9":  "assets/solar9.jpeg",
        "solar10": "assets/solar10.jpeg",
        "mnit":    "assets/mnit.png",
        "pmr":     "assets/pmr_logo.jpeg",
        "hefa":    "assets/hefa_logo.png",
    }
    result = {}
    for key, path in paths.items():
        try:
            with open(path, "rb") as f:
                result[key] = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except FileNotFoundError:
            result[key] = ""
    return result

imgs = get_all_images()
html_code = HTML_TEMPLATE
html_code = html_code.replace("assets/solar.png",     imgs["solar"])
html_code = html_code.replace("assets/solar2.jpeg",   imgs["solar2"])
html_code = html_code.replace("assets/solar3.jpg",    imgs["solar3"])
html_code = html_code.replace("assets/solar4.avif",    imgs["solar4"])
html_code = html_code.replace("assets/solar5.jpg",    imgs["solar5"])
html_code = html_code.replace("assets/solar6.jpeg",   imgs["solar6"])
html_code = html_code.replace("assets/solar7.jpeg",    imgs["solar7"])
html_code = html_code.replace("assets/solar8.jpeg",    imgs["solar8"])
html_code = html_code.replace("assets/solar9.jpeg",    imgs["solar9"])
html_code = html_code.replace("assets/solar10.jpeg",   imgs["solar10"])
html_code = html_code.replace("assets/mnit.png",      imgs["mnit"])
html_code = html_code.replace("assets/pmr_logo.jpeg",  imgs["pmr"])
html_code = html_code.replace("assets/hefa_logo.png", imgs["hefa"])
html_code = html_code.replace("__EV_TRANSPORT_HTML__", ev_section_html)
html_code = html_code.replace("__ENERGY_MAP_HTML__", energy_map_html)
try:
    total_monthly, total_yearly = get_combined_historical()
except Exception:
    total_monthly, total_yearly = {}, {}
html_code = html_code.replace("__JS_MONTHLY_LABELS__", json.dumps(list(total_monthly.keys())))
html_code = html_code.replace("__JS_MONTHLY_DATA__", json.dumps([round(v, 1) for v in total_monthly.values()]))
html_code = html_code.replace("__JS_YEARLY_LABELS__", json.dumps(list(total_yearly.keys())))
html_code = html_code.replace("__JS_YEARLY_DATA__", json.dumps([round(v, 1) for v in total_yearly.values()]))

html_code = html_code.replace("__ISO_TABLE_BODY__", iso_table_rows)
html_code = html_code.replace("__HAV_TABLE_BODY__", hav_table_rows)
html_code = html_code.replace("__HAV_INDIV_CHARTS_HTML__", hav_indiv_html)
html_code = html_code.replace("__ISO_INDIV_CHARTS_HTML__", iso_indiv_html)
html_code = html_code.replace("__JS_ISO_INDIV_DATA__", json.dumps(js_iso_indiv_data))
html_code = html_code.replace("__JS_HAV_INDIV_DATA__", json.dumps(js_hav_indiv_data))

html_code = html_code.replace("__JS_WEEKLY_DATES__", json.dumps(weekly_dates))
html_code = html_code.replace("__JS_WEEKLY_ISO__", json.dumps(weekly_iso_data))
html_code = html_code.replace("__JS_WEEKLY_HAV__", json.dumps(weekly_hav_data))

html_code = html_code.replace("__JS_ALL_PIE_NAMES__", json.dumps(js_iso_names + js_hav_names))
html_code = html_code.replace("__JS_ALL_PIE_KWH__", json.dumps([round(x, 1) for x in js_iso_kwh] + [round(x, 1) for x in js_hav_kwh]))
html_code = html_code.replace("__JS_ISO_PIE_KWH__", json.dumps([round(x, 1) for x in js_iso_kwh]))
html_code = html_code.replace("__JS_HAV_PIE_KWH__", json.dumps([round(x, 1) for x in js_hav_kwh]))

html_code = html_code.replace("__JS_HOURS__", js_hours)
html_code = html_code.replace("__JS_ISO_NAMES__", json.dumps(js_iso_names))
html_code = html_code.replace("__JS_ISO_DC__", js_iso_plant_dc)
html_code = html_code.replace("__JS_ISO_AC__", js_iso_plant_ac)
html_code = html_code.replace("__JS_ISO_LINE_DC__", js_iso_dc)
html_code = html_code.replace("__JS_ISO_LINE_AC__", js_iso_ac)

html_code = html_code.replace("__JS_HAV_NAMES__", json.dumps(js_hav_names))
html_code = html_code.replace("__JS_HAV_DC__", js_hav_plant_dc)
html_code = html_code.replace("__JS_HAV_AC__", js_hav_plant_ac)
html_code = html_code.replace("__JS_HAV_LINE_DC__", js_hav_dc)
html_code = html_code.replace("__JS_HAV_LINE_AC__", js_hav_ac)

html_code = html_code.replace("__JS_TOT_LINE_AC__", js_tot_ac)

html_code = html_code.replace("__DATE_TODAY__", display_date_str)
html_code = html_code.replace("__DATE_YESTERDAY__", display_yesterday_str)
html_code = html_code.replace("__ISO_PK_DC__", f"{iso_pk_dc:,.1f}")
html_code = html_code.replace("__ISO_PK_AC__", f"{iso_pk_ac:,.1f}")
html_code = html_code.replace("__ISO_KWH__", f"{iso_kwh:,.1f}")
html_code = html_code.replace("__ISO_KWH_INT__", f"{iso_kwh:,.0f}")
html_code = html_code.replace("__ISO_ACTIVE__", f"{len(valid_iso)}")
html_code = html_code.replace("__ISO_TOTAL__", f"{len(PLANTS)}")
html_code = html_code.replace("__ISO_CO2__", f"{(iso_kwh * CO2_PER_KWH)/1000:,.3f}")
html_code = html_code.replace("__ISO_COAL__", f"{(iso_kwh * COAL_PER_KWH)/1000:,.3f}")
html_code = html_code.replace("__ISO_TREE__", f"{(iso_kwh * TREES_PER_KWH):,.1f}")

html_code = html_code.replace("__HAV_PK_DC__", f"{hav_pk_dc:,.1f}")
html_code = html_code.replace("__HAV_PK_AC__", f"{hav_pk_ac:,.1f}")
html_code = html_code.replace("__HAV_KWH__", f"{hav_kwh:,.1f}")
html_code = html_code.replace("__HAV_KWH_INT__", f"{hav_kwh:,.0f}")
html_code = html_code.replace("__HAV_ACTIVE__", f"{len(valid_hav)}")
html_code = html_code.replace("__HAV_TOTAL__", f"{len(HAVELLS_PLANTS)}")
html_code = html_code.replace("__HAV_CO2__", f"{(hav_kwh * CO2_PER_KWH)/1000:,.3f}")
html_code = html_code.replace("__HAV_COAL__", f"{(hav_kwh * COAL_PER_KWH)/1000:,.3f}")
html_code = html_code.replace("__HAV_TREE__", f"{(hav_kwh * TREES_PER_KWH):,.1f}")

html_code = html_code.replace("__TOT_PK_AC__", f"{tot_pk_ac:,.1f}")
html_code = html_code.replace("__TOT_KWH__", f"{tot_kwh:,.1f}")
html_code = html_code.replace("__TOT_KWH_INT__", f"{tot_kwh:,.0f}")
html_code = html_code.replace("__TOT_ACTIVE__", f"{len(valid_iso) + len(valid_hav)}")
html_code = html_code.replace("__TOT_CO2__", f"{(tot_kwh * CO2_PER_KWH)/1000:,.3f}")
html_code = html_code.replace("__TOT_CO2_KG__", f"{(tot_kwh * CO2_PER_KWH):,.0f}")
html_code = html_code.replace("__TOT_COAL__", f"{(tot_kwh * COAL_PER_KWH)/1000:,.3f}")
html_code = html_code.replace("__TOT_TREE__", f"{(tot_kwh * TREES_PER_KWH):,.1f}")

# --- NEW 12 FILE EWATCH INJECTIONS ---

html_code = html_code.replace("__JS_CG_DAILY__", ew_cg_daily)
html_code = html_code.replace("__JS_CG_INST_T__", ew_cg_inst_t)
html_code = html_code.replace("__JS_CG_INST_V__", ew_cg_inst_v)
html_code = html_code.replace("__JS_CG_RES_T__", ew_cg_res_t)
html_code = html_code.replace("__JS_CG_RES_V__", ew_cg_res_v)

html_code = html_code.replace("__JS_DEM_DAILY__", ew_dem_daily)
html_code = html_code.replace("__JS_DEM_INST_T__", ew_dem_inst_t)
html_code = html_code.replace("__JS_DEM_INST_V__", ew_dem_inst_v)
html_code = html_code.replace("__JS_DEM_RES_T__", ew_dem_res_t)
html_code = html_code.replace("__JS_DEM_RES_V__", ew_dem_res_v)

html_code = html_code.replace("__JS_M_CG_T__", m_cg_t)
html_code = html_code.replace("__JS_M_CG_I__", m_cg_i)
html_code = html_code.replace("__JS_M_CG_R__", m_cg_r)

html_code = html_code.replace("__JS_M_LO_T__", m_lo_t)
html_code = html_code.replace("__JS_M_LO_I__", m_lo_i)
html_code = html_code.replace("__JS_M_LO_R__", m_lo_r)

html_code = html_code.replace("__JS_M_RD_T__", m_rd_t)
html_code = html_code.replace("__JS_M_RD_I__", m_rd_i)
html_code = html_code.replace("__JS_M_RD_R__", m_rd_r)

html_code = html_code.replace("__JS_TVA_D_T__", tva_d_t)
html_code = html_code.replace("__JS_TVA_D_IT__", tva_d_it)
html_code = html_code.replace("__JS_TVA_D_IA__", tva_d_ia)
html_code = html_code.replace("__JS_TVA_D_RT__", tva_d_rt)
html_code = html_code.replace("__JS_TVA_D_RA__", tva_d_ra)

html_code = html_code.replace("__JS_TVA_H_T__", tva_h_t)
html_code = html_code.replace("__JS_TVA_H_IT__", tva_h_it)
html_code = html_code.replace("__JS_TVA_H_IA__", tva_h_ia)
html_code = html_code.replace("__JS_TVA_H_RT__", tva_h_rt)
html_code = html_code.replace("__JS_TVA_H_RA__", tva_h_ra)

html_code = html_code.replace("__JS_TVA_M_T__", tva_m_t)
html_code = html_code.replace("__JS_TVA_M_IT__", tva_m_it)
html_code = html_code.replace("__JS_TVA_M_IA__", tva_m_ia)
html_code = html_code.replace("__JS_TVA_M_RT__", tva_m_rt)
html_code = html_code.replace("__JS_TVA_M_RA__", tva_m_ra)

st.components.v1.html(html_code, height=1200, scrolling=True)