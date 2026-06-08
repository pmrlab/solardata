"""
ev_module.py  —  EV Transport Hub for SolUrja (PMR Lab, MNIT Jaipur)
Generates the full HTML/JS block for the EV Transport sub-page.
Import this in combine.py and call  get_ev_html()  to get the string.
"""

# ──────────────────────────────────────────────────
# MNIT JAIPUR EV CHARGING POINTS DATABASE
# Add / remove / edit stations here as needed.
# ──────────────────────────────────────────────────
MNIT_EV_STATIONS = [
    {"id":"s1","name":"Electric Vehicle Charging Station","lat":26.858782936340187,"lng":75.81297489755812,"solar_powered":False,"maps_link":"https://www.google.com/maps/place/Electric+Vehicle+Charging+Station/@26.8588724,75.8125883,19.34z","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"24/7"},
    {"id":"s2","name":"Adani Charging Station","lat":26.857334964734907,"lng":75.8155430826787,"solar_powered":False,"maps_link":"https://www.google.com/maps/place/Adani+Charging+Station/@26.8574308,75.815548,20.7z","connectors":["CCS2","Type-2"],"chargers":3,"available":2,"kw":"22 kW AC","hours":"24/7"},
    {"id":"s3","name":"Sustainable Energy Materials & Systems Station","lat":26.859378674913735,"lng":75.8111109247328,"solar_powered":False,"maps_link":"https://www.google.com/maps/place/Sustainable+Energy+Materials+%26+Systems+(SEMS)+Lab","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"9 AM – 6 PM"},
    {"id":"s4","name":"Electrical Engineering Department Station","lat":26.86176205796383,"lng":75.80995462040451,"solar_powered":True,"maps_link":"https://www.google.com/maps/place/MNIT+Electrical+Engineering+Department/@26.8619413,75.8108501","connectors":["CCS2","Type-2"],"chargers":3,"available":3,"kw":"22 kW AC","hours":"24/7"},
    {"id":"s5","name":"Civil Engineering Department Station","lat":26.861200375555676,"lng":75.80903228766958,"solar_powered":False,"maps_link":"https://www.google.com/maps/@26.8615459,75.8090009,18.26z","connectors":["Type-2"],"chargers":2,"available":1,"kw":"7.4 kW AC","hours":"8 AM – 8 PM"},
    {"id":"s6","name":"Department of Metallurgy & Physics Station","lat":26.862213629222754,"lng":75.81017984362397,"solar_powered":False,"maps_link":"https://www.google.com/maps/place/Department+of+Metallurgy+%26+Physics/@26.8619814,75.8102602","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"9 AM – 6 PM"},
    {"id":"s7","name":"Prabha Bhawan Parking Station","lat":26.863618852785738,"lng":75.81121442103036,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8639295,75.8110533,19.68z","connectors":["CCS2","Type-2"],"chargers":4,"available":3,"kw":"22 kW AC","hours":"24/7"},
    {"id":"s8","name":"MNIT Shopping Centre Station","lat":26.864231285598372,"lng":75.81306143249138,"solar_powered":False,"maps_link":"https://www.google.com/maps/@26.8646837,75.8123253,17.89z","connectors":["Type-2","Bharat AC-001"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"8 AM – 10 PM"},
    {"id":"s9","name":"Aurobindo Hostel Rd Station","lat":26.862915249369145,"lng":75.8172815568426,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8625085,75.8165413,17z","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"24/7"},
    {"id":"s10","name":"Aravali Hostel Station","lat":26.859996035176835,"lng":75.82039290095058,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8615992,75.819202,17z","connectors":["Type-2","Bharat AC-001"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"24/7"},
    {"id":"s11","name":"Aurobindo Hostel Station","lat":26.862149561809627,"lng":75.81969554054798,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8627286,75.8193737,17z","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"24/7"},
    {"id":"s12","name":"Hostel 5 Station","lat":26.860761227346956,"lng":75.81748240109951,"solar_powered":False,"maps_link":"https://www.google.com/maps/place/26%C2%B051'38.2%22N+75%C2%B049'02.8%22E/@26.8609766,75.8174824,17z","connectors":["Bharat AC-001"],"chargers":2,"available":1,"kw":"7.4 kW AC","hours":"6 AM – 11 PM"},
    {"id":"s13","name":"Sports Complex Station","lat":26.86190683899826,"lng":75.81384160799908,"solar_powered":False,"maps_link":"https://www.google.com/maps/@26.8617476,75.8139184,18.25z","connectors":["Type-2","Bharat AC-001"],"chargers":3,"available":3,"kw":"7.4 kW AC","hours":"6 AM – 11 PM"},
    {"id":"s14","name":"VLTC Station","lat":26.8629286,"lng":75.8143792,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8629286,75.8143792,18.25z","connectors":["CCS2","Type-2"],"chargers":3,"available":2,"kw":"22 kW AC","hours":"24/7"},
    {"id":"s15","name":"Vinodini Hostel Station","lat":26.864268653820066,"lng":75.81540933325957,"solar_powered":False,"maps_link":"https://www.google.com/maps/@26.8645125,75.8143295,18.25z","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"7 AM – 10 PM"},
    {"id":"s16","name":"Department of Electronics & Communication Station","lat":26.86315122254952,"lng":75.81133554904177,"solar_powered":False,"maps_link":"https://www.google.com/maps/@26.8631815,75.8105934,18.04z","connectors":["Type-2"],"chargers":2,"available":1,"kw":"7.4 kW AC","hours":"9 AM – 6 PM"},
    {"id":"s17","name":"Acharya Bhawan Station","lat":26.8652023,"lng":75.818601,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8652023,75.818601,19.38z","connectors":["CCS2","Type-2"],"chargers":3,"available":3,"kw":"22 kW AC","hours":"24/7"},
    {"id":"s18","name":"Guest House Station","lat":26.865873817296034,"lng":75.81054762551767,"solar_powered":True,"maps_link":"https://www.google.com/maps/@26.8648359,75.8130228,17.3z","connectors":["Type-2"],"chargers":2,"available":2,"kw":"7.4 kW AC","hours":"24/7"},
]
# ──────────────────────────────────────────────────
# KEY CAMPUS LANDMARKS (used in trip planner)
# ──────────────────────────────────────────────────
MNIT_LANDMARKS = [
    {"name": "Main Gate",               "lat": 26.8651, "lng": 75.8116},
    {"name": "Library",                 "lat": 26.8630, "lng": 75.8140},
    {"name": "Central Cafeteria",       "lat": 26.8638, "lng": 75.8148},
    {"name": "Electrical Department",   "lat": 26.8639, "lng": 75.8141},
    {"name": "Computer Science Dept",   "lat": 26.8625, "lng": 75.8152},
    {"name": "MIIC Building",           "lat": 26.8632, "lng": 75.8160},
    {"name": "Prabha Bhawan",           "lat": 26.8618, "lng": 75.8170},
    {"name": "Sports Complex",          "lat": 26.8644, "lng": 75.8128},
    {"name": "Boys Hostel Block A",     "lat": 26.8610, "lng": 75.8135},
    {"name": "Girls Hostel",            "lat": 26.8608, "lng": 75.8155},
    {"name": "Admin Block",             "lat": 26.8648, "lng": 75.8138},
    {"name": "Mechanical Dept",         "lat": 26.8622, "lng": 75.8145},
]

def get_ev_html() -> str:
    """
    Returns the complete HTML string for the EV Transport Hub section.
    Plug the returned string directly into the __EV_TRANSPORT_HTML__
    placeholder inside your HTML_TEMPLATE in combine.py.
    """
    import json
    import base64, os
    img_path = os.path.join(os.path.dirname(__file__), "assets", "ev_bg.jpg")
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    img_data_url = f"data:image/jpeg;base64,{img_b64}"

    stations_json = json.dumps(MNIT_EV_STATIONS)
    landmarks_json = json.dumps(MNIT_LANDMARKS)

    total_chargers  = sum(s["chargers"]  for s in MNIT_EV_STATIONS)
    total_available = sum(s["available"] for s in MNIT_EV_STATIONS)
    total_stations  = len(MNIT_EV_STATIONS)
    solar_stations  = sum(1 for s in MNIT_EV_STATIONS if s["solar_powered"])

    # Pre-build station cards HTML (server-side, no JS needed for list)
    station_cards_html = ""
    for s in MNIT_EV_STATIONS:
        avail_color = "#22C55E" if s["available"] > 0 else "#EF4444"
        avail_text  = f"{s['available']}/{s['chargers']} Available" if s["available"] > 0 else "Currently Full"
        solar_badge = '<span class="ev-tag solar">☀️ Solar</span>' if s["solar_powered"] else ""
        tags_html   = ""
        conn_html   = "".join(f'<span class="ev-conn">{c}</span>' for c in s["connectors"])

        station_cards_html += f"""
        <div class="ev-station-card" data-id="{s['id']}" data-lat="{s['lat']}" data-lng="{s['lng']}"
             onclick="focusStation('{s['id']}', {s['lat']}, {s['lng']})">
          <div class="ev-sc-header">
            <div>
              <div class="ev-sc-name">{s['name']}</div>
            </div>
            <div class="ev-avail-badge" style="background:{avail_color}20;color:{avail_color};border:1.5px solid {avail_color}40;">
              <span class="ev-avail-dot" style="background:{avail_color}"></span>
              {avail_text}
            </div>
          </div>
          <div class="ev-sc-meta">
            <span>⚡ {s['kw']}</span>
            <span>🕐 {s['hours']}</span>
          </div>
          <div class="ev-sc-connectors">{conn_html}</div>
          <div class="ev-sc-tags">{solar_badge}</div>
          <div class="ev-sc-actions">
            <button class="ev-act-btn primary" onclick="event.stopPropagation();window.open('{s['maps_link']}','_blank')">
              📍 View on Maps
            </button>
            <button class="ev-act-btn" onclick="event.stopPropagation();openStreetView({s['lat']},{s['lng']})">
              🌐 Street View
            </button>
            <button class="ev-act-btn" onclick="event.stopPropagation();addToTrip('{s['id']}','{s['name']}')">
              ➕ Add to Trip
            </button>
          </div>
        </div>
        """

    # Landmark options for trip planner dropdowns
    landmark_opts = "".join(
        f'<option value="{lm["lat"]},{lm["lng"]}">{lm["name"]}</option>'
        for lm in MNIT_LANDMARKS
    )
    station_opts = "".join(
        f'<option value="{s["lat"]},{s["lng"]}">{s["name"]}</option>'
        for s in MNIT_EV_STATIONS
    )

    html = f"""
<!-- ══════════════════════════════════════════════════════════ -->
<!--  EV TRANSPORT HUB  (generated by ev_module.py)           -->
<!-- ══════════════════════════════════════════════════════════ -->

<style>
/* ── EV Module Scoped Styles ─────────────────────────────── */
.ev-hub-wrap {{ font-family: 'DM Sans', sans-serif; }}
.spc {{ overflow-x: hidden; overflow-y: auto; position: relative; z-index: 0; }}
#ev-leaflet-map {{ z-index: 1; position: relative; }}
/* hero banner */
.ev-hero {{
 background: url('{img_data_url}') center/cover no-repeat;
  border-radius: 20px; padding: 44px 40px; color: #fff;
  position: relative; overflow: hidden; margin-bottom: 28px;
}}
.ev-hero::after {{
  content: '';
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.45);
  border-radius: 20px;
  z-index: 0;
}}
.ev-hero > * {{
  position: relative;
  z-index: 1;
}}
.ev-hero::before {{
  content: ''; position: absolute; top: -80px; right: -80px;
  width: 340px; height: 340px; border-radius: 50%;
  background: radial-gradient(circle, rgba(34,197,94,.18) 0%, transparent 70%);
}}
.ev-hero-title {{
  font-family: 'Syne', sans-serif; font-size: 36px; font-weight: 900;
  margin-bottom: 10px; position: relative; line-height: 1.1;
}}
.ev-hero-title span {{ color: #4ADE80; }}
.ev-hero-sub {{ font-size: 14px; opacity: .72; max-width: 520px; line-height: 1.75; position: relative; }}
.ev-hero-stats {{ display: flex; gap: 18px; margin-top: 28px; flex-wrap: wrap; position: relative; }}
.ev-hs {{ background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12);
  border-radius: 14px; padding: 14px 22px; text-align: center; }}
.ev-hs-v {{ font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 800; color: #4ADE80; }}
.ev-hs-l {{ font-size: 10px; opacity: .6; margin-top: 3px; letter-spacing: .5px; }}

/* filter bar */
.ev-filter-bar {{
  display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 22px; align-items: center;
}}
.ev-filter-btn {{
  padding: 9px 20px; border-radius: 30px; font-size: 12px; font-weight: 600;
  border: 1.5px solid #E5E7EB; background: #fff; cursor: pointer;
  color: #6B7280; transition: all .22s; font-family: 'DM Sans', sans-serif;
}}
.ev-filter-btn.on {{ background: #22C55E; color: #fff; border-color: #22C55E; }}
.ev-filter-btn:hover:not(.on) {{ border-color: #22C55E; color: #22C55E; }}
.ev-search-wrap {{ position: relative; flex: 1; min-width: 220px; }}
.ev-search {{
  width: 100%; padding: 10px 16px 10px 38px; border-radius: 30px;
  border: 1.5px solid #E5E7EB; background: #fff; font-size: 13px;
  font-family: 'DM Sans', sans-serif; outline: none; transition: border-color .2s; color: #111827;
}}
.ev-search:focus {{ border-color: #22C55E; }}
.ev-search-icon {{ position: absolute; left: 13px; top: 50%; transform: translateY(-50%); font-size: 14px; }}

/* main layout */
.ev-main-grid {{
  display: grid; grid-template-columns: 1fr 1.4fr; gap: 22px; margin-bottom: 28px;
}}
@media(max-width: 1000px) {{ .ev-main-grid {{ grid-template-columns: 1fr; }} }}

/* station list */
.ev-station-list {{
  display: flex; flex-direction: column; gap: 14px;
  max-height: 680px; overflow-y: auto; padding-right: 4px;
}}
.ev-station-list::-webkit-scrollbar {{ width: 5px; }}
.ev-station-list::-webkit-scrollbar-track {{ background: #F9FAFB; border-radius: 10px; }}
.ev-station-list::-webkit-scrollbar-thumb {{ background: #D1D5DB; border-radius: 10px; }}

.ev-station-card {{
  background: #fff; border: 1.5px solid #E5E7EB; border-radius: 16px;
  padding: 18px 20px; cursor: pointer; transition: all .25s;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}}
.ev-station-card:hover, .ev-station-card.selected {{
  border-color: #22C55E; box-shadow: 0 6px 24px rgba(34,197,94,.15);
  transform: translateY(-2px);
}}
.ev-sc-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px; }}
.ev-sc-name {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: #111827; margin-bottom: 3px; }}
.ev-sc-building {{ font-size: 11px; color: #9CA3AF; }}
.ev-avail-badge {{
  display: flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700;
  padding: 5px 12px; border-radius: 20px; white-space: nowrap; flex-shrink: 0;
}}
.ev-avail-dot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
.ev-sc-meta {{ display: flex; gap: 14px; font-size: 11px; color: #6B7280; margin-bottom: 10px; flex-wrap: wrap; }}
.ev-sc-connectors {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }}
.ev-conn {{
  font-size: 10px; font-weight: 600; padding: 3px 9px; border-radius: 6px;
  background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE;
}}
.ev-sc-tags {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }}
.ev-tag {{
  font-size: 10px; font-weight: 600; padding: 3px 9px; border-radius: 20px;
  background: #DCFCE7; color: #166534;
}}
.ev-tag.solar {{ background: #FEF9C3; color: #854D0E; }}
.ev-sc-desc {{ font-size: 12px; color: #6B7280; line-height: 1.6; margin-bottom: 12px; }}
.ev-sc-actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.ev-act-btn {{
  padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600;
  border: 1.5px solid #E5E7EB; background: #fff; cursor: pointer;
  color: #374151; font-family: 'DM Sans', sans-serif; transition: all .2s;
}}
.ev-act-btn:hover {{ border-color: #22C55E; color: #22C55E; }}
.ev-act-btn.primary {{ background: #22C55E; color: #fff; border-color: #22C55E; }}
.ev-act-btn.primary:hover {{ background: #16A34A; }}

/* map panel */
.ev-map-panel {{
  background: #fff; border: 1.5px solid #E5E7EB; border-radius: 20px;
  overflow: hidden; position: relative; z-index: 0;
}}
.ev-map-header {{
  padding: 16px 20px; border-bottom: 1px solid #E5E7EB;
  display: flex; align-items: center; justify-content: space-between;
}}
.ev-map-title {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: #111827; }}
.ev-map-sub {{ font-size: 11px; color: #9CA3AF; margin-top: 2px; }}
.ev-live-dot {{
  width: 8px; height: 8px; background: #22C55E; border-radius: 50%;
  animation: blink 1.8s ease-in-out infinite; display: inline-block; margin-right: 5px;
}}
#ev-map-container {{ height: 500px; width: 100%; background: #F0FDF4; position: relative; }}
.ev-map-legend {{
  padding: 12px 16px; background: #F9FAFB; border-top: 1px solid #E5E7EB;
  display: flex; gap: 16px; flex-wrap: wrap;
}}
.ev-leg-item {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: #6B7280; font-weight: 500; }}
.ev-leg-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

/* map info popup */
.ev-info-popup {{
  background: #fff; border-radius: 14px; padding: 16px; width: 240px;
  box-shadow: 0 8px 32px rgba(0,0,0,.15); border: 1px solid #E5E7EB;
}}
.ev-ip-name {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 14px; color: #111827; margin-bottom: 4px; }}
.ev-ip-meta {{ font-size: 11px; color: #6B7280; margin-bottom: 10px; line-height: 1.5; }}
.ev-ip-btn {{
  display: block; width: 100%; text-align: center; padding: 9px; border-radius: 8px;
  background: #22C55E; color: #fff; font-size: 12px; font-weight: 700;
  border: none; cursor: pointer; font-family: 'DM Sans', sans-serif;
  margin-bottom: 6px; transition: background .2s;
}}
.ev-ip-btn:hover {{ background: #16A34A; }}
.ev-ip-btn.sec {{ background: #F9FAFB; color: #374151; border: 1.5px solid #E5E7EB; }}
.ev-ip-btn.sec:hover {{ border-color: #22C55E; color: #22C55E; }}

/* trip planner */
.ev-trip-wrap {{
  background: linear-gradient(135deg, #052e16, #0c1117);
  border-radius: 20px; padding: 32px 36px; color: #fff; margin-bottom: 28px;
}}
.ev-trip-title {{ font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800; margin-bottom: 6px; }}
.ev-trip-title span {{ color: #4ADE80; }}
.ev-trip-sub {{ font-size: 13px; opacity: .65; margin-bottom: 24px; line-height: 1.7; }}
.ev-trip-row {{ display: grid; grid-template-columns: 1fr 1fr auto; gap: 12px; align-items: end; margin-bottom: 14px; }}
@media(max-width:780px) {{ .ev-trip-row {{ grid-template-columns: 1fr; }} }}
.ev-trip-fg {{ display: flex; flex-direction: column; gap: 6px; }}
.ev-trip-label {{ font-size: 10px; font-weight: 700; color: rgba(255,255,255,.5); letter-spacing: 1px; text-transform: uppercase; }}
.ev-trip-input, .ev-trip-select {{
  padding: 12px 16px; border-radius: 10px; background: rgba(255,255,255,.09);
  border: 1px solid rgba(255,255,255,.15); color: #fff; font-size: 13px;
  font-family: 'DM Sans', sans-serif; outline: none; transition: border-color .25s; width: 100%;
}}
.ev-trip-input::placeholder {{ color: rgba(255,255,255,.35); }}
.ev-trip-input:focus, .ev-trip-select:focus {{ border-color: #4ADE80; }}
.ev-trip-select option {{ background: #111827; color: #fff; }}
.ev-trip-btn {{
  padding: 12px 28px; border-radius: 10px; background: #22C55E; color: #fff;
  border: none; cursor: pointer; font-size: 14px; font-weight: 700;
  font-family: 'Syne', sans-serif; transition: all .25s; white-space: nowrap; height: fit-content;
}}
.ev-trip-btn:hover {{ background: #16A34A; transform: translateY(-1px); }}

/* trip result */
.ev-trip-result {{
  display: none; background: rgba(34,197,94,.1); border: 1px solid rgba(34,197,94,.3);
  border-radius: 12px; padding: 18px; margin-top: 4px; color: rgba(255,255,255,.9); font-size: 13px;
}}
.ev-trip-stop {{
  display: flex; align-items: center; gap: 12px; padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,.08);
}}
.ev-trip-stop:last-child {{ border-bottom: none; padding-bottom: 0; }}
.ev-ts-icon {{ width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }}
.ev-ts-name {{ font-weight: 600; font-size: 13px; margin-bottom: 2px; }}
.ev-ts-meta {{ font-size: 11px; opacity: .6; }}

/* trip stops list (added stations) */
.ev-stops-list {{ display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }}
.ev-stop-item {{
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(255,255,255,.07); border-radius: 10px; padding: 10px 14px;
  font-size: 13px;
}}
.ev-stop-remove {{ background: none; border: none; color: #EF4444; cursor: pointer; font-size: 16px; line-height: 1; }}

/* stats summary row */
.ev-stats-row {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 28px; }}
@media(max-width:900px) {{ .ev-stats-row {{ grid-template-columns: 1fr 1fr; }} }}
.ev-stat-card {{
  background: #fff; border: 1px solid #E5E7EB; border-radius: 16px; padding: 20px;
  text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.04); position: relative; overflow: hidden;
  transition: all .22s;
}}
.ev-stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.08); }}
.ev-stat-card::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #22C55E, #4ADE80); border-radius: 16px 16px 0 0;
}}
.ev-stat-icon {{ font-size: 22px; margin-bottom: 8px; }}
.ev-stat-val {{ font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 800; color: #111827; }}
.ev-stat-lbl {{ font-size: 11px; color: #9CA3AF; margin-top: 3px; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; }}

/* nearby charging table */
.ev-nearby-wrap {{ background: #fff; border: 1.5px solid #E5E7EB; border-radius: 20px; overflow: hidden; margin-bottom: 28px; }}
.ev-nearby-head {{ padding: 18px 24px; border-bottom: 1px solid #E5E7EB; display: flex; justify-content: space-between; align-items: center; }}
.ev-nearby-title {{ font-family: 'Syne', sans-serif; font-weight: 700; font-size: 16px; color: #111827; }}
.ev-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.ev-table th {{ padding: 11px 16px; text-align: left; font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #9CA3AF; border-bottom: 1.5px solid #E5E7EB; background: #F9FAFB; }}
.ev-table td {{ padding: 14px 16px; border-bottom: 1px solid #F3F4F6; vertical-align: middle; }}
.ev-table tr:last-child td {{ border-bottom: none; }}
.ev-table tr:hover td {{ background: #F9FAFB; }}
.ev-status-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }}

/* no-results */
.ev-no-results {{ text-align: center; padding: 48px; color: #9CA3AF; }}
.ev-no-results span {{ font-size: 36px; display: block; margin-bottom: 12px; }}
</style>

<div class="ev-hub-wrap">

  <!-- HERO -->
  <div class="ev-hero">
    <h2 class="ev-hero-title">MNIT <span>ElectricQ</span> — Campus EV Hub</h2>
    <p class="ev-hero-sub">
      Find every EV charging point on MNIT Jaipur campus, check real-time availability,
      plan your route, and navigate directly from this dashboard.
      All solar-powered stations run off campus rooftop solar.
    </p>
    <div class="ev-hero-stats">
      <div class="ev-hs"><div class="ev-hs-v">{total_stations}</div><div class="ev-hs-l">Charging Points</div></div>
      <div class="ev-hs"><div class="ev-hs-v">{total_available}</div><div class="ev-hs-l">Available Now</div></div>
      <div class="ev-hs"><div class="ev-hs-v">{total_chargers}</div><div class="ev-hs-l">Total Chargers</div></div>
      <div class="ev-hs"><div class="ev-hs-v">{solar_stations}</div><div class="ev-hs-l">Solar Powered</div></div>
    </div>
  </div>

  

  

  

  <!-- MAIN: MAP FULL WIDTH -->
  <div class="ev-map-panel" style="margin-bottom:22px;">
    <div class="ev-map-header">
      <div>
        <div class="ev-map-title"><span class="ev-live-dot"></span>Live Campus Map</div>
        <div class="ev-map-sub">Click a pin or station card to see details</div>
      </div>
      <div style="display:flex;gap:8px">
        <button class="ev-filter-btn" style="font-size:11px;padding:7px 14px;" onclick="toggleSatellite()" id="ev-sat-btn">🛰 Satellite</button>
        <button class="ev-filter-btn" style="font-size:11px;padding:7px 14px;" onclick="recenterMap()">⊕ Re-centre</button>
      </div>
    </div>
    <div id="ev-map-container">
      <div id="ev-leaflet-map" style="height:500px;width:100%;"></div>
    </div>
    <div class="ev-map-legend">
      <div class="ev-leg-item"><span class="ev-leg-dot" style="background:#22C55E"></span>Available</div>
      <div class="ev-leg-item"><span class="ev-leg-dot" style="background:#EF4444"></span>Full / Offline</div>
      <div class="ev-leg-item"><span class="ev-leg-dot" style="background:#F59E0B"></span>Solar Powered</div>
      <div class="ev-leg-item"><span class="ev-leg-dot" style="background:#3B82F6"></span>Your Location</div>
    </div>
  </div>
<!-- FILTER BAR -->
  <div class="ev-filter-bar">
    <div class="ev-search-wrap">
      <span class="ev-search-icon">🔍</span>
      <input type="text" class="ev-search" placeholder="Search station name or building..."
             oninput="filterStations()" id="ev-search-input">
    </div>
    <button class="ev-filter-btn on" onclick="setFilter('all',this)">All</button>
    <button class="ev-filter-btn" onclick="setFilter('available',this)">🟢 Available</button>
    <button class="ev-filter-btn" onclick="setFilter('solar',this)">☀️ Solar</button>
    <button class="ev-filter-btn" onclick="setFilter('fast',this)">⚡ DC Fast</button>
    <button class="ev-filter-btn" onclick="setFilter('24',this)">🕐 24/7</button>
  </div>
  <!-- STATION LIST BELOW MAP -->
  <div id="ev-station-list" class="ev-station-list" style="max-height:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px;margin-bottom:28px;">
    {station_cards_html}
  </div>
  <div id="ev-no-results" class="ev-no-results" style="display:none">
    <span>🔌</span>
    No stations match your filter.<br>Try a different search or filter.
  </div>

  <!-- TRIP PLANNER BELOW LIST -->
  <div class="ev-trip-wrap">
    <div class="ev-trip-title">⚡ <span>Campus</span> EV Trip Planner</div>
    <p class="ev-trip-sub">
      Select your starting point and destination anywhere on campus.
      We'll show you the closest charging stations along the way.
    </p>
    <div class="ev-trip-row">
      <div class="ev-trip-fg">
        <label class="ev-trip-label">📍 Starting Point</label>
        <select class="ev-trip-select" id="ev-trip-start">
          <option value="">-- Select start --</option>
          {landmark_opts}
          {station_opts}
        </select>
      </div>
      <div class="ev-trip-fg">
        <label class="ev-trip-label">🏁 Destination</label>
        <select class="ev-trip-select" id="ev-trip-dest">
          <option value="">-- Select destination --</option>
          {landmark_opts}
          {station_opts}
        </select>
      </div>
      <button class="ev-trip-btn" onclick="planCampusTrip()">⚡ Plan Trip</button>
    </div>
    <div id="ev-trip-result" class="ev-trip-result"></div>
    <div style="margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,255,255,.1)">
      <div style="font-size:11px;font-weight:700;color:rgba(255,255,255,.5);letter-spacing:1px;text-transform:uppercase;margin-bottom:10px">
        My Trip Stops
      </div>
      <div id="ev-stops-list" class="ev-stops-list">
        <div style="font-size:12px;color:rgba(255,255,255,.35);font-style:italic">
          No stops added yet. Click "Add to Trip" on any station card below.
        </div>
      </div>
      <div style="display:flex;gap:10px;margin-top:12px;">
        <button class="ev-trip-btn" style="font-size:12px;padding:9px 18px;" onclick="openTripInMaps()">
          🗺️ Open Full Route in Google Maps
        </button>
        <button class="ev-trip-btn" style="font-size:12px;padding:9px 18px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);" onclick="clearTrip()">
          ✕ Clear Trip
        </button>
      </div>
    </div>
  </div>
     

  <!-- NEARBY TABLE (summary) -->
  <div class="ev-nearby-wrap">
    <div class="ev-nearby-head">
      <div class="ev-nearby-title">📋 All Campus Charging Points</div>
      <button class="ev-filter-btn" onclick="exportStationCSV()">⬇ Export CSV</button>
    </div>
    <div style="overflow-x:auto">
      <table class="ev-table" id="ev-summary-table">
        <thead>
          <tr>
            <th>Station</th>
            <th>Location</th>
            <th>Speed</th>
            <th>Available</th>
            <th>Hours</th>
            <th>Solar</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody id="ev-table-body">
        </tbody>
      </table>
    </div>
  </div>

</div><!-- end ev-hub-wrap -->

<!-- Leaflet CSS + JS (OpenStreetMap, no API key) -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
// ── EV Module Data (injected from Python) ────────────────────
const EV_STATIONS  = {stations_json};
const EV_LANDMARKS = {landmarks_json};

// ── State ────────────────────────────────────────────────────
let evMap        = null;
let evMarkers    = {{}};
let activeFilter = 'all';
let tripStops    = [];      // {{id, name, lat, lng}}
let userLatLng   = null;

// ── Init Map ─────────────────────────────────────────────────
// MNIT campus bounds — map cannot scroll outside this
const MNIT_BOUNDS = L.latLngBounds(
  [26.857, 75.806],   // SW corner
  [26.870, 75.823]    // NE corner
);

let streetLayer  = null;
let satelliteLayer = null;
let isSatellite  = false;

function initEVMap() {{
  if (evMap) return;
  evMap = L.map('ev-leaflet-map', {{
    center: [26.8635, 75.8145],
    zoom: 16,
    zoomControl: true,
    minZoom: 15,
    maxZoom: 19,
    maxBounds: MNIT_BOUNDS,
    maxBoundsViscosity: 1.0,
  }});
  evMap.scrollWheelZoom.disable();
evMap.on('focus', () => evMap.scrollWheelZoom.enable());
evMap.on('blur',  () => evMap.scrollWheelZoom.disable());

  // Street layer (OpenStreetMap)
  streetLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }});

  // Satellite layer (Esri World Imagery — free, no key)
  satelliteLayer = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
    {{
      attribution: 'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics',
      maxZoom: 19,
    }}
  );

  streetLayer.addTo(evMap);

  // Add all station markers
  EV_STATIONS.forEach(s => addMarker(s));

  // User location (only show if within campus)
  if (navigator.geolocation) {{
    navigator.geolocation.getCurrentPosition(pos => {{
      const ll = [pos.coords.latitude, pos.coords.longitude];
      userLatLng = ll;
      const userIcon = L.divIcon({{
        className: '',
        html: `<div style="width:16px;height:16px;border-radius:50%;background:#3B82F6;border:3px solid #fff;box-shadow:0 0 0 4px rgba(59,130,246,.3);"></div>`,
        iconSize: [16, 16], iconAnchor: [8, 8]
      }});
      L.marker(ll, {{icon: userIcon}}).addTo(evMap).bindPopup('<b>You are here</b>');
    }}, () => {{}});
  }}

  buildSummaryTable(EV_STATIONS);
}}

function toggleSatellite() {{
  if (!evMap) return;
  const btn = document.getElementById('ev-sat-btn');
  if (isSatellite) {{
    evMap.removeLayer(satelliteLayer);
    streetLayer.addTo(evMap);
    btn.textContent = '🛰 Satellite';
    isSatellite = false;
  }} else {{
    evMap.removeLayer(streetLayer);
    satelliteLayer.addTo(evMap);
    btn.textContent = '🗺 Street';
    isSatellite = true;
  }}
}}

 

function makePinHTML(color, label) {{
  return `<div style="position:relative;width:28px;height:36px;cursor:pointer;">
    <svg viewBox="0 0 28 36" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%">
      <ellipse cx="14" cy="34" rx="6" ry="2" fill="rgba(0,0,0,.25)"/>
      <path d="M14 2 C7 2 2 8 2 14 C2 24 14 34 14 34 C14 34 26 24 26 14 C26 8 21 2 14 2Z" fill="${{color}}" stroke="#fff" stroke-width="1.5"/>
      <text x="14" y="18" text-anchor="middle" font-size="12" fill="#fff" font-weight="bold"
            font-family="sans-serif" dominant-baseline="middle">${{label}}</text>
    </svg>
  </div>`;
}}

function addMarker(s) {{
  const avail    = s.available > 0;
  const pinColor = s.solar_powered ? '#F59E0B' : (avail ? '#22C55E' : '#EF4444');
  const pinLabel = '⚡';

  const icon = L.divIcon({{
    className: '',
    html: makePinHTML(pinColor, pinLabel),
    iconSize: [28, 36], iconAnchor: [14, 36], popupAnchor: [0, -36]
  }});

  const marker = L.marker([s.lat, s.lng], {{icon}}).addTo(evMap);

  const popupHTML = `
    <div class="ev-info-popup">
      <div class="ev-ip-name">${{s.name}}</div>
<div class="ev-ip-meta">
        ⚡ ${{s.kw}}  &nbsp; 🕐 ${{s.hours}}<br>
        🔌 ${{s.available}}/${{s.chargers}} chargers available
      </div>
      <button class="ev-ip-btn" onclick="openDirections(${{s.lat}},${{s.lng}},'${{s.name}}')">📍 Get Directions</button>
      <button class="ev-ip-btn sec" onclick="addToTrip('${{s.id}}','${{s.name}}')">➕ Add to My Trip</button>
    </div>`;

  marker.bindPopup(popupHTML, {{maxWidth: 260, className: 'ev-popup'}});
  marker.on('click', () => highlightCard(s.id));
  evMarkers[s.id] = marker;
}}

function recenterMap() {{
  if (!evMap) return;
  evMap.setView([26.8635, 75.8145], 16, {{animate: true}});
}}

function focusStation(id, lat, lng) {{
  if (!evMap) initEVMap();
  document.querySelectorAll('.ev-station-card').forEach(c => c.classList.remove('selected'));
  const card = document.querySelector(`.ev-station-card[data-id="${{id}}"]`);
  if (card) {{ card.classList.add('selected'); card.scrollIntoView({{behavior:'smooth', block:'nearest'}}); }}
  evMap.setView([lat, lng], 18, {{animate: true}});
  if (evMarkers[id]) evMarkers[id].openPopup();
}}

function highlightCard(id) {{
  document.querySelectorAll('.ev-station-card').forEach(c => c.classList.remove('selected'));
  const card = document.querySelector(`.ev-station-card[data-id="${{id}}"]`);
  if (card) {{ card.classList.add('selected'); card.scrollIntoView({{behavior:'smooth', block:'nearest'}}); }}
}}

// ── Filtering ────────────────────────────────────────────────
function setFilter(f, btn) {{
  activeFilter = f;
  document.querySelectorAll('.ev-filter-btn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  applyFilters();
}}

function filterStations() {{ applyFilters(); }}

function applyFilters() {{
  const q = (document.getElementById('ev-search-input').value || '').toLowerCase();
  let visible = 0;

  EV_STATIONS.forEach(s => {{
    const card = document.querySelector(`.ev-station-card[data-id="${{s.id}}"]`);
    if (!card) return;
    let show = true;

    if (activeFilter === 'available') show = s.available > 0;
    else if (activeFilter === 'solar')  show = s.solar_powered;
    else if (activeFilter === 'fast')   show = s.kw.includes('DC') || s.kw.includes('50');
    else if (activeFilter === '24')     show = s.hours === '24/7';

    if (show && q) {{
      show = s.name.toLowerCase().includes(q);
    }}

    card.style.display = show ? '' : 'none';
    if (show) visible++;
  }});

  document.getElementById('ev-no-results').style.display = visible === 0 ? 'block' : 'none';
}}

// ── Directions ───────────────────────────────────────────────
function openDirections(lat, lng, name) {{
  const url = `https://www.google.com/maps/dir/?api=1&destination=${{lat}},${{lng}}&travelmode=driving`;
  window.open(url, '_blank');
}}

function openStreetView(lat, lng) {{
  const url = `https://www.google.com/maps?layer=c&cbll=${{lat}},${{lng}}`;
  window.open(url, '_blank');
}}

// ── Trip Planner ─────────────────────────────────────────────
function addToTrip(id, name) {{
  if (tripStops.find(s => s.id === id)) {{
    alert(name + ' is already in your trip!'); return;
  }}
  const st = EV_STATIONS.find(s => s.id === id);
  tripStops.push({{id, name, lat: st.lat, lng: st.lng}});
  renderTripStops();
}}

function removeStop(id) {{
  tripStops = tripStops.filter(s => s.id !== id);
  renderTripStops();
}}

function clearTrip() {{
  tripStops = [];
  renderTripStops();
  document.getElementById('ev-trip-result').style.display = 'none';
}}

function renderTripStops() {{
  const el = document.getElementById('ev-stops-list');
  if (tripStops.length === 0) {{
    el.innerHTML = `<div style="font-size:12px;color:rgba(255,255,255,.35);font-style:italic">No stops added yet. Click "Add to Trip" on any station card below.</div>`;
    return;
  }}
  el.innerHTML = tripStops.map((s,i) => `
    <div class="ev-stop-item">
      <span style="font-size:11px;color:rgba(255,255,255,.45);width:20px;">${{i+1}}.</span>
      <span style="flex:1;font-weight:600;">${{s.name}}</span>
      <button class="ev-stop-remove" onclick="removeStop('${{s.id}}')">✕</button>
    </div>`).join('');
}}

function openTripInMaps() {{
  if (tripStops.length === 0) {{ alert('Add at least one stop first.'); return; }}
  const waypoints = tripStops.map(s => `${{s.lat}},${{s.lng}}`).join('/');
  const url = `https://www.google.com/maps/dir/${{waypoints}}`;
  window.open(url, '_blank');
}}

function planCampusTrip() {{
  const startSel = document.getElementById('ev-trip-start');
  const destSel  = document.getElementById('ev-trip-dest');
  const startVal = startSel.value;
  const destVal  = destSel.value;

  if (!startVal || !destVal) {{
    alert('Please select both a starting point and a destination.'); return;
  }}
  if (startVal === destVal) {{
    alert('Start and destination cannot be the same.'); return;
  }}

  const [sLat, sLng] = startVal.split(',').map(Number);
  const [dLat, dLng] = destVal.split(',').map(Number);
  const startName = startSel.options[startSel.selectedIndex].text;
  const destName  = destSel.options[destSel.selectedIndex].text;

  // Find 2 closest charging stations to midpoint
  const midLat = (sLat + dLat) / 2, midLng = (sLng + dLng) / 2;
  const sorted = [...EV_STATIONS].sort((a,b) => {{
    const da = Math.hypot(a.lat - midLat, a.lng - midLng);
    const db = Math.hypot(b.lat - midLat, b.lng - midLng);
    return da - db;
  }});
  const nearby = sorted.slice(0, 2);

  // Rough campus distance (m)
  const distM = Math.round(Math.hypot((dLat-sLat)*111320, (dLng-sLng)*96488));
  const distKm = (distM/1000).toFixed(2);
  const walkMin = Math.ceil(distM / 83);  // ~5 km/h

  const res = document.getElementById('ev-trip-result');
  res.style.display = 'block';
  res.innerHTML = `
    <div style="font-weight:700;font-size:14px;margin-bottom:12px;color:#4ADE80;">
      ⚡ Route: ${{startName}} → ${{destName}}
    </div>
    <div class="ev-trip-stop">
      <div class="ev-ts-icon" style="background:rgba(34,197,94,.2);">🟢</div>
      <div><div class="ev-ts-name">${{startName}}</div><div class="ev-ts-meta">Starting point</div></div>
    </div>
    ${{nearby.map(s=>`
    <div class="ev-trip-stop">
      <div class="ev-ts-icon" style="background:rgba(245,158,11,.2);">⚡</div>
      <div>
        <div class="ev-ts-name">${{s.name}}</div>
        <div class="ev-ts-meta">${{s.kw}} · ${{s.available}}/${{s.chargers}} available · ${{s.hours}}</div>
      </div>
    </div>`).join('')}}
    <div class="ev-trip-stop">
      <div class="ev-ts-icon" style="background:rgba(239,68,68,.2);">🏁</div>
      <div><div class="ev-ts-name">${{destName}}</div><div class="ev-ts-meta">Destination</div></div>
    </div>
    <div style="margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,.1);
                display:flex;gap:20px;font-size:12px;color:rgba(255,255,255,.7);">
      <span>🛣 ~${{distKm}} km on campus</span>
      <span>🚶 ~${{walkMin}} min walk</span>
      <span>⚡ ${{nearby.length}} charging stops</span>
    </div>
    <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">
      <button onclick="window.open('https://www.google.com/maps/dir/${{startVal.replace(',','%2C')}}/${{destVal.replace(',','%2C')}}','_blank')"
        style="background:#4ADE80;color:#111;border:none;padding:9px 18px;border-radius:8px;cursor:pointer;font-weight:700;font-size:12px;">
        🗺 Open in Google Maps
      </button>
    </div>`;

// Find all stations within 100m of the route line
  function pointToSegmentDist(px, py, ax, ay, bx, by) {{
    const dx = bx-ax, dy = by-ay;
    if (dx===0 && dy===0) return Math.hypot(px-ax, py-ay);
    const t = Math.max(0, Math.min(1, ((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)));
    return Math.hypot(px-(ax+t*dx), py-(ay+t*dy));
  }}
  const routeStations = EV_STATIONS.filter(s => {{
    const distDeg = pointToSegmentDist(s.lat, s.lng, sLat, sLng, dLat, dLng);
    const distM = distDeg * 111320;
    return distM <= 100;
  }});

  if (routeStations.length > 0) {{
    res.innerHTML += `
      <div style="margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.1);">
        <div style="font-size:11px;font-weight:700;color:#4ADE80;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;">
          ⚡ Charging Stations Within 100m of Your Route (${{routeStations.length}} found)
        </div>
        ${{routeStations.map(s => `
          <div class="ev-trip-stop">
            <div class="ev-ts-icon" style="background:rgba(34,197,94,.2);">🔌</div>
            <div style="flex:1;">
              <div class="ev-ts-name">${{s.name}}</div>
              <div class="ev-ts-meta">${{s.kw}} · ${{s.available}}/${{s.chargers}} available</div>
            </div>
            <button onclick="window.open('${{s.maps_link}}','_blank')"
              style="background:#4ADE80;color:#111;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-weight:700;font-size:11px;flex-shrink:0;">
              📍 Maps
            </button>
          </div>`).join('')}}
      </div>`;
  }} else {{
    res.innerHTML += `<div style="margin-top:10px;font-size:12px;color:rgba(255,255,255,.5);">No charging stations within 100m of this route.</div>`;
  }}

  // Zoom map to show route
  if (evMap) {{
    evMap.fitBounds([[sLat,sLng],[dLat,dLng]], {{padding:[40,40]}});
    routeStations.forEach(s => {{ if(evMarkers[s.id]) evMarkers[s.id].openPopup(); }});
  }}
}}

// ── Summary Table ────────────────────────────────────────────
function buildSummaryTable(stations) {{
  const tbody = document.getElementById('ev-table-body');
  if (!tbody) return;
  tbody.innerHTML = stations.map(s => {{
    const avail = s.available > 0;
    const dotColor = avail ? '#22C55E' : '#EF4444';
    const statusTxt = avail ? 'Available' : 'Full';
    return `<tr>
      <td style="font-weight:600;">${{s.name}}</td>
      <td style="color:#6B7280;font-size:12px;">—</td>
      <td style="font-family:'JetBrains Mono',monospace;font-size:12px;">${{s.kw}}</td>
      <td>
        <span style="display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;color:${{dotColor}};">
          <span style="width:7px;height:7px;border-radius:50%;background:${{dotColor}};display:inline-block;"></span>
          ${{s.available}}/${{s.chargers}} ${{statusTxt}}
        </span>
      </td>
      <td style="font-size:12px;color:#6B7280;">${{s.hours}}</td>
      <td style="text-align:center;">${{s.solar_powered ? '☀️' : '—'}}</td>
      <td>
        <div style="display:flex;gap:6px;">
          <button class="ev-act-btn primary" style="padding:6px 12px;font-size:11px;"
            onclick="focusStation('${{s.id}}',${{s.lat}},${{s.lng}})">📍 View</button>
          <button class="ev-act-btn" style="padding:6px 12px;font-size:11px;"
            onclick="openDirections(${{s.lat}},${{s.lng}},'${{s.name}}')">Navigate</button>
        </div>
      </td>
    </tr>`;
  }}).join('');
}}

// ── Export CSV ───────────────────────────────────────────────
function exportStationCSV() {{
  const rows = [['Name','Building','Speed','Available','Total','Hours','Solar','Lat','Lng']];
  EV_STATIONS.forEach(s => rows.push([
    s.name, s.building, s.kw, s.available, s.chargers, s.hours,
    s.solar_powered ? 'Yes' : 'No', s.lat, s.lng
  ]));
  const csv = rows.map(r => r.join(',')).join('\\n');
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = 'mnit_ev_stations.csv';
  a.click();
}}

// ── Auto-init when the EV Transport page opens ───────────────
// This is called from combine.py's openSP('transport') handler.
// We attach it so the map loads the moment the panel becomes visible.
(function waitForMap() {{
  const check = setInterval(() => {{
    const el = document.getElementById('ev-leaflet-map');
    if (el && el.offsetWidth > 0) {{
      clearInterval(check);
      initEVMap();
    }}
  }}, 200);
}})();
</script>
"""
    return html