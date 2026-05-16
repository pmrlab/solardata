import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://pvcheck.havells.com/device-s/report/export"

# ✅ YOUR REAL TOKEN (already from your screenshot)
headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX25hbWUiOiIwX3NvbGFyQG1uaXQuYWMuaW5fMiIsIm1vZGlmeV9wYXNzd29yZCI6MSwic2NvcGUiOlsiYWxsIl0sImRldGFpbCI6eyJvcmdhbml6YXRpb25JZCI6MCwidG9wR3JvdXBJZCI6bnVsbCwiZ3JvdXBJZCI6bnVsbCwicm9sZUlkIjotMSwidXNlcklkIjoxMjc1NjA1MSwidmVyc2lvbiI6MTAwNCwiaWRlbnRpZmllciI6InNvbGFyQG1uaXQuYWMuaW4iLCJpZGVudGl0eVR5cGUiOjIsIm1kYyI6IkZPUkVJR05fMSIsImFwcElkIjpudWxsLCJuYW1lIjpudWxsLCJyb2xlSWRzIjpudWxsLCJ0ZW5hbnRPcmdJZCI6bnVsbCwic2lnblJlbElkIjpudWxsLCJ0ZW5hbnRMb2dpbkVudW0iOiJPVEhFUiJ9LCJleHAiOjE3ODI1NjM3MDgsIm1kYyI6IkZPUkVJR05fMSIsImF1dGhvcml0aWVzIjpbImFsbCJdLCJqdGkiOiIwOWNlNDQ3Ny0yMjE4LTRiY2QtYWYxZi1jNzJlMjMyN2EyOGUiLCJjbGllbnRfaWQiOiJ0ZXN0In0.C6lcdkvfPDBoH1kZaIe8_qZ6gba-GDNW6MQDMPHiaXF-t6uzJpwdtT6XkF5F0PpjUiWVzxhgELxhxfTAJeHB1xfWkU-wEfxsIywXtiCFe2-nObOEV82j1yGwe94jOweMRKKshc6HjNs8K1YtFBCtv36fI-t2X9JZpoTOTbf8WgnStjQCCZrRnqhmTfZESqVwzpzN315Sqjnum734rKeetxUPpiOn-vyS0RsGQ8iFcuA2XyvOQLLSwaqetSllxkTMc2haZ_lybrCdOkpDJ71jitDZfiiKGniXaqiUAI6NStlCDWNYfGW99DsnZnlLeQep-d7xQExAZB_itC9isAeB0A",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://pvcheck.havells.com",
    "Referer": "https://pvcheck.havells.com/plant/infos/device"
}

# ✅ FULL PAYLOAD (trimmed only enum maps for size, API doesn’t require them)
data = {
    "deviceId": 225321346,
    "deviceSn": "SJ2ES350N98002",
    "displayParams": [
        {"primaryId":2403,"storageName":"DV1","name":"DC Voltage PV1","unit":"V"},
        {"primaryId":2405,"storageName":"AV1","name":"AC Voltage R/U/A","unit":"V"},
        {"primaryId":2411,"storageName":"APo_t1","name":"Total AC Output Power (Active)","unit":"W"},
        {"primaryId":2870,"storageName":"Etdy_ge1","name":"Daily Production (Active)","unit":"kWh"},
        {"primaryId":2429,"storageName":"Bus_V1","name":"Bus Voltage","unit":"V"}
    ],
    "reportFields": [
        {"name":"Device Name","storageName":"TYPE_NAME","unit":""},
        {"name":"SN","storageName":"DEVICE_SN","unit":""},
        {"name":"Updated Time","storageName":"COLLECTION_TIME","unit":""}
    ],
    "isPage": True,
    "endDay": "2026-04-29",
    "startDay": "2026-04-29",
    "timeDimension": 1,
    "language": "en",
    "timeZone": "Asia/Calcutta",
    "orderDirection": "DESC",
    "orderProperty": "collectTime",
    "typeName": "Inverter"
}

# 🚀 REQUEST
response = requests.post(url, headers=headers, json=data, verify=False)

# DEBUG
print("Status:", response.status_code)
print("Type:", response.headers.get("content-type"))

# 💾 SAVE FILE
with open("havells_data.xlsx", "wb") as f:
    f.write(response.content)

print("✅ Downloaded: havells_data.xlsx")