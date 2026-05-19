import base64

with open("Mnit_logo.png", "rb") as f:
    base64_string = base64.b64encode(f.read()).decode("utf-8")

print(base64_string)