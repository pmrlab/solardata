# convert_map.py — run once from solardata folder
import os, re, json, glob

for js_file in glob.glob("map_export/data/*.js"):
    with open(js_file, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            out = js_file.replace(".js", ".geojson")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f"✅ {out}  ({len(data.get('features',[]))} features)")
        except Exception as e:
            print(f"❌ {js_file}: {e}")