import streamlit as st
import streamlit.components.v1 as components
import json
import os
import numpy as np

CAMPUS_CENTER_LAT = 26.8618
CAMPUS_CENTER_LNG = 75.8163

ORANGE = "#FF6B00"
SKY    = "#0EA5E9"
TEAL   = "#10B981"
BORDER = "#E2E8F0"
BG     = "#FFFFFF"


def render_campus_map(valid_isolar=None, valid_havells=None,
                      asset_file="mnit_assets.json"):

    if not os.path.exists(asset_file):
        st.warning(f"'{asset_file}' not found. Create it with plant coordinates.")
        return

    with open(asset_file) as f:
        assets = json.load(f)

    solar_count = sum(1 for a in assets if a["type"] == "solar")
    total_cap   = sum(a.get("capacity_kw") or 0 for a in assets if a["type"] == "solar")

    # ── Collect live plant names ──────────────────────────────────────────────
    live_names = set()
    for source in [valid_isolar, valid_havells]:
        if source:
            live_names.update(source.keys())

    # ── Compute KPIs from combined data ──────────────────────────────────────
    peak_dc_kw   = 0.0
    peak_ac_kw   = 0.0
    daily_kwh    = 0.0
    active_count = 0
    total_plant_count = solar_count

    for source in [valid_isolar, valid_havells]:
        if not source:
            continue
        for name, payload in source.items():
            df, t, dc, ac = payload
            if df is None or df.empty:
                continue
            active_count += 1
            peak_dc_kw = max(peak_dc_kw, float(df[dc].max()))
            peak_ac_kw = max(peak_ac_kw, float(df[ac].max()))
            try:
                _trap = getattr(np, "trapezoid", None) or getattr(np, "trapz", None)
                times_h = (df[t] - df[t].iloc[0]).dt.total_seconds().values / 3600.0
                daily_kwh += max(float(_trap(df[dc].values, x=times_h)), 0.0)
            except Exception:
                pass

    online_pct = int(100 * active_count / total_plant_count) if total_plant_count else 0

    # ── KPI strip ─────────────────────────────────────────────────────────────
    stats_html = f"""
    <div style="display:flex;gap:0;flex-wrap:nowrap;background:#FFFFFF;
                border:1px solid {BORDER};border-radius:10px;overflow:hidden;
                box-shadow:0 2px 10px rgba(0,0,0,0.06);margin-bottom:14px;
                font-family:'Inter',sans-serif;">
      <div style="flex:1;padding:14px 16px;border-right:1px solid {BORDER};text-align:center;">
        <div style="font-size:9.5px;font-weight:700;color:#64748B;letter-spacing:1.1px;
                    text-transform:uppercase;margin-bottom:6px;">⚡ Peak DC Power</div>
        <div style="font-size:24px;font-weight:800;color:#1E293B;letter-spacing:-0.5px;line-height:1;">
          {peak_dc_kw:,.1f}<span style="font-size:12px;color:#94A3B8;font-weight:600;margin-left:3px;">kW</span>
        </div>
      </div>
      <div style="flex:1;padding:14px 16px;border-right:1px solid {BORDER};text-align:center;">
        <div style="font-size:9.5px;font-weight:700;color:{SKY};letter-spacing:1.1px;
                    text-transform:uppercase;margin-bottom:6px;">↑ Peak AC Power</div>
        <div style="font-size:24px;font-weight:800;color:{SKY};letter-spacing:-0.5px;line-height:1;">
          {peak_ac_kw:,.1f}<span style="font-size:12px;color:#94A3B8;font-weight:600;margin-left:3px;">kW</span>
        </div>
      </div>
      <div style="flex:1;padding:14px 16px;border-right:1px solid {BORDER};text-align:center;">
        <div style="font-size:9.5px;font-weight:700;color:{TEAL};letter-spacing:1.1px;
                    text-transform:uppercase;margin-bottom:6px;">🟡 Daily Energy</div>
        <div style="font-size:24px;font-weight:800;color:{TEAL};letter-spacing:-0.5px;line-height:1;">
          {daily_kwh:,.1f}<span style="font-size:12px;color:#94A3B8;font-weight:600;margin-left:3px;">kWh</span>
        </div>
      </div>
      <div style="flex:1;padding:14px 16px;text-align:center;">
        <div style="font-size:9.5px;font-weight:700;color:{ORANGE};letter-spacing:1.1px;
                    text-transform:uppercase;margin-bottom:6px;">🟢 Active Plants</div>
        <div style="font-size:24px;font-weight:800;color:#1E293B;letter-spacing:-0.5px;line-height:1;">
          {active_count}<span style="font-size:14px;color:#94A3B8;font-weight:600;"> / {total_plant_count}</span>
        </div>
        <div style="font-size:10px;color:#94A3B8;margin-top:3px;">{online_pct}% online</div>
      </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    # ── Build GeoJSON features list for JS ────────────────────────────────────
    features = []
    for asset in assets:
        name       = asset["name"]
        atype      = asset["type"]
        is_online  = (name in live_names) if atype == "solar" else True
        cap        = asset.get("capacity_kw", 0) or 0

        # live stats for popup
        ldc = lac = pk_dc = pk_ac = energy = 0.0
        status_str = "ONLINE" if is_online else "OFFLINE"
        for source in [valid_isolar, valid_havells]:
            if not source or name not in source:
                continue
            df, t, dc, ac = source[name]
            if df is None or df.empty:
                continue
            ldc   = float(df[dc].iloc[-1])
            lac   = float(df[ac].iloc[-1])
            pk_dc = float(df[dc].max())
            pk_ac = float(df[ac].max())
            try:
                _trap   = getattr(np, "trapezoid", None) or getattr(np, "trapz", None)
                times_h = (df[t] - df[t].iloc[0]).dt.total_seconds().values / 3600.0
                energy  = max(float(_trap(df[dc].values, x=times_h)), 0.0)
            except Exception:
                pass
            break

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [asset["lon"], asset["lat"]]},
            "properties": {
                "name":      name,
                "atype":     atype,
                "is_online": is_online,
                "cap":       cap,
                "ldc":       round(ldc,   2),
                "lac":       round(lac,   2),
                "pk_dc":     round(pk_dc, 2),
                "pk_ac":     round(pk_ac, 2),
                "energy":    round(energy,1),
                "status":    status_str,
                "lat":       asset["lat"],
                "lon":       asset["lon"],
            }
        })

    geojson_str = json.dumps({"type": "FeatureCollection", "features": features})

    # ── Inline Mapbox GL JS map (no token — uses OpenFreeMap) ─────────────────
    # OpenFreeMap's "liberty" style is free, open, no API key required
    MAP_HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MNIT Campus Map</title>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<link  href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Inter',sans-serif; background:#0F172A; }}
  #map {{ width:100%; height:780px; }}

  /* ── Layer switcher ── */
  #layer-switcher {{
    position:absolute; top:10px; right:10px; z-index:10;
    background:#FFFFFF; border:1px solid #E2E8F0;
    border-radius:10px; padding:10px 14px;
    box-shadow:0 4px 16px rgba(0,0,0,0.12);
    font-family:'Inter',sans-serif; font-size:12px; color:#1E293B;
    min-width:160px;
  }}
  #layer-switcher .ls-title {{
    font-weight:800; font-size:10px; color:#64748B;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;
  }}
  #layer-switcher label {{
    display:flex; align-items:center; gap:7px;
    cursor:pointer; padding:4px 0; font-weight:600; color:#1E293B;
  }}
  #layer-switcher label:hover {{ color:#FF6B00; }}
  #layer-switcher input[type=radio]  {{ accent-color:#FF6B00; }}
  #layer-switcher input[type=checkbox] {{ accent-color:#FF6B00; }}
  #layer-switcher hr {{ border:none; border-top:1px solid #E2E8F0; margin:7px 0; }}

  /* ── 3D toggle ── */
  #tilt-btn {{
    position:absolute; top:10px; right:180px; z-index:10;
    background:#FFFFFF; border:1px solid #E2E8F0;
    border-radius:8px; padding:8px 14px;
    box-shadow:0 4px 16px rgba(0,0,0,0.12);
    font-family:'Inter',sans-serif; font-size:11px; font-weight:800;
    color:#FF6B00; cursor:pointer; transition:all 0.2s;
    letter-spacing:0.5px;
  }}
  #tilt-btn:hover {{ background:#FFF3E8; border-color:#FF6B00; }}

  /* ── Popup ── */
  .maplibregl-popup-content {{
    background:#0F172A !important; color:#F8FAFC !important;
    border:1px solid #334155 !important; border-radius:10px !important;
    padding:0 !important; box-shadow:0 8px 28px rgba(0,0,0,0.45) !important;
    max-width:290px !important;
  }}
  .maplibregl-popup-tip {{ border-top-color:#0F172A !important; }}
  .maplibregl-popup-close-button {{
    color:#94A3B8 !important; font-size:16px !important;
    padding:4px 8px !important; right:2px !important; top:2px !important;
  }}
  .maplibregl-popup-close-button:hover {{ color:#F8FAFC !important; background:transparent !important; }}

  /* ── Scale / attrib ── */
  .maplibregl-ctrl-attrib {{ font-size:9px !important; }}
</style>
</head>
<body>
<div id="map"></div>
<button id="tilt-btn" onclick="toggleTilt()">🏔 3D View</button>
<div id="layer-switcher">
  <div class="ls-title">🗺 Base Map</div>
  <label><input type="radio" name="base" value="satellite" checked onchange="switchBase(this.value)"> Real Base Map</label>
  <label><input type="radio" name="base" value="light"     onchange="switchBase(this.value)"> Light Base Map</label>
  <hr/>
  <div class="ls-title">Overlays</div>
  <label><input type="checkbox" id="labels-toggle" checked onchange="toggleLabels(this.checked)"> Labels</label>
</div>

<script>
const CAMPUS = [{CAMPUS_CENTER_LNG}, {CAMPUS_CENTER_LAT}];

// Tile URLs
const SATELLITE_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}";
const LIGHT_TILES     = "https://{{a-c}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}@2x.png";
const LABEL_TILES     = "https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}";

let is3D    = false;
let baseMode = 'satellite';

const map = new maplibregl.Map({{
  container: 'map',
  style: {{
    version: 8,
    glyphs: "https://fonts.openmaptiles.org/{{fontstack}}/{{range}}.pbf",
    sources: {{
      satellite: {{ type:'raster', tiles:[SATELLITE_TILES], tileSize:256, attribution:'© Esri' }},
      light:     {{ type:'raster', tiles:[LIGHT_TILES],     tileSize:256, attribution:'© Carto' }},
      labels:    {{ type:'raster', tiles:[LABEL_TILES],     tileSize:256, attribution:'© Esri' }},
    }},
    layers: [
      {{ id:'satellite-layer', type:'raster', source:'satellite', paint:{{'raster-opacity':1}} }},
      {{ id:'light-layer',     type:'raster', source:'light',     paint:{{'raster-opacity':0}} }},
      {{ id:'labels-layer',    type:'raster', source:'labels',    paint:{{'raster-opacity':0.85}} }},
    ]
  }},
  center: CAMPUS,
  zoom: 16.8,
  pitch: 0,
  bearing: 0,
  maxZoom: 21,
}});

// ── Controls ──────────────────────────────────────────────────────────────
map.addControl(new maplibregl.NavigationControl({{ visualizePitch:true }}), 'top-left');
map.addControl(new maplibregl.ScaleControl({{ maxWidth:120, unit:'metric' }}), 'bottom-right');
map.addControl(new maplibregl.FullscreenControl(), 'top-left');

// Enable two-finger pitch (touch devices)
map.touchPitch.enable();
map.dragRotate.enable();

// ── Layer switching ───────────────────────────────────────────────────────
function switchBase(val) {{
  baseMode = val;
  if(val === 'satellite') {{
    map.setPaintProperty('satellite-layer', 'raster-opacity', 1);
    map.setPaintProperty('light-layer',     'raster-opacity', 0);
  }} else {{
    map.setPaintProperty('satellite-layer', 'raster-opacity', 0);
    map.setPaintProperty('light-layer',     'raster-opacity', 1);
  }}
}}

function toggleLabels(show) {{
  map.setPaintProperty('labels-layer', 'raster-opacity', show ? 0.85 : 0);
}}

// ── 3D tilt toggle ────────────────────────────────────────────────────────
function toggleTilt() {{
  is3D = !is3D;
  map.easeTo({{
    pitch:   is3D ? 55 : 0,
    bearing: is3D ? -20 : 0,
    duration: 900
  }});
  document.getElementById('tilt-btn').textContent = is3D ? '🗺 2D View' : '🏔 3D View';
}}

// ── GeoJSON data ──────────────────────────────────────────────────────────
const GEOJSON = {geojson_str};

// ── Markers ───────────────────────────────────────────────────────────────
map.on('load', function() {{

  GEOJSON.features.forEach(function(f) {{
    const p        = f.properties;
    const isOnline = p.is_online;
    const isSolar  = p.atype === 'solar';

    // Custom marker element
    const el = document.createElement('div');
    el.style.cssText = [
      'width:'          + (isSolar ? '32px' : '28px'),
      'height:'         + (isSolar ? '32px' : '28px'),
      'border-radius:50%',
      'display:flex',
      'align-items:center',
      'justify-content:center',
      'font-size:'      + (isSolar ? '15px' : '13px'),
      'cursor:pointer',
      'border:2.5px solid ' + (isSolar ? (isOnline ? '#FF6B00' : '#64748B') : '#0EA5E9'),
      'background:'     + (isSolar ? (isOnline ? 'rgba(255,107,0,0.15)' : 'rgba(100,116,139,0.15)') : 'rgba(14,165,233,0.15)'),
      'box-shadow:0 2px 10px rgba(0,0,0,0.25)',
      'transition:transform 0.15s',
    ].join(';');
    el.innerHTML = isSolar ? (isOnline ? '☀️' : '⛔') : '⚡';
    el.onmouseover = () => {{ el.style.transform = 'scale(1.25)'; }};
    el.onmouseout  = () => {{ el.style.transform = 'scale(1)';    }};

    // Popup
    const accentCol   = isSolar ? (isOnline ? '#FF6B00' : '#64748B') : '#0EA5E9';
    const statusBadge = isOnline
      ? `<span style="background:#064E3B;color:#34D399;font-size:9px;font-weight:800;padding:2px 7px;border-radius:20px;">● ONLINE</span>`
      : `<span style="background:#450A0A;color:#F87171;font-size:9px;font-weight:800;padding:2px 7px;border-radius:20px;">● OFFLINE</span>`;

    const capRow = p.cap
      ? `<tr><td style="padding:3px 0;color:#94A3B8;font-weight:600;">Capacity</td>
             <td style="text-align:right;font-weight:800;color:#F8FAFC;">${{p.cap}} kW</td></tr>`
      : '';

    let liveSection = '';
    if(isOnline && isSolar) {{
      liveSection = `
        <div style="margin-top:8px;padding:10px;background:#1E293B;border-radius:6px;border:1px solid #334155;">
          <div style="font-size:9px;color:#94A3B8;font-weight:800;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Live Reading</div>
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <span style="color:#F8FAFC;font-size:12px;font-weight:800;"><span style="color:#FF6B00;">DC</span> ${{p.ldc}} <span style="font-size:9px;color:#94A3B8;">kW</span></span>
            <span style="color:#F8FAFC;font-size:12px;font-weight:800;"><span style="color:#0EA5E9;">AC</span> ${{p.lac}} <span style="font-size:9px;color:#94A3B8;">kW</span></span>
          </div>
          <div style="border-top:1px solid #334155;padding-top:6px;display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:#94A3B8;font-size:10px;font-weight:600;">Peak DC</span>
            <span style="color:#FF6B00;font-size:11px;font-weight:800;">${{p.pk_dc}} kW</span>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:#94A3B8;font-size:10px;font-weight:600;">Peak AC</span>
            <span style="color:#0EA5E9;font-size:11px;font-weight:800;">${{p.pk_ac}} kW</span>
          </div>
          <div style="border-top:1px solid #334155;padding-top:6px;display:flex;justify-content:space-between;">
            <span style="color:#94A3B8;font-size:10px;font-weight:600;">Daily Energy</span>
            <span style="color:#10B981;font-size:11px;font-weight:800;">${{p.energy}} kWh</span>
          </div>
        </div>`;
    }} else if(isSolar && !isOnline) {{
      liveSection = `
        <div style="margin-top:8px;padding:10px;background:#1C0A0A;border-radius:6px;
                    border:1px solid #450A0A;text-align:center;">
          <div style="color:#F87171;font-size:11px;font-weight:800;">⛔ No data for selected date</div>
          <div style="color:#94A3B8;font-size:9.5px;margin-top:4px;">Plant may be offline or data not uploaded</div>
        </div>`;
    }}

    const popupHTML = `
      <div style="font-family:'Inter',sans-serif;background:#0F172A;padding:2px;">
        <div style="background:#1E293B;border-left:4px solid ${{accentCol}};
                    padding:8px 12px;margin-bottom:10px;border-radius:0 6px 6px 0;">
          <div style="color:#F8FAFC;font-size:14px;font-weight:800;line-height:1.2;">${{p.name}}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
            <div style="color:${{accentCol}};font-size:10px;font-weight:800;letter-spacing:0.5px;">${{p.atype.toUpperCase()}}</div>
            ${{statusBadge}}
          </div>
        </div>
        <div style="padding:0 10px 2px 10px;">
          <table style="width:100%;font-size:12px;color:#F8FAFC;border-collapse:collapse;margin-bottom:4px;">
            ${{capRow}}
            <tr><td style="padding:3px 0;color:#94A3B8;font-weight:600;">Lat</td>
                <td style="text-align:right;color:#F8FAFC;font-weight:700;">${{p.lat.toFixed(4)}}</td></tr>
            <tr><td style="padding:3px 0;color:#94A3B8;font-weight:600;">Lon</td>
                <td style="text-align:right;color:#F8FAFC;font-weight:700;">${{p.lon.toFixed(4)}}</td></tr>
          </table>
          ${{liveSection}}
        </div>
        <div style="height:8px;"></div>
      </div>`;

    const popup = new maplibregl.Popup({{
      offset: 18,
      closeButton: true,
      maxWidth: '290px'
    }}).setHTML(popupHTML);

    new maplibregl.Marker({{ element: el }})
      .setLngLat(f.geometry.coordinates)
      .setPopup(popup)
      .addTo(map);
  }});

  // Campus boundary circle (drawn as a polygon approximation)
  const R = 600 / 111320;
  const circleCoords = [];
  for(let i=0; i<=64; i++) {{
    const angle = (i / 64) * 2 * Math.PI;
    circleCoords.push([
      CAMPUS[0] + R * Math.cos(angle),
      CAMPUS[1] + R * Math.sin(angle) * Math.cos(CAMPUS[1] * Math.PI/180)
    ]);
  }}
  map.addSource('campus-boundary', {{
    type:'geojson',
    data:{{ type:'Feature', geometry:{{ type:'Polygon', coordinates:[circleCoords] }} }}
  }});
  map.addLayer({{
    id:'campus-fill',
    type:'fill',
    source:'campus-boundary',
    paint:{{ 'fill-color':'#FF6B00', 'fill-opacity':0.04 }}
  }});
  map.addLayer({{
    id:'campus-line',
    type:'line',
    source:'campus-boundary',
    paint:{{ 'line-color':'#FF6B00', 'line-width':2, 'line-opacity':0.8 }}
  }});

  // 3D building extrusion layer for atmosphere (light style)
  map.addLayer({{
    id:'3d-buildings',
    source: {{ type:'raster', tiles:[] }},   // placeholder – actual 3D via pitch
    type:'raster',
    paint:{{}}
  }});

}});

// ── Keyboard shortcut: T = toggle tilt ───────────────────────────────────
document.addEventListener('keydown', e => {{
  if(e.key === 't' || e.key === 'T') toggleTilt();
}});

</script>
</body>
</html>
"""

    # Render the map component
    components.html(MAP_HTML, height=800, scrolling=False)

    # ── Legend ────────────────────────────────────────────────────────────────
    offline_count = sum(
        1 for a in assets
        if a["type"] == "solar" and a["name"] not in live_names
    )
    st.markdown(f"""
    <div style="display:flex;gap:24px;padding:10px 16px;
                background-color:{BG};border:1px solid {BORDER};
                border-radius:8px;margin-top:8px;
                font-family:Inter,sans-serif;font-size:12px;
                color:#000000;font-weight:600;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:6px;">
        <div style="width:12px;height:12px;background:{ORANGE};border-radius:50%;"></div>
        Solar plant (online)
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <div style="width:12px;height:12px;background:#94A3B8;border-radius:50%;"></div>
        Solar plant (offline{'&nbsp;·&nbsp;' + str(offline_count) if offline_count else ''})
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <div style="width:12px;height:12px;background:{SKY};border-radius:50%;"></div>
        Transformer
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <div style="width:12px;height:12px;border:2px solid {ORANGE};border-radius:50%;
                    background:rgba(255,107,0,0.05);"></div>
        Campus boundary
      </div>
      <div style="margin-left:auto;color:#475569;font-size:11px;">
        ⌨️ Press <b>T</b> or click 🏔 3D View to tilt · Two-finger drag to pitch
      </div>
    </div>
    """, unsafe_allow_html=True)