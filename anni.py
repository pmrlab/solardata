import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# RENEWABLE ENERGY + HYDROGEN STORAGE SIMULATION
# B.Tech Project
# ============================================================

# -----------------------------
# 1. TIME (24 HOURS)
# -----------------------------
hours = np.arange(24)

# -----------------------------
# 2. SOLAR POWER PROFILE (kW)
# -----------------------------
solar_power = np.array([
    0, 0, 0, 0, 0,
    1, 2, 4, 6, 8,
    10, 12, 13, 12, 10,
    8, 6, 4, 2, 1,
    0, 0, 0, 0
])

# -----------------------------
# 3. LOAD DEMAND PROFILE (kW)
# -----------------------------
load_demand = np.array([
    5, 5, 5, 5, 5,
    6, 7, 8, 9, 10,
    11, 12, 12, 11, 10,
    9, 8, 7, 6, 6,
    5, 5, 5, 5
])

# ============================================================
# 4. SYSTEM PARAMETERS
# ============================================================

electrolyzer_efficiency = 0.70
fuel_cell_efficiency = 0.60

# Hydrogen storage tank capacity
max_hydrogen_storage = 50

# Initial hydrogen storage
stored_hydrogen = 0

# ============================================================
# 5. VARIABLES FOR RESULTS
# ============================================================

hydrogen_storage_history = []
fuel_cell_output_history = []
hydrogen_production_history = []
unused_solar_history = []
grid_deficit_history = []
net_power_history = []

# ============================================================
# 6. MAIN SIMULATION LOOP
# ============================================================

for hour in range(24):

    # Current solar and load
    solar = solar_power[hour]
    load = load_demand[hour]

    # Net power
    net_power = solar - load

    # Save net power
    net_power_history.append(net_power)

    # ========================================================
    # CASE 1: EXCESS SOLAR POWER AVAILABLE
    # ========================================================

    if net_power > 0:

        # Hydrogen produced
        hydrogen_produced = (
            net_power * electrolyzer_efficiency
        )

        # Check tank capacity
        available_space = (
            max_hydrogen_storage - stored_hydrogen
        )

        # Actual hydrogen stored
        hydrogen_stored = min(
            hydrogen_produced,
            available_space
        )

        # Update storage
        stored_hydrogen += hydrogen_stored

        # No fuel cell needed
        fuel_cell_output = 0

        # Unused solar if tank full
        unused_solar = (
            hydrogen_produced - hydrogen_stored
        )

        # No deficit
        grid_deficit = 0

    # ========================================================
    # CASE 2: POWER DEFICIT
    # ========================================================

    else:

        # Required power
        deficit = abs(net_power)

        # Max power from fuel cell
        available_fuelcell_power = (
            stored_hydrogen * fuel_cell_efficiency
        )

        # Actual fuel cell output
        fuel_cell_output = min(
            deficit,
            available_fuelcell_power
        )

        # Hydrogen consumed
        hydrogen_used = (
            fuel_cell_output / fuel_cell_efficiency
        )

        # Update storage
        stored_hydrogen -= hydrogen_used

        # No hydrogen production
        hydrogen_produced = 0

        # No unused solar
        unused_solar = 0

        # Remaining deficit from grid
        grid_deficit = deficit - fuel_cell_output

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    hydrogen_storage_history.append(stored_hydrogen)

    fuel_cell_output_history.append(fuel_cell_output)

    hydrogen_production_history.append(hydrogen_produced)

    unused_solar_history.append(unused_solar)

    grid_deficit_history.append(grid_deficit)

# ============================================================
# 7. CREATE RESULTS TABLE
# ============================================================

results = pd.DataFrame({
    'Hour': hours,
    'Solar Power (kW)': solar_power,
    'Load Demand (kW)': load_demand,
    'Net Power (kW)': net_power_history,
    'Hydrogen Produced': hydrogen_production_history,
    'Stored Hydrogen': hydrogen_storage_history,
    'Fuel Cell Output': fuel_cell_output_history,
    'Grid Deficit': grid_deficit_history
})

# ============================================================
# 8. DISPLAY RESULTS TABLE
# ============================================================

print("\n================================================")
print("SIMULATION RESULTS")
print("================================================\n")

print(results)

# ============================================================
# 9. PERFORMANCE CALCULATIONS
# ============================================================

total_solar_energy = np.sum(solar_power)

total_load_energy = np.sum(load_demand)

total_hydrogen_produced = np.sum(
    hydrogen_production_history
)

total_fuelcell_output = np.sum(
    fuel_cell_output_history
)

total_grid_deficit = np.sum(
    grid_deficit_history
)

renewable_utilization = (
    (
        total_load_energy - total_grid_deficit
    )
    /
    total_load_energy
) * 100

# Simple CO2 reduction estimate
# Assume 0.82 kg CO2 per kWh grid electricity

co2_saved = (
    total_fuelcell_output * 0.82
)

# ============================================================
# 10. PRINT PERFORMANCE SUMMARY
# ============================================================

print("\n================================================")
print("SYSTEM PERFORMANCE")
print("================================================\n")

print(f"Total Solar Energy Generated : "
      f"{total_solar_energy:.2f} kWh")

print(f"Total Load Demand            : "
      f"{total_load_energy:.2f} kWh")

print(f"Total Hydrogen Produced      : "
      f"{total_hydrogen_produced:.2f}")

print(f"Total Fuel Cell Output       : "
      f"{total_fuelcell_output:.2f} kWh")

print(f"Total Grid Deficit           : "
      f"{total_grid_deficit:.2f} kWh")

print(f"Renewable Utilization        : "
      f"{renewable_utilization:.2f}%")

print(f"Estimated CO2 Saved          : "
      f"{co2_saved:.2f} kg CO2")

# ============================================================
# 11. PLOT 1
# SOLAR VS LOAD
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    hours,
    solar_power,
    marker='o',
    linewidth=2,
    label='Solar Power'
)

plt.plot(
    hours,
    load_demand,
    marker='s',
    linewidth=2,
    label='Load Demand'
)

plt.xlabel('Hour')
plt.ylabel('Power (kW)')
plt.title('Solar Generation vs Load Demand')
plt.grid(True)
plt.legend()

plt.show()

# ============================================================
# 12. PLOT 2
# HYDROGEN STORAGE
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    hours,
    hydrogen_storage_history,
    marker='o',
    linewidth=2,
    label='Stored Hydrogen'
)

plt.xlabel('Hour')
plt.ylabel('Hydrogen Level')
plt.title('Hydrogen Storage Over Time')
plt.grid(True)
plt.legend()

plt.show()

# ============================================================
# 13. PLOT 3
# FUEL CELL OUTPUT
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    hours,
    fuel_cell_output_history
)

plt.xlabel('Hour')
plt.ylabel('Power (kW)')
plt.title('Fuel Cell Power Output')
plt.grid(True)

plt.show()

# ============================================================
# 14. PLOT 4
# GRID DEFICIT
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    hours,
    grid_deficit_history
)

plt.xlabel('Hour')
plt.ylabel('Deficit Power (kW)')
plt.title('Remaining Grid Deficit')
plt.grid(True)

plt.show()

# ============================================================
# 15. FINAL MESSAGE
# ============================================================

print("\n================================================")
print("SIMULATION COMPLETED SUCCESSFULLY")
print("================================================")

print("\nProject Conclusion:")
print("Hydrogen storage helps utilize excess renewable")
print("energy and improves system reliability by")
print("supplying electricity during deficit periods.")