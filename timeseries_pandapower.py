import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import copy

# ==============================
# LOAD IEEE 33 BUS SYSTEM
# ==============================
net_base = pn.case33bw()
base_load = net_base.load["p_mw"].copy()
base_total_load = base_load.sum()   # ~3.715 MW — system base load

# ==============================
# TIME SERIES PROFILES
# ==============================

# Load profile (per unit of base load)
load_profile = [
    0.6, 0.6, 0.6, 0.6, 0.6, 0.7,   # Hours 0–5
    0.8, 0.9, 1.0, 1.0, 1.0, 1.1,   # Hours 6–11
    1.2, 1.2, 1.1, 1.0, 0.9, 1.1,   # Hours 12–17
    1.2, 1.1, 0.9, 0.8, 0.7, 0.6    # Hours 18–23
]

# PV penetration profile — fraction of BASE total load (3.715 MW)
# 0.0 = 0%, 0.2 = 20%, 0.5 = 50%, 1.0 = 100%, 1.5 = 150%
# Matches the paper's five penetration levels through the day
pv_profile = [
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00,   # Hours 0–5:  Night (0%)
    0.05, 0.20, 0.50, 1.00, 1.30, 1.50,   # Hours 6–11: Ramp up → 150% at hour 11
    1.50, 1.30, 1.00, 0.50, 0.20, 0.05,   # Hours 12–17: Ramp down
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00    # Hours 18–23: Night (0%)
]

# ==============================
# PRE-COMPUTE HOURLY TOTALS
# ==============================
hours = list(range(24))
total_load_mw = [(base_load * load_profile[t]).sum() for t in hours]
total_pv_mw   = [pv_profile[t] * base_total_load       for t in hours]

# ==============================
# CASE 0: BASE CASE — NO PV
# ==============================
net = copy.deepcopy(net_base)
v6_base, v18_base, v33_base = [], [], []

for t in hours:
    net.load["p_mw"] = base_load * load_profile[t]
    pp.runpp(net)
    v6_base.append(net.res_bus.vm_pu[5])    # Bus 6  (0-indexed: 5)
    v18_base.append(net.res_bus.vm_pu[17])  # Bus 18 (0-indexed: 17)
    v33_base.append(net.res_bus.vm_pu[32])  # Bus 33 (0-indexed: 32)

# ==============================
# CASE A: SINGLE PV AT BUS 6
# ==============================
net = copy.deepcopy(net_base)
pv_A = pp.create_sgen(net, bus=5, p_mw=0)  # Bus 6 (0-indexed: 5)
v6_A, v18_A, v33_A = [], [], []

for t in hours:
    net.load["p_mw"] = base_load * load_profile[t]
    net.sgen.at[pv_A, "p_mw"] = pv_profile[t] * base_total_load  # Full penetration at Bus 6
    pp.runpp(net)
    v6_A.append(net.res_bus.vm_pu[5])
    v18_A.append(net.res_bus.vm_pu[17])
    v33_A.append(net.res_bus.vm_pu[32])

# ==============================
# CASE B: MULTI-SITE PV (Bus 6, Bus 18, Bus 30)
# ==============================
net = copy.deepcopy(net_base)
pv_B = [pp.create_sgen(net, bus=b, p_mw=0) for b in [5, 17, 29]]  # Buses 6, 18, 30
v6_B, v18_B, v33_B = [], [], []

for t in hours:
    net.load["p_mw"] = base_load * load_profile[t]
    total_pv_inj = pv_profile[t] * base_total_load
    for p in pv_B:
        net.sgen.at[p, "p_mw"] = total_pv_inj / 3  # Equal split across 3 buses
    pp.runpp(net)
    v6_B.append(net.res_bus.vm_pu[5])
    v18_B.append(net.res_bus.vm_pu[17])
    v33_B.append(net.res_bus.vm_pu[32])

# ==============================
# PLOTTING
# ==============================
fig, axs = plt.subplots(4, 1, figsize=(13, 14), sharex=True)
fig.suptitle("IEEE 33-Bus: Time-Series Voltage Profile and Power Generation", fontsize=13, fontweight='bold')

line_styles = {'No PV': 'k-', 'Single PV': 'k--', 'Multi PV': 'k:'}

# Helper: adds both voltage limit lines to an axis
def add_vlimits(ax):
    ax.axhline(0.95, color='r', linestyle='-.', linewidth=0.9, label='Vmin limit (0.95 p.u.)')
    ax.axhline(1.05, color='b', linestyle='-.', linewidth=0.9, label='Vmax limit (1.05 p.u.)')

# -----------------------------------------------
# PLOT 1: Bus 6 (PV Injection Point — Case A)
# -----------------------------------------------
axs[0].plot(hours, v6_base, 'k-',  linewidth=1.5, label='No PV (Base)')
axs[0].plot(hours, v6_A,    'k--', linewidth=1.5, label='Case A: Single PV (Bus 6)')
axs[0].plot(hours, v6_B,    'k:',  linewidth=1.5, label='Case B: Multi PV (Bus 6+18+30)')
add_vlimits(axs[0])
axs[0].set_title('Bus 6  —  PV Injection Point (Case A)')
axs[0].set_ylabel('Voltage (p.u.)')
axs[0].legend(loc='lower right', fontsize=8)
axs[0].grid(True, alpha=0.4)
axs[0].set_ylim(0.88, 1.08)

# -----------------------------------------------
# PLOT 2: Bus 18 (Weakest Bus / Mid-Feeder)
# -----------------------------------------------
axs[1].plot(hours, v18_base, 'k-',  linewidth=1.5, label='No PV (Base)')
axs[1].plot(hours, v18_A,    'k--', linewidth=1.5, label='Case A: Single PV (Bus 6)')
axs[1].plot(hours, v18_B,    'k:',  linewidth=1.5, label='Case B: Multi PV (Bus 6+18+30)')
add_vlimits(axs[1])
axs[1].set_title('Bus 18  —  Weakest Bus / Mid-Feeder (PV Injection Point — Case B)')
axs[1].set_ylabel('Voltage (p.u.)')
axs[1].legend(loc='lower right', fontsize=8)
axs[1].grid(True, alpha=0.4)
axs[1].set_ylim(0.88, 1.10)

# -----------------------------------------------
# PLOT 3: Bus 33 (End of Feeder)
# -----------------------------------------------
axs[2].plot(hours, v33_base, 'k-',  linewidth=1.5, label='No PV (Base)')
axs[2].plot(hours, v33_A,    'k--', linewidth=1.5, label='Case A: Single PV (Bus 6)')
axs[2].plot(hours, v33_B,    'k:',  linewidth=1.5, label='Case B: Multi PV (Bus 6+18+30)')
add_vlimits(axs[2])
axs[2].set_title('Bus 33  —  End of Feeder')
axs[2].set_ylabel('Voltage (p.u.)')
axs[2].legend(loc='lower right', fontsize=8)
axs[2].grid(True, alpha=0.4)
axs[2].set_ylim(0.88, 1.08)

# -----------------------------------------------
# PLOT 4: Load and PV Generation (combined)
# -----------------------------------------------
axs[3].plot(hours, total_load_mw, 'k-o',  linewidth=1.5, markersize=4, label='System Load (MW)')
axs[3].plot(hours, total_pv_mw,   'k--s', linewidth=1.5, markersize=4, label='PV Generation (MW)')
axs[3].fill_between(hours, 0, total_load_mw, alpha=0.08, color='blue')
axs[3].fill_between(hours, 0, total_pv_mw,   alpha=0.15, color='orange')

# Mark where PV exceeds load (reverse flow zone)
pv_arr   = [total_pv_mw[t]   for t in hours]
load_arr = [total_load_mw[t] for t in hours]
axs[3].fill_between(hours, load_arr, pv_arr,
                    where=[pv_arr[t] > load_arr[t] for t in hours],
                    alpha=0.25, color='red', label='Reverse Flow Zone (PV > Load)')

axs[3].set_title('System Load and PV Generation Profile (PV penetration: 0% → 150% → 0%)')
axs[3].set_xlabel('Hour of Day')
axs[3].set_ylabel('Power (MW)')
axs[3].legend(loc='upper left', fontsize=8)
axs[3].grid(True, alpha=0.4)

# X-axis ticks
axs[3].set_xticks(range(0, 24, 2))
axs[3].set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], rotation=30, ha='right')

plt.tight_layout()
plt.savefig(r"C:\Users\Shubh\Desktop\solar_data\timeseries_voltage_profile.png", dpi=150, bbox_inches='tight')
plt.show()
print("Done. Plot saved.")