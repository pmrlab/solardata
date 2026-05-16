# -*- coding: utf-8 -*-
"""
campus_data.py  -  Central data for campus power system.
All strings ASCII-safe. Compatible with Python 2.7 (PSSE 33).
"""

import math

SYSTEM_MVA_BASE = 100.0
POWER_FACTOR    = 0.85
VOLTAGE_LV      = 0.4

def amps_to_mw(amps, kv=None, pf=None):
    if kv is None:
        kv = VOLTAGE_LV
    if pf is None:
        pf = POWER_FACTOR
    s_mva  = math.sqrt(3.0) * kv * (amps / 1000.0)
    p_mw   = s_mva * pf
    q_mvar = s_mva * math.sqrt(1.0 - pf * pf)
    return round(p_mw, 4), round(q_mvar, 4)

GRID_BUS = {"bus_no":1,"name":"GRID_33KV","base_kv":33.0,"bus_type":3,
            "area":1,"zone":1,"v_pu":1.00,"angle":0.0,"v_max":1.05,"v_min":0.95}

MAIN_11KV_BUSES = [
    {"bus_no":2,"name":"ACAD_11KV","base_kv":11.0,"bus_type":1,"area":1,"zone":1,"v_pu":1.00,"v_max":1.06,"v_min":0.94},
    {"bus_no":3,"name":"RESI_11KV","base_kv":11.0,"bus_type":1,"area":2,"zone":2,"v_pu":1.00,"v_max":1.06,"v_min":0.94},
]

MAIN_TRANSFORMERS = [
    {"tx_id":"MTX_01","name":"ACAD_MAIN_TX","hv_bus":1,"lv_bus":2,"rated_mva":5.0,"hv_kv":33.0,"lv_kv":11.0,"z_pct":7.5,"xr_ratio":15.0},
    {"tx_id":"MTX_02","name":"RESI_MAIN_TX","hv_bus":1,"lv_bus":3,"rated_mva":5.0,"hv_kv":33.0,"lv_kv":11.0,"z_pct":7.5,"xr_ratio":15.0},
]

ACADEMIC_TRANSFORMERS = [
    {"tx_id":"TX_A01","name":"EE_DEPT",   "hv_bus":2,"lv_bus":10,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":800,
     "loads":[{"name":"EE_Main","amps":400},{"name":"EE_Labs","amps":250},{"name":"EE_Wksp","amps":100}]},
    {"tx_id":"TX_A02","name":"MECH_DEPT", "hv_bus":2,"lv_bus":11,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":800,
     "loads":[{"name":"Mech_Main","amps":400},{"name":"Mech_Wksp","amps":250},{"name":"Hydraulics","amps":100}]},
    {"tx_id":"TX_A03","name":"CS_DEPT",   "hv_bus":2,"lv_bus":12,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":800,
     "loads":[{"name":"CS_Main","amps":400},{"name":"CS_Labs","amps":250},{"name":"Infra","amps":100}]},
    {"tx_id":"TX_A04","name":"ECE_DEPT",  "hv_bus":2,"lv_bus":13,"rated_mva":0.250,"hv_kv":11.0,"lv_kv":0.4,"z_pct":4.0,"xr_ratio":5.0,"feeder_amps":400,
     "loads":[{"name":"ECE_Main","amps":200},{"name":"ECE_Labs","amps":150}]},
    {"tx_id":"TX_A05","name":"LIBRARY",   "hv_bus":2,"lv_bus":14,"rated_mva":0.250,"hv_kv":11.0,"lv_kv":0.4,"z_pct":4.0,"xr_ratio":5.0,"feeder_amps":400,
     "loads":[{"name":"Library","amps":200},{"name":"Lib_AC","amps":150}]},
    {"tx_id":"TX_A06","name":"ADMIN_BLK", "hv_bus":2,"lv_bus":15,"rated_mva":0.315,"hv_kv":11.0,"lv_kv":0.4,"z_pct":4.0,"xr_ratio":5.0,"feeder_amps":600,
     "loads":[{"name":"Admin","amps":300},{"name":"Admin_UPS","amps":200}]},
]

RESIDENTIAL_TRANSFORMERS = [
    {"tx_id":"TX_R01","name":"CTYPE_QTR",   "hv_bus":3,"lv_bus":50,"rated_mva":0.250,"hv_kv":11.0,"lv_kv":0.4,"z_pct":4.0,"xr_ratio":5.0,"feeder_amps":600,
     "loads":[{"name":"H_Type_H1","amps":250},{"name":"CType_MHS","amps":250},{"name":"H_Type_H41","amps":250}]},
    {"tx_id":"TX_R02","name":"AROBINDO_H1", "hv_bus":3,"lv_bus":51,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":1000,
     "loads":[{"name":"C_Block","amps":400},{"name":"Emergency","amps":200},{"name":"A_Block","amps":200},{"name":"C_Blk2","amps":200},{"name":"A_Blk2","amps":630}]},
    {"tx_id":"TX_R03","name":"HOSTEL_7",    "hv_bus":3,"lv_bus":52,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":800,
     "loads":[{"name":"Hostel1","amps":250},{"name":"Hostel2","amps":250},{"name":"Hostel3","amps":250}]},
    {"tx_id":"TX_R04","name":"VINODINI_H1", "hv_bus":3,"lv_bus":53,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":1000,
     "loads":[{"name":"AMF_OUT","amps":400},{"name":"SCADA","amps":250},{"name":"Girls_H","amps":630}]},
    {"tx_id":"TX_R05","name":"AROBINDO_H2", "hv_bus":3,"lv_bus":54,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":1000,
     "loads":[{"name":"G_Block","amps":630},{"name":"E_Block","amps":630},{"name":"Hostel6","amps":200},{"name":"E_Blk2","amps":400}]},
    {"tx_id":"TX_R06","name":"SHOPPING",    "hv_bus":3,"lv_bus":55,"rated_mva":0.250,"hv_kv":11.0,"lv_kv":0.4,"z_pct":4.0,"xr_ratio":5.0,"feeder_amps":600,
     "loads":[{"name":"Shop1","amps":250},{"name":"Shop2","amps":250},{"name":"Shop3","amps":250}]},
    {"tx_id":"TX_R07","name":"VINODINI_H2", "hv_bus":3,"lv_bus":56,"rated_mva":0.500,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.0,"xr_ratio":6.0,"feeder_amps":1000,
     "loads":[{"name":"LT_Load","amps":630},{"name":"APF","amps":400},{"name":"Internal","amps":400},{"name":"Gargi_H","amps":250}]},
    {"tx_id":"TX_R08","name":"AACHARYA_BH1","hv_bus":3,"lv_bus":57,"rated_mva":1.000,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.5,"xr_ratio":8.0,"feeder_amps":1600,
     "loads":[{"name":"APFC","amps":400},{"name":"Neelam","amps":400},{"name":"Gomed","amps":400},{"name":"Pukhraj","amps":630}]},
    {"tx_id":"TX_R09","name":"STAFF_GATE",  "hv_bus":3,"lv_bus":58,"rated_mva":0.315,"hv_kv":11.0,"lv_kv":0.4,"z_pct":4.0,"xr_ratio":5.0,"feeder_amps":600,
     "loads":[{"name":"Gate1","amps":250},{"name":"Gate2","amps":250},{"name":"Gate3","amps":250},{"name":"Gate4","amps":250}]},
    {"tx_id":"TX_R10","name":"AACHARYA_BH2","hv_bus":3,"lv_bus":59,"rated_mva":1.000,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.5,"xr_ratio":8.0,"feeder_amps":1600,
     "loads":[{"name":"AB2_Ld1","amps":630},{"name":"AB2_Ld2","amps":630},{"name":"AB2_Ld3","amps":400},{"name":"AB2_Ld4","amps":400}]},
    {"tx_id":"TX_R11","name":"AACHARYA_BH3","hv_bus":3,"lv_bus":60,"rated_mva":1.000,"hv_kv":11.0,"lv_kv":0.4,"z_pct":5.5,"xr_ratio":8.0,"feeder_amps":1600,
     "loads":[{"name":"Manakya","amps":400},{"name":"Moti","amps":400},{"name":"Moonga","amps":400},{"name":"Panna","amps":630}]},
]

ALL_TRANSFORMERS = ACADEMIC_TRANSFORMERS + RESIDENTIAL_TRANSFORMERS

SOLAR_PLANTS = [
    {"plant_id":"PV_A01","lv_bus":10,"name":"Solar_EE",      "kw":50.0,  "pf":1.0},
    {"plant_id":"PV_A02","lv_bus":12,"name":"Solar_CS",       "kw":50.0,  "pf":1.0},
    {"plant_id":"PV_A03","lv_bus":14,"name":"Solar_Library",  "kw":100.0, "pf":1.0},
    {"plant_id":"PV_R01","lv_bus":51,"name":"Solar_Arobindo1","kw":100.0, "pf":1.0},
    {"plant_id":"PV_R02","lv_bus":53,"name":"Solar_Vinodini1","kw":50.0,  "pf":1.0},
    {"plant_id":"PV_R03","lv_bus":57,"name":"Solar_Aacharya1","kw":50.0,  "pf":1.0},
]

SOLAR_CAPACITY_FACTOR = 0.19
GRID_EMISSION_FACTOR  = 0.82

SCENARIOS = {
    "S1_BASE"    : {"solar_scale":0.0, "load_scale":0.75, "desc":"No solar, avg load"},
    "S2_PK_SOLAR": {"solar_scale":1.0, "load_scale":0.40, "desc":"Peak solar, min load"},
    "S3_PK_LOAD" : {"solar_scale":0.6, "load_scale":1.00, "desc":"Peak load, partial solar"},
    "S4_NIGHT"   : {"solar_scale":0.0, "load_scale":0.85, "desc":"Night, zero solar"},
    "S5_NET_ZERO": {"solar_scale":1.0, "load_scale":0.75, "desc":"Net-zero verify"},
    "S6_OVERGEN" : {"solar_scale":1.2, "load_scale":0.40, "desc":"Over-gen reverse flow"},
}
