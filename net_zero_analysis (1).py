# -*- coding: utf-8 -*-
"""
net_zero_analysis.py
====================
Standalone analysis script (no PSS/E required). Run with Python 3.

Calculates:
  1. Additional PV needed for net-zero energy
  2. Hosting capacity per bus (voltage sensitivity)
  3. Optimal PV placement using Voltage Sensitivity Index (VSI)
  4. Loss Sensitivity Factor (LSF) ranking
  5. CO2 and economic savings
  6. Exports everything to CSV (UTF-8 with BOM for Excel)

Run:
    python net_zero_analysis.py

Author  : M.Tech Intern
Fix     : Removed all Unicode/non-ASCII characters to avoid cp1252 errors
          All CSV files opened with encoding='utf-8-sig' for Excel compatibility
"""

import math
import csv
import os
import sys

# Handle import path so campus_data.py can be found
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from campus_data import (
    ALL_TRANSFORMERS, SOLAR_PLANTS,
    SOLAR_CAPACITY_FACTOR, GRID_EMISSION_FACTOR,
    SYSTEM_MVA_BASE, amps_to_mw
)

OUTPUT_DIR = os.path.join(THIS_DIR, "psse_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===========================================================================
# CONSTANTS  (update from your actual campus records)
# ===========================================================================
ELECTRICITY_TARIFF_INR_KWH = 7.50      # Campus HT tariff (Rs/kWh)
SOLAR_CAPEX_INR_PER_KW     = 45000.0   # Rs 45,000 per kW installed (2024)
SOLAR_OPEX_INR_PER_KW_YR   = 800.0     # Annual O&M per kW
LOAD_FACTOR                = 0.60      # Campus annual load factor
HOURS_PER_YEAR             = 8760.0


# ===========================================================================
# 1.  LOAD INVENTORY
# ===========================================================================

def get_load_inventory():
    """Return list of dicts: transformer name, bus, peak kW, annual kWh."""
    inventory = []
    for tx in ALL_TRANSFORMERS:
        total_kw = sum(
            amps_to_mw(ld["amps"])[0] * 1000.0
            for ld in tx["loads"]
        )
        annual_kwh = total_kw * HOURS_PER_YEAR * LOAD_FACTOR
        inventory.append({
            "tx_name"   : tx["name"],
            "lv_bus"    : tx["lv_bus"],
            "area"      : "Academic" if tx["lv_bus"] < 50 else "Residential",
            "peak_kw"   : round(total_kw, 2),
            "annual_kwh": round(annual_kwh, 0),
        })
    return inventory


# ===========================================================================
# 2.  NET-ZERO SIZING
# ===========================================================================

def net_zero_sizing(inventory):
    """Calculate PV capacity required for annual net-zero energy."""

    total_peak_kw    = sum(b["peak_kw"]    for b in inventory)
    total_annual_kwh = sum(b["annual_kwh"] for b in inventory)

    existing_kw      = sum(p["kw"] for p in SOLAR_PLANTS)
    existing_gen_kwh = existing_kw * HOURS_PER_YEAR * SOLAR_CAPACITY_FACTOR

    deficit_kwh           = max(0.0, total_annual_kwh - existing_gen_kwh)
    additional_kw_needed  = deficit_kwh / (HOURS_PER_YEAR * SOLAR_CAPACITY_FACTOR)
    total_pv_needed_kw    = existing_kw + additional_kw_needed
    energy_independence   = min(100.0, (existing_gen_kwh / total_annual_kwh) * 100.0)

    # Economics
    investment_inr       = additional_kw_needed * SOLAR_CAPEX_INR_PER_KW
    annual_savings_inr   = deficit_kwh * ELECTRICITY_TARIFF_INR_KWH
    annual_opex_inr      = additional_kw_needed * SOLAR_OPEX_INR_PER_KW_YR
    net_annual_saving    = annual_savings_inr - annual_opex_inr
    if net_annual_saving > 0:
        payback_years = investment_inr / net_annual_saving
    else:
        payback_years = 9999.0

    # CO2 (India grid emission factor 0.82 kg CO2/kWh)
    co2_existing_t_yr  = existing_gen_kwh   * GRID_EMISSION_FACTOR / 1000.0
    co2_netzero_t_yr   = (total_pv_needed_kw * HOURS_PER_YEAR *
                          SOLAR_CAPACITY_FACTOR * GRID_EMISSION_FACTOR / 1000.0)
    co2_25yr           = co2_netzero_t_yr * 25.0

    return {
        "total_peak_kw"          : round(total_peak_kw, 2),
        "total_annual_kwh"       : round(total_annual_kwh, 0),
        "existing_pv_kw"         : round(existing_kw, 2),
        "existing_gen_kwh"       : round(existing_gen_kwh, 0),
        "deficit_kwh"            : round(deficit_kwh, 0),
        "additional_pv_kw"       : round(additional_kw_needed, 2),
        "total_pv_needed_kw"     : round(total_pv_needed_kw, 2),
        "energy_independence_pct": round(energy_independence, 1),
        "investment_inr"         : round(investment_inr, 0),
        "annual_savings_inr"     : round(annual_savings_inr, 0),
        "net_annual_saving_inr"  : round(net_annual_saving, 0),
        "payback_years"          : round(payback_years, 1),
        "co2_existing_t_yr"      : round(co2_existing_t_yr, 1),
        "co2_netzero_t_yr"       : round(co2_netzero_t_yr, 1),
        "co2_25yr_netzero_t"     : round(co2_25yr, 0),
    }


# ===========================================================================
# 3.  VOLTAGE SENSITIVITY INDEX (VSI)
# ===========================================================================

def voltage_sensitivity_index():
    """
    Estimate VSI for each load bus.
    Formula: VSI = V^4 - 4*(P*X - Q*R)*V^2 - 4*(P*R + Q*X)^2
    Lower VSI = more voltage-sensitive = better candidate for PV injection.
    This is an approximation; exact values require PSS/E Jacobian.
    """
    results = []
    for tx in ALL_TRANSFORMERS:

        z_pu    = tx["z_pct"] / 100.0
        xr      = tx["xr_ratio"]
        denom   = math.sqrt(1.0 + xr * xr)
        r_pu_tx = z_pu / denom
        x_pu_tx = z_pu * xr / denom

        # Convert to system MVA base
        base_ratio = float(SYSTEM_MVA_BASE) / float(tx["rated_mva"])
        r_pu = r_pu_tx * base_ratio
        x_pu = x_pu_tx * base_ratio

        total_p_mw   = sum(amps_to_mw(ld["amps"])[0] for ld in tx["loads"])
        total_q_mvar = sum(amps_to_mw(ld["amps"])[1] for ld in tx["loads"])
        p_pu = total_p_mw   / float(SYSTEM_MVA_BASE)
        q_pu = total_q_mvar / float(SYSTEM_MVA_BASE)

        v2  = 1.0   # assume V = 1.0 pu at source
        vsi = (v2**2
               - 4.0 * (p_pu * x_pu - q_pu * r_pu) * v2
               - 4.0 * (p_pu * r_pu + q_pu * x_pu)**2)

        results.append({
            "tx_name" : tx["name"],
            "lv_bus"  : tx["lv_bus"],
            "area"    : "Academic" if tx["lv_bus"] < 50 else "Residential",
            "p_mw"    : round(total_p_mw, 3),
            "q_mvar"  : round(total_q_mvar, 3),
            "r_pu"    : round(r_pu, 4),
            "x_pu"    : round(x_pu, 4),
            "vsi"     : round(vsi, 6),
            "priority": "",
            "rank"    : 0,
        })

    # Sort ascending: lowest VSI = highest priority
    results.sort(key=lambda b: b["vsi"])
    for rank, b in enumerate(results, 1):
        b["rank"] = rank
        if rank <= 3:
            b["priority"] = "HIGH"       # was HIGH *** (removed Unicode stars)
        elif rank <= 7:
            b["priority"] = "MEDIUM"
        else:
            b["priority"] = "LOW"

    return results


# ===========================================================================
# 4.  LOSS SENSITIVITY FACTOR (LSF)
# ===========================================================================

def loss_sensitivity_factor():
    """
    LSF = dP_loss / dP_gen_at_bus
    Approximation: LSF_i = 2*(R_i*P_i - X_i*Q_i) / V^2
    Buses with highest LSF benefit most from DG for loss reduction.
    """
    results = []
    for tx in ALL_TRANSFORMERS:

        z_pu    = tx["z_pct"] / 100.0
        xr      = tx["xr_ratio"]
        denom   = math.sqrt(1.0 + xr * xr)
        r_pu_tx = z_pu / denom
        x_pu_tx = z_pu * xr / denom

        base_ratio = float(SYSTEM_MVA_BASE) / float(tx["rated_mva"])
        r_pu = r_pu_tx * base_ratio
        x_pu = x_pu_tx * base_ratio

        total_p_mw   = sum(amps_to_mw(ld["amps"])[0] for ld in tx["loads"])
        total_q_mvar = sum(amps_to_mw(ld["amps"])[1] for ld in tx["loads"])
        p_pu = total_p_mw   / float(SYSTEM_MVA_BASE)
        q_pu = total_q_mvar / float(SYSTEM_MVA_BASE)

        v_sq = 1.0
        lsf  = 2.0 * (r_pu * p_pu / v_sq - x_pu * q_pu / v_sq)

        results.append({
            "tx_name": tx["name"],
            "lv_bus" : tx["lv_bus"],
            "area"   : "Academic" if tx["lv_bus"] < 50 else "Residential",
            "lsf"    : round(lsf, 6),
            "p_mw"   : round(total_p_mw, 3),
            "rank"   : 0,
        })

    results.sort(key=lambda b: b["lsf"], reverse=True)
    for rank, b in enumerate(results, 1):
        b["rank"] = rank
    return results


# ===========================================================================
# 5.  HOSTING CAPACITY ESTIMATION
# ===========================================================================

def hosting_capacity_estimation():
    """
    Maximum PV at each bus before voltage exceeds 1.06 pu.
    Voltage rise formula: dV = P_pv * R / V  (unity PF, Q=0)
    Max P_pv = dV_max * V / R
    dV_max = 0.06 pu  (CEA grid code +/-6% band)
    """
    results = []
    v_nom  = 1.0
    dv_max = 0.06

    for tx in ALL_TRANSFORMERS:

        z_pu    = tx["z_pct"] / 100.0
        xr      = tx["xr_ratio"]
        denom   = math.sqrt(1.0 + xr * xr)
        r_pu_tx = z_pu / denom

        base_ratio = float(SYSTEM_MVA_BASE) / float(tx["rated_mva"])
        r_pu = r_pu_tx * base_ratio

        if r_pu > 0:
            max_pv_pu = (dv_max * v_nom) / r_pu
        else:
            max_pv_pu = 9999.0

        max_pv_kw  = max_pv_pu * float(SYSTEM_MVA_BASE) * 1000.0
        tx_limit_kw = tx["rated_mva"] * 1000.0
        hosting_kw  = min(max_pv_kw, tx_limit_kw)

        results.append({
            "tx_name"      : tx["name"],
            "lv_bus"       : tx["lv_bus"],
            "area"         : "Academic" if tx["lv_bus"] < 50 else "Residential",
            "tx_rated_kva" : tx["rated_mva"] * 1000.0,
            "r_pu"         : round(r_pu, 4),
            "max_pv_v_kw"  : round(max_pv_kw, 1),
            "hosting_kw"   : round(hosting_kw, 1),
        })

    results.sort(key=lambda b: b["hosting_kw"], reverse=True)
    return results


# ===========================================================================
# 6.  EXPORT TO CSV
#     KEY FIX: encoding='utf-8-sig' so Excel opens correctly on Windows
#              and no Unicode symbols in any string value
# ===========================================================================

def export_all(nz, inventory, vsi_list, lsf_list, hc_list):
    """Write all results to separate CSV files."""

    # --- Net-zero sizing -------------------------------------------------
    nz_path = os.path.join(OUTPUT_DIR, "net_zero_sizing.csv")
    with open(nz_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["=== NET-ZERO SIZING ANALYSIS ==="])
        w.writerow(["Parameter", "Value", "Unit"])
        w.writerows([
            ("Campus Peak Load",               nz["total_peak_kw"],          "kW"),
            ("Annual Energy Demand",           nz["total_annual_kwh"],        "kWh/yr"),
            ("Existing PV Capacity",           nz["existing_pv_kw"],          "kW"),
            ("Existing Annual Generation",     nz["existing_gen_kwh"],        "kWh/yr"),
            ("Annual Energy Deficit",          nz["deficit_kwh"],             "kWh/yr"),
            ("Additional PV Required",         nz["additional_pv_kw"],        "kW"),
            ("Total PV for Net-Zero",          nz["total_pv_needed_kw"],      "kW"),
            ("Current Energy Independence",    nz["energy_independence_pct"], "%"),
            ("", "", ""),
            ("=== ECONOMICS ===",              "", ""),
            ("Additional PV Investment",       nz["investment_inr"],          "INR"),
            ("Annual Electricity Savings",     nz["annual_savings_inr"],      "INR/yr"),
            ("Net Annual Saving (after O&M)",  nz["net_annual_saving_inr"],   "INR/yr"),
            ("Simple Payback Period",          nz["payback_years"],           "years"),
            ("", "", ""),
            ("=== ENVIRONMENT ===",            "", ""),
            ("CO2 Avoided (existing PV)",      nz["co2_existing_t_yr"],       "tonnes/yr"),
            ("CO2 Avoided at Net-Zero",        nz["co2_netzero_t_yr"],        "tonnes/yr"),
            ("CO2 Avoided over 25 years",      nz["co2_25yr_netzero_t"],      "tonnes"),
        ])
    print("[CSV] Net-zero sizing    -> " + nz_path)

    # --- Load inventory --------------------------------------------------
    inv_path = os.path.join(OUTPUT_DIR, "load_inventory.csv")
    with open(inv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["Transformer", "LV Bus", "Area", "Peak Load kW", "Annual kWh"])
        for b in inventory:
            w.writerow([b["tx_name"], b["lv_bus"], b["area"],
                        b["peak_kw"], b["annual_kwh"]])
    print("[CSV] Load inventory     -> " + inv_path)

    # --- VSI optimal placement ------------------------------------------
    vsi_path = os.path.join(OUTPUT_DIR, "vsi_pv_placement.csv")
    with open(vsi_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["Rank", "Transformer", "LV Bus", "Area",
                    "P (MW)", "Q (MVAR)", "R (pu)", "X (pu)",
                    "VSI", "Priority"])
        for b in vsi_list:
            w.writerow([b["rank"], b["tx_name"], b["lv_bus"], b["area"],
                        b["p_mw"], b["q_mvar"], b["r_pu"], b["x_pu"],
                        b["vsi"], b["priority"]])
    print("[CSV] VSI PV placement   -> " + vsi_path)

    # --- LSF loss reduction ---------------------------------------------
    lsf_path = os.path.join(OUTPUT_DIR, "lsf_loss_reduction.csv")
    with open(lsf_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["Rank", "Transformer", "LV Bus", "Area", "P (MW)", "LSF"])
        for b in lsf_list:
            w.writerow([b["rank"], b["tx_name"], b["lv_bus"],
                        b["area"], b["p_mw"], b["lsf"]])
    print("[CSV] LSF loss ranking   -> " + lsf_path)

    # --- Hosting capacity -----------------------------------------------
    hc_path = os.path.join(OUTPUT_DIR, "hosting_capacity.csv")
    with open(hc_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(["Transformer", "LV Bus", "Area", "TX Rating kVA",
                    "R (pu sys base)", "Max PV voltage limit kW",
                    "Hosting Capacity kW"])
        for b in hc_list:
            w.writerow([b["tx_name"], b["lv_bus"], b["area"],
                        b["tx_rated_kva"], b["r_pu"],
                        b["max_pv_v_kw"], b["hosting_kw"]])
    print("[CSV] Hosting capacity   -> " + hc_path)


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  CAMPUS NET-ZERO AND GRID IMPACT ANALYSIS")
    print("=" * 60)

    inventory   = get_load_inventory()
    nz          = net_zero_sizing(inventory)
    vsi_list    = voltage_sensitivity_index()
    lsf_list    = loss_sensitivity_factor()
    hc_list     = hosting_capacity_estimation()

    # -----------------------------------------------------------------------
    # CONSOLE OUTPUT (plain ASCII only)
    # -----------------------------------------------------------------------
    print("")
    print("  Campus Peak Demand       : %10.1f kW"    % nz["total_peak_kw"])
    print("  Annual Demand            : %10.0f kWh/yr" % nz["total_annual_kwh"])
    print("  Existing Solar           : %10.1f kW"    % nz["existing_pv_kw"])
    print("  Energy Independence Now  : %9.1f %%"     % nz["energy_independence_pct"])
    print("")
    print("  --- NET-ZERO TARGET ---")
    print("  Additional PV Needed     : %10.1f kW"    % nz["additional_pv_kw"])
    print("  Total PV Required        : %10.1f kW  (%.2f MW)" % (
        nz["total_pv_needed_kw"], nz["total_pv_needed_kw"] / 1000.0))
    print("  Investment (approx)      :  Rs %10.0f"  % nz["investment_inr"])
    print("  Net Annual Savings       :  Rs %10.0f/yr" % nz["net_annual_saving_inr"])
    print("  Simple Payback           : %9.1f years" % nz["payback_years"])
    print("  CO2 Avoided at Net-Zero  : %10.1f tonnes/yr" % nz["co2_netzero_t_yr"])
    print("  CO2 over 25 years        : %10.0f tonnes"    % nz["co2_25yr_netzero_t"])

    print("")
    print("  --- TOP 3 BUSES FOR PV PLACEMENT (by VSI, lowest = highest priority) ---")
    for b in vsi_list[:3]:
        print("  Rank %d: %-22s  Bus %2d  VSI=%.4f  %s" % (
            b["rank"], b["tx_name"], b["lv_bus"], b["vsi"], b["priority"]))

    print("")
    print("  --- TOP 3 BUSES FOR LOSS REDUCTION (by LSF) ---")
    for b in lsf_list[:3]:
        print("  Rank %d: %-22s  Bus %2d  LSF=%.4f  Load=%.3f MW" % (
            b["rank"], b["tx_name"], b["lv_bus"], b["lsf"], b["p_mw"]))

    print("")
    print("  --- HOSTING CAPACITY (TOP 3) ---")
    for b in hc_list[:3]:
        print("  %-22s  Bus %2d  HC = %.0f kW" % (
            b["tx_name"], b["lv_bus"], b["hosting_kw"]))

    print("")
    print("  --- EXPORTING RESULTS ---")
    export_all(nz, inventory, vsi_list, lsf_list, hc_list)

    print("")
    print("  Done. Check psse_output folder.")
    print("=" * 60)
