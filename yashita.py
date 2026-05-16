import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# -----------------------------
# 24-Hour Time Axis
# -----------------------------
hours = np.arange(0, 24)

# -----------------------------
# STEP 0 : Original Residential Load Profile (kW)
# -----------------------------
# Simulated residential demand curve
base_load = np.array([
    1.2, 1.1, 1.0, 0.9, 0.9, 1.1,
    1.8, 2.5, 3.0, 2.7, 2.3, 2.0,
    1.9, 1.8, 1.9, 2.1, 2.5, 3.2,
    4.0, 4.5, 4.2, 3.5, 2.5, 1.8
])

# -----------------------------
# STEP 1 : Demand Reduction
# -----------------------------
# Assume:
# - Efficient appliances reduce load by 15%
# - Peak shaving during evening hours

reduced_load = base_load.copy()

# Overall reduction
reduced_load = reduced_load * 0.85

# Additional peak shaving from 6 PM to 10 PM
reduced_load[18:22] *= 0.90

# -----------------------------
# STEP 2 : Solar PV Integration
# -----------------------------
# Simulated rooftop solar generation profile

solar_generation = np.array([
    0, 0, 0, 0, 0, 0,
    0.3, 0.8, 1.5, 2.5, 3.2, 3.8,
    4.0, 3.7, 3.0, 2.2, 1.2, 0.5,
    0, 0, 0, 0, 0, 0
])

# Net load after solar integration
net_load = reduced_load - solar_generation

# Avoid negative demand
net_load = np.maximum(net_load, 0)

# -----------------------------
# Energy Calculations
# -----------------------------
# Since interval = 1 hour
base_energy = np.sum(base_load)
reduced_energy = np.sum(reduced_load)
net_energy = np.sum(net_load)

# Peak Demand
base_peak = np.max(base_load)
reduced_peak = np.max(reduced_load)
net_peak = np.max(net_load)

# -----------------------------
# CO2 Emission Calculation
# -----------------------------
# Assume emission factor = 0.82 kg CO2 per kWh

emission_factor = 0.82

base_co2 = base_energy * emission_factor
net_co2 = net_energy * emission_factor

co2_reduction = base_co2 - net_co2

# -----------------------------
# Display Results
# -----------------------------
print("\n========== RESULTS ==========\n")

print(f"Base Energy Consumption      : {base_energy:.2f} kWh")
print(f"Reduced Energy Consumption   : {reduced_energy:.2f} kWh")
print(f"Net Grid Energy Consumption  : {net_energy:.2f} kWh\n")

print(f"Base Peak Demand             : {base_peak:.2f} kW")
print(f"Reduced Peak Demand          : {reduced_peak:.2f} kW")
print(f"Net Peak Demand              : {net_peak:.2f} kW\n")

print(f"CO2 Emission Before          : {base_co2:.2f} kg")
print(f"CO2 Emission After           : {net_co2:.2f} kg")
print(f"CO2 Reduction                : {co2_reduction:.2f} kg")

# -----------------------------
# Create Data Table
# -----------------------------
data = pd.DataFrame({
    'Hour': hours,
    'Base Load (kW)': base_load,
    'Reduced Load (kW)': reduced_load,
    'Solar Generation (kW)': solar_generation,
    'Net Grid Load (kW)': net_load
})

print("\n")
print(data)

# -----------------------------
# Plot 1 : Load Curves
# -----------------------------
plt.figure(figsize=(12,6))

plt.plot(hours, base_load,
         marker='o',
         linewidth=2,
         label='Base Load')

plt.plot(hours, reduced_load,
         marker='s',
         linewidth=2,
         label='After Demand Reduction')

plt.plot(hours, net_load,
         marker='^',
         linewidth=2,
         label='After Solar Integration')

plt.plot(hours, solar_generation,
         linestyle='--',
         linewidth=2,
         label='Solar Generation')

plt.xlabel('Time (Hours)')
plt.ylabel('Power (kW)')
plt.title('Residential Load Demand Reduction')
plt.xticks(hours)
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# -----------------------------
# Plot 2 : Energy Comparison
# -----------------------------
plt.figure(figsize=(8,5))

cases = ['Base Load', 'Reduced Load', 'Net Grid Load']
energy_values = [base_energy, reduced_energy, net_energy]

plt.bar(cases, energy_values)

plt.ylabel('Energy Consumption (kWh)')
plt.title('Daily Energy Consumption Comparison')

plt.tight_layout()
plt.show()

# -----------------------------
# Plot 3 : Peak Demand Comparison
# -----------------------------
plt.figure(figsize=(8,5))

peak_values = [base_peak, reduced_peak, net_peak]

plt.bar(cases, peak_values)

plt.ylabel('Peak Demand (kW)')
plt.title('Peak Demand Comparison')

plt.tight_layout()
plt.show()