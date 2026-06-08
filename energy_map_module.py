"""
energy_map_module.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SolUrja — PMR Lab, MNIT Jaipur
Energy Map Module — Standalone, plug into app.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import glob
import base64

# ── GeoJSON loader ────────────────────────────────────────────────
def _load_geojson(path: str) -> str:
    """Return GeoJSON as a JS-safe string, or empty FeatureCollection."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f))
    except Exception:
        return '{"type":"FeatureCollection","features":[]}'

def _find_geojson(name: str) -> str:
    """Search common locations for a geojson file."""
    candidates = [
        f"map_export/layers/{name}.geojson",
        f"map_export/{name}.geojson",
        f"{name}.geojson",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    matches = glob.glob(f"map_export/**/{name}*.geojson", recursive=True)
    return matches[0] if matches else ""

def get_energy_map_html() -> str:
    """Return complete self-contained HTML string for the energy map section."""

    # 1. Load GeoJSON data directly from your exported files
    buildings_path    = _find_geojson("mnit_buildings")
    solar_path        = _find_geojson("solar_panel")
    transformer_path  = _find_geojson("transformers")
    roads_path        = _find_geojson("Roads")
    boundary_path     = _find_geojson("Boundary")
    powerline_path    = _find_geojson("powerline")

    buildings_data   = _load_geojson(buildings_path)   if buildings_path   else '{"type":"FeatureCollection","features":[]}'
    solar_data       = _load_geojson(solar_path)       if solar_path       else '{"type":"FeatureCollection","features":[]}'
    transformer_data = _load_geojson(transformer_path) if transformer_path else '{"type":"FeatureCollection","features":[]}'
    roads_data       = _load_geojson(roads_path)       if roads_path       else '{"type":"FeatureCollection","features":[]}'
    boundary_data    = _load_geojson(boundary_path)    if boundary_path    else '{"type":"FeatureCollection","features":[]}'
    powerline_data   = _load_geojson(powerline_path)   if powerline_path   else '{"type":"FeatureCollection","features":[]}'

    # 2. Safe Asset Loader for 2D Icons
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")

    def _img_b64(filename):
        path = os.path.join(ASSETS_DIR, filename)
        try:
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode()
        except:
            return ""

    solar_icon_b64       = _img_b64("solar_icon.png")
    transformer_icon_b64 = _img_b64("transformer_icon.png")

    html = f"""
<style>
/* ── Map module scoped styles ── */
.em-wrap {{ font-family: 'DM Sans', sans-serif; }}
.em-mode-bar {{
  display: flex; gap: 0; background: #fff; border: 1.5px solid #E5E7EB;
  border-radius: 14px; overflow: hidden; width: fit-content; margin-bottom: 18px;
  box-shadow: 0 2px 10px rgba(0,0,0,.06);
}}
.em-mode-btn {{
  padding: 11px 34px; font-size: 14px; font-weight: 700; font-family: 'DM Sans', sans-serif;
  border: none; background: none; cursor: pointer; color: #6B7280; transition: all .25s;
  border-right: 1.5px solid #E5E7EB; letter-spacing: .2px;
}}
.em-mode-btn:last-child {{ border-right: none; }}
.em-mode-btn.active {{ background: #0d9488; color: #fff; }}
.em-mode-btn:hover:not(.active) {{ background: #f0fdfa; color: #0d9488; }}

/* Layer toggle pill bar */
.em-layer-bar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; align-items: center; }}
.em-layer-pill {{
  display: flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: 30px;
  border: 1.5px solid #E5E7EB; background: #fff; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: all .22s; font-family: 'DM Sans', sans-serif; color: #374151; user-select: none;
}}
.em-layer-pill .dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}
.em-layer-pill.active {{ border-color: currentColor; }}
.em-layer-pill[data-layer*="buildings"].active  {{ color:#e879a0; border-color:#e879a0; background:#fff0f7; }}
.em-layer-pill[data-layer*="solar"].active      {{ color:#3b82f6; border-color:#3b82f6; background:#eff6ff; }}
.em-layer-pill[data-layer*="transformers"].active{{ color:#f59e0b; border-color:#f59e0b; background:#fffbeb; }}
.em-layer-pill[data-layer*="roads"].active      {{ color:#6b7280; border-color:#6b7280; background:#f9fafb; }}
.em-layer-pill[data-layer*="powerlines"].active {{ color:#22c55e; border-color:#22c55e; background:#f0fdf4; }}

.em-basemap-bar {{ display: flex; gap: 8px; margin-bottom: 14px; }}
.em-base-btn {{
  padding: 7px 18px; border-radius: 20px; border: 1.5px solid #E5E7EB; background: #fff;
  font-size: 12px; font-weight: 600; cursor: pointer; color: #6B7280; transition: all .22s;
}}
.em-base-btn.active {{ background: #111827; color: #fff; border-color: #111827; }}

#em-map-container {{
  width: 100%; height: 600px; border-radius: 16px; overflow: hidden;
  border: 1.5px solid #E5E7EB; box-shadow: 0 4px 24px rgba(0,0,0,.07); 
  position: relative; display: block;
}}
#em-leaflet-map {{ width: 100%; height: 600px; display: block; }}
#em-maplibre-map {{ width: 100%; height: 600px; display: none; }}
#em-maplibre-map {{ display: none; }}

.em-legend {{
  background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 14px 18px;
  margin-top: 14px; display: flex; flex-wrap: wrap; gap: 14px 24px; font-size: 12px;
}}
.em-leg-item {{ display: flex; align-items: center; gap: 7px; font-weight: 500; color: #374151; }}
.em-leg-swatch {{ width: 28px; height: 10px; border-radius: 3px; flex-shrink: 0; }}
.em-leg-circle {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}

/* Popup styles */
.em-popup h4 {{ font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; margin-bottom: 6px; color: #111827; }}
.em-popup p {{ font-size: 12px; color: #6B7280; margin: 2px 0; }}

/* Animated power line pulse */
@keyframes em-dash-flow {{ to {{ stroke-dashoffset: -20; }} }}
.em-powerline-animated {{ animation: em-dash-flow 1s linear infinite; }}

/* 3D info badge */
.em-3d-badge {{
  position: absolute; top: 14px; right: 14px; background: rgba(13,148,136,.9); color: #fff;
  font-size: 11px; font-weight: 700; padding: 5px 12px; border-radius: 20px; z-index: 10;
  backdrop-filter: blur(6px); pointer-events: none;
}}

.em-stats-row {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; }}
.em-stat-card {{ background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px 18px; }}
.em-stat-label {{ font-size: 10px; font-weight: 700; letter-spacing: 1.1px; text-transform: uppercase; color: #9CA3AF; margin-bottom: 6px; }}
.em-stat-val {{ font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 800; color: #111827; }}
.em-stat-unit {{ font-size: 12px; font-weight: 500; color: #9CA3AF; margin-left: 3px; }}
</style>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet"/>

<div class="em-wrap">
  <div style="margin-bottom:16px;">
    <div style="margin-bottom:14px;">
      <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#111827;margin-bottom:4px;">
        🗺️ MNIT Jaipur — Campus Energy Map
      </div>
      <div style="font-size:12px;color:#9CA3AF;">
        Real geospatial data exported from QGIS · Toggle layers · Switch 2D / 3D view
      </div>
    </div>
    <div class="em-mode-bar">
      <button class="em-mode-btn active" id="em-btn-2d" onclick="emSwitchMode('2d')">🗺️ 2D Map</button>
      <button class="em-mode-btn" id="em-btn-3d" onclick="emSwitchMode('3d')">🏙️ 3D View</button>
    </div>
  </div>

  <div id="em-controls-2d">
    <div class="em-layer-bar">
      <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:.8px;text-transform:uppercase;margin-right:4px;">Layers:</span>
      <div class="em-layer-pill active" data-layer="buildings" onclick="emToggleLayer('buildings',this)">
        <span class="dot" style="background:#e879a0;"></span>Buildings
      </div>
      <div class="em-layer-pill active" data-layer="solar" onclick="emToggleLayer('solar',this)">
        <span class="dot" style="background:#3b82f6;"></span>Solar Panels
      </div>
      <div class="em-layer-pill active" data-layer="transformers" onclick="emToggleLayer('transformers',this)">
        <span class="dot" style="background:#f59e0b;"></span>Transformers
      </div>
      <div class="em-layer-pill active" data-layer="roads" onclick="emToggleLayer('roads',this)">
        <span class="dot" style="background:#6b7280;"></span>Roads
      </div>
      <div class="em-layer-pill active" data-layer="powerlines" onclick="emToggleLayer('powerlines',this)">
        <span class="dot" style="background:#22c55e;"></span>Power Lines
      </div>
    </div>
    <div class="em-basemap-bar">
      <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:.8px;text-transform:uppercase;margin-right:4px;">Basemap:</span>
      <button class="em-base-btn active" onclick="emSwitchBasemap('satellite',this)">🛰️ Satellite</button>
      <button class="em-base-btn" onclick="emSwitchBasemap('street',this)">🗺️ Street</button>
      <button class="em-base-btn" onclick="emSwitchBasemap('topo',this)">⛰️ Topo</button>
    </div>
  </div>

  <div id="em-controls-3d" style="display:none;">
    <div class="em-layer-bar">
      <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:.8px;text-transform:uppercase;margin-right:4px;">3D Layers:</span>
      <div class="em-layer-pill active" data-layer="3d-buildings" onclick="em3dToggle('buildings-3d',this)">
        <span class="dot" style="background:#f87171;"></span>Buildings
      </div>
      <div class="em-layer-pill active" data-layer="3d-solar" onclick="em3dToggle('solar-3d',this);em3dToggle('solar-3d-fill',this);em3dToggle('solar-3d-outline',this)">
        <span class="dot" style="background:#60a5fa;"></span>Solar Panels
      </div>
      <div class="em-layer-pill active" data-layer="3d-transformers" onclick="em3dToggle('transformers-3d',this);em3dToggle('transformers-3d-pts',this);em3dToggle('transformers-3d-fill',this);em3dToggle('transformers-3d-outline',this)">
        <span class="dot" style="background:#fbbf24;"></span>Transformers
      </div>
      <div class="em-layer-pill active" data-layer="3d-roads" onclick="em3dToggle('roads-3d',this)">
        <span class="dot" style="background:#9ca3af;"></span>Roads
      </div>
      <div class="em-layer-pill active" data-layer="3d-powerlines" onclick="em3dToggle('powerlines-3d-glow',this);em3dToggle('powerlines-3d-core',this)">
        <span class="dot" style="background:#22c55e;"></span>Power Lines
      </div>
    </div>
    <div class="em-basemap-bar">
      <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:.8px;text-transform:uppercase;margin-right:4px;">Basemap:</span>
      <button class="em-base-btn active" onclick="em3dBasemap('satellite',this)">🛰️ Satellite</button>
      <button class="em-base-btn" onclick="em3dBasemap('street',this)">🗺️ Street</button>
    </div>
  </div>

  <div id="em-map-container">
    <div id="em-leaflet-map"></div>
    <div id="em-maplibre-map"></div>
    <div id="em-3d-badge" style="display:none;"></div>
  </div>

  <div class="em-legend">
    <div class="em-leg-item"><div class="em-leg-swatch" style="background:#000000;border:1px dashed #000;height:4px;"></div>Boundary</div>
    <div class="em-leg-item"><div class="em-leg-swatch" style="background:#f9a8d4;border:1px solid #e879a0;"></div>Buildings</div>
    <div class="em-leg-item"><div class="em-leg-swatch" style="background:#93c5fd;border:1px solid #3b82f6;"></div>Solar Panels</div>
    <div class="em-leg-item"><div class="em-leg-circle" style="background:#f59e0b;border:2px solid #d97706;border-radius:0;"></div>Transformers (Ground)</div>
    <div class="em-leg-item"><div class="em-leg-swatch" style="background:#d1d5db;border:1px solid #6b7280;height:4px;"></div>Roads</div>
    <div class="em-leg-item"><div class="em-leg-swatch" style="background:repeating-linear-gradient(90deg,#22c55e 0,#22c55e 8px,transparent 8px,transparent 14px);border:none;"></div>Power Lines (Live)</div>
  </div>

  <div class="em-stats-row">
    <div class="em-stat-card"><div class="em-stat-label">Campus Area</div><div class="em-stat-val">325<span class="em-stat-unit">acres</span></div></div>
    <div class="em-stat-card"><div class="em-stat-label">Solar Installations</div><div class="em-stat-val">20<span class="em-stat-unit">sites</span></div></div>
    <div class="em-stat-card"><div class="em-stat-label">Transformers</div><div class="em-stat-val">12<span class="em-stat-unit">units</span></div></div>
    <div class="em-stat-card"><div class="em-stat-label">Total Capacity</div><div class="em-stat-val">250<span class="em-stat-unit">kW</span></div></div>
    <div class="em-stat-card"><div class="em-stat-label">Buildings Mapped</div><div class="em-stat-val" id="em-bldg-count">—</div></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>

<script>
// ══════════════════════════════════════════════════════════════
//  GEOJSON DATA - Purely from QGIS, NO FAKE DATA
// ══════════════════════════════════════════════════════════════
const EM_BUILDINGS    = {buildings_data};
const EM_SOLAR        = {solar_data};
const EM_TRANSFORMERS = {transformer_data};
const EM_ROADS        = {roads_data};
const EM_BOUNDARY     = {boundary_data};
const EM_POWERLINES   = {powerline_data}; // Actual exact lines from your QGIS layer!
const EM_CENTER       = [26.8566, 75.8157];
const EM_ZOOM         = 15;

// ══════════════════════════════════════════════════════════════
//  2D LEAFLET MAP
// ══════════════════════════════════════════════════════════════
let emLeaflet = null;
let emLayers  = {{}};
let emBaseLayers = {{}};

function emInitLeaflet() {{
  if (emLeaflet) return;

const campusBounds = L.latLngBounds(
    L.latLng(26.846, 75.807),
    L.latLng(26.867, 75.826)
  );
  emLeaflet = L.map('em-leaflet-map', {{
    center: [26.857, 75.817],
    zoom: 15,
    minZoom: 15,
    maxZoom: 19,
    maxBounds: campusBounds,
    maxBoundsViscosity: 1.0
  }});
  emBaseLayers['satellite'] = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}');
  emBaseLayers['street'] = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png');
  emBaseLayers['topo'] = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png');
  emBaseLayers['satellite'].addTo(emLeaflet);

  if (EM_BOUNDARY.features && EM_BOUNDARY.features.length > 0) {{
    L.geoJSON(EM_BOUNDARY, {{
      style: {{ color: '#000000', weight: 7, fillOpacity: 0, dashArray: '5 5' }}
    }}).addTo(emLeaflet);
  }}

  // ── Buildings ──
  emLayers['buildings'] = L.geoJSON(EM_BUILDINGS, {{
    style: {{ color: '#e879a0', weight: 1.5, fillColor: '#fce7f3', fillOpacity: 0.55 }},
    onEachFeature: (feat, layer) => layer.bindPopup(`<div class="em-popup"><h4>🏛️ ${{feat.properties.name || 'Building'}}</h4></div>`)
  }}).addTo(emLeaflet);

  const bldgCount = EM_BUILDINGS.features ? EM_BUILDINGS.features.length : 0;
  if (document.getElementById('em-bldg-count')) document.getElementById('em-bldg-count').textContent = bldgCount || '—';

  // ── Solar Panels (Blue Rectangles) ──
  const b64Solar = '{solar_icon_b64}';
  const solarIcon = (b64Solar.length > 10) 
    ? L.icon({{ iconUrl: b64Solar, iconSize: [28,28], iconAnchor:[14,14], popupAnchor:[0,-14] }})
    : L.divIcon({{ html: `<div style="background:#3b82f6;width:20px;height:20px;border-radius:3px;"></div>`, className:'', iconSize:[20,20], iconAnchor:[10,10] }});

  emLayers['solar'] = L.geoJSON(EM_SOLAR, {{
    style: {{ color: '#1d4ed8', weight: 1.5, fillColor: '#3b82f6', fillOpacity: 0.85 }}, // forces blue polygon
    pointToLayer: (f, latlng) => L.marker(latlng, {{icon: solarIcon}}), // fallback for points
    onEachFeature: (feat, layer) => layer.bindPopup(`<div class="em-popup"><h4>☀️ ${{feat.properties.name || 'Solar Panel'}}</h4></div>`)
  }}).addTo(emLeaflet);

  // ── Transformers (Orange Squares) ──
  const b64Tx = '{transformer_icon_b64}';
  const txIcon = (b64Tx.length > 10) 
    ? L.icon({{ iconUrl: b64Tx, iconSize: [28,28], iconAnchor:[14,14], popupAnchor:[0,-14] }})
    : L.divIcon({{ html: `<div style="background:#f59e0b;width:18px;height:18px;border:2px solid #fff;"></div>`, className:'', iconSize:[18,18], iconAnchor:[9,9] }});

  emLayers['transformers'] = L.geoJSON(EM_TRANSFORMERS, {{
    style: {{ color: '#d97706', weight: 1.5, fillColor: '#f59e0b', fillOpacity: 0.9 }}, 
    pointToLayer: (f, latlng) => L.marker(latlng, {{icon: txIcon}}), 
    onEachFeature: (feat, layer) => layer.bindPopup(`<div class="em-popup"><h4>⚡ ${{feat.properties.name || 'Transformer'}}</h4></div>`)
  }}).addTo(emLeaflet);

  emLayers['roads'] = L.geoJSON(EM_ROADS, {{
    style: {{ color: '#000000', weight: 3, opacity: 0.95 }}
  }}).addTo(emLeaflet);

  // ── Real Power Lines (from actual QGIS line data) ──
  emLayers['powerlines'] = L.geoJSON(EM_POWERLINES, {{
    style: {{ color: '#22c55e', weight: 6, opacity: 0.95, dashArray: '8 6', className: 'em-powerline-animated' }},
    onEachFeature: (feat, layer) => layer.bindPopup('<div class="em-popup"><h4>⚡ Power Line</h4><p>Live grid distribution</p></div>')
  }}).addTo(emLeaflet);
}}

function emToggleLayer(name, pill) {{
  pill.classList.toggle('active');
  if (!emLeaflet || !emLayers[name]) return;
  if (emLeaflet.hasLayer(emLayers[name])) emLeaflet.removeLayer(emLayers[name]);
  else emLeaflet.addLayer(emLayers[name]);
}}

function emSwitchBasemap(name, btn) {{
  document.querySelectorAll('.em-basemap-bar .em-base-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (!emLeaflet || !emBaseLayers[name]) return;
  Object.values(emBaseLayers).forEach(l => {{ if (emLeaflet.hasLayer(l)) emLeaflet.removeLayer(l); }});
  emBaseLayers[name].addTo(emLeaflet);
}}

// ══════════════════════════════════════════════════════════════
//  3D MAPLIBRE MAP (NATIVE SHAPES)
// ══════════════════════════════════════════════════════════════
let emML = null;

function emInitMapLibre() {{
  if (emML) return;

  emML = new maplibregl.Map({{
    container: 'em-maplibre-map',
    style: {{
      version: 8,
      sources: {{
        'esri-satellite': {{
          type: 'raster',
          tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}'],
          tileSize: 256,
          attribution: 'Esri World Imagery'
        }}
      }},
      layers: [{{ id: 'esri-satellite', type: 'raster', source: 'esri-satellite' }}]
    }},
    center: [75.8160, 26.8560],
    zoom: 16,
    minZoom: 16,
    maxZoom: 19,
    pitch: 60,
    bearing: -20,
    antialias: true,
    maxBounds: [[75.809, 26.848], [75.824, 26.865]]
  }});

  emML.addControl(new maplibregl.NavigationControl());

  emML.on('load', () => {{
    // ── 1. Load Real GeoJSON Sources ───────────────────────────
    emML.addSource('buildings-src',    {{ type: 'geojson', data: EM_BUILDINGS }});
    emML.addSource('solar-src',        {{ type: 'geojson', data: EM_SOLAR }});
    emML.addSource('transformers-src', {{ type: 'geojson', data: EM_TRANSFORMERS }});
    emML.addSource('roads-src',        {{ type: 'geojson', data: EM_ROADS }});
    emML.addSource('powerlines-src',   {{ type: 'geojson', data: EM_POWERLINES }}); // Actual lines!
    emML.addSource('boundary-src',     {{ type: 'geojson', data: EM_BOUNDARY }});

    // ── 2. Native 3D Rendering ───────────────
    
    // Black Boundary Line
    emML.addLayer({{ id:'boundary-3d', type:'line', source:'boundary-src',
      paint:{{'line-color':'#000000','line-width':8,'line-dasharray':[2,2]}} }});

    // Roads
    emML.addLayer({{ id:'roads-3d', type:'line', source:'roads-src',
      paint:{{'line-color':'#000000','line-width':4,'line-opacity':0.95}} }});

    // 3D Powerline Neon Effect (follows your exact QGIS lines)
    emML.addLayer({{ id:'powerlines-3d-glow', type:'line', source:'powerlines-src',
      paint:{{'line-color':'#22c55e','line-width':14,'line-opacity':0.35,'line-blur':6}} }});
    emML.addLayer({{ id:'powerlines-3d-core', type:'line', source:'powerlines-src',
      paint:{{'line-color':'#4ade80','line-width':6,'line-dasharray':[2,1]}} }});

    // Buildings (Base 0, Extrude up to 12 meters)
    emML.addLayer({{ id:'buildings-3d', type:'fill-extrusion', source:'buildings-src',
      paint:{{'fill-extrusion-color':'#f87171',
              'fill-extrusion-height':['coalesce',['get','height'],['get','building:levels'],12],
              'fill-extrusion-base':0,'fill-extrusion-opacity':0.82}} }});

// ── Solar — blue rectangle, NO type filter (works for polygon AND point) ──
   // ── Solar — flat blue rectangles on ground (same as 2D) ──
    emML.addLayer({{ id:'solar-3d-fill', type:'fill', source:'solar-src',
      paint:{{
        'fill-color': '#3b82f6',
        'fill-opacity': 0.92
      }}
    }});
    emML.addLayer({{ id:'solar-3d-outline', type:'line', source:'solar-src',
      paint:{{
        'line-color': '#1d4ed8',
        'line-width': 2.5
      }}
    }});
    emML.addLayer({{ id:'solar-3d', type:'circle', source:'solar-src',
      filter: ['==', ['geometry-type'], 'Point'],
      paint:{{
        'circle-color': '#3b82f6',
        'circle-radius': 10,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#1d4ed8'
      }}
    }});

    // ── Transformers — flat orange squares on ground (same as 2D) ──
    emML.addLayer({{ id:'transformers-3d-fill', type:'fill', source:'transformers-src',
      paint:{{
        'fill-color': '#f59e0b',
        'fill-opacity': 0.95
      }}
    }});
    emML.addLayer({{ id:'transformers-3d-outline', type:'line', source:'transformers-src',
      paint:{{
        'line-color': '#d97706',
        'line-width': 2.5
      }}
    }});
    emML.addLayer({{ id:'transformers-3d', type:'circle', source:'transformers-src',
      filter: ['==', ['geometry-type'], 'Point'],
      paint:{{
        'circle-color': '#f59e0b',
        'circle-radius': 10,
        'circle-stroke-width': 2.5,
        'circle-stroke-color': '#fff'
      }}
    }});
    emML.addLayer({{ id:'transformers-3d-pts', type:'circle', source:'transformers-src',
      filter: ['==', ['geometry-type'], 'Point'],
      paint:{{
        'circle-color': '#f59e0b',
        'circle-radius': 10,
        'circle-stroke-width': 2.5,
        'circle-stroke-color': '#fff'
      }}
    }});
    // ── 3. Interactive Popups ─────────
    ['buildings-3d', 'solar-3d', 'solar-3d-fill', 'transformers-3d', 'transformers-3d-fill', 'transformers-3d-pts', 'powerlines-3d-core'].forEach(layerId => {{
      emML.on('click', layerId, e => {{
        const p = e.features[0].properties || {{}};
        const name = p.name || p.Name || layerId.split('-')[0].toUpperCase();
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(`<div class="em-popup"><h4>📌 ${{name}}</h4>
            ${{Object.entries(p).slice(0,3).map(([k,v])=>`<p><b>${{k}}:</b> ${{v}}</p>`).join('')}}
          </div>`)
          .addTo(emML);
      }});
      emML.on('mouseenter', layerId, () => emML.getCanvas().style.cursor = 'pointer');
      emML.on('mouseleave', layerId, () => emML.getCanvas().style.cursor = '');
    }});
  }});
}}

function em3dToggle(layerId, pill) {{
  pill.classList.toggle('active');
  if (!emML) return;
  try {{
    const vis = emML.getLayoutProperty(layerId, 'visibility');
    emML.setLayoutProperty(layerId, 'visibility', vis === 'none' ? 'visible' : 'none');
  }} catch(e) {{}}
}}

function em3dBasemap(name, btn) {{
  document.querySelectorAll('#em-controls-3d .em-base-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (!emML) return;
  const urls = {{
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
    street:    'https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png'
  }};
  const src = emML.getSource('esri-satellite');
  if (src) src.setTiles([urls[name] || urls.satellite]);
}}

// ══════════════════════════════════════════════════════════════
//  MODE SWITCH
// ══════════════════════════════════════════════════════════════
function emSwitchMode(mode) {{
  const leafletDiv  = document.getElementById('em-leaflet-map');
  const mlDiv       = document.getElementById('em-maplibre-map');
  const controls2d  = document.getElementById('em-controls-2d');
  const controls3d  = document.getElementById('em-controls-3d');
  const badge3d     = document.getElementById('em-3d-badge');

  document.getElementById('em-btn-2d').classList.toggle('active', mode === '2d');
  document.getElementById('em-btn-3d').classList.toggle('active', mode === '3d');

  if (mode === '2d') {{
    leafletDiv.style.display = 'block'; 
    leafletDiv.style.height = '600px';
    mlDiv.style.display = 'none';
    controls2d.style.display = ''; controls3d.style.display = 'none'; badge3d.style.display = 'none';
    emInitLeaflet();
    setTimeout(() => {{ 
      if (emLeaflet) {{
        emLeaflet.invalidateSize();
        emLeaflet.setView(EM_CENTER, 16);
      }}
    }}, 200);
  }} else {{
    leafletDiv.style.display = 'none'; 
    mlDiv.style.display = 'block';
    mlDiv.style.height = '600px';
    controls2d.style.display = 'none'; controls3d.style.display = ''; badge3d.style.display = 'block';
    emInitMapLibre();
    setTimeout(() => {{ if (emML) emML.resize(); }}, 200);
  }}
}}

(function() {{
  let attempts = 0;
  const tryInit = () => {{
    attempts++;
    const el = document.getElementById('em-leaflet-map');
    if (el && (el.offsetWidth > 0 || attempts > 10)) {{
      emInitLeaflet();
      setTimeout(() => {{
        if (emLeaflet) emLeaflet.invalidateSize();
      }}, 500);
    }} else {{
      setTimeout(tryInit, 400);
    }}
  }};
  setTimeout(tryInit, 800);
}})();
</script>
"""
    return html

if __name__ == "__main__":
    html = get_energy_map_html()
    with open("/tmp/energy_map_test.html", "w") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body>{html}</body></html>")