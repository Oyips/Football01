import requests

KEY = "AQ.Ab8RN6IPP6QHclQTlwu5iS42iLln2YBNS-8ad7E393ubOkHSDg"
r = requests.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    headers={"x-goog-api-key": KEY},
    timeout=30,
)
print("Status:", r.status_code)
if r.status_code == 200:
    for m in r.json()["models"]:
        if "generateContent" in m.get("supportedGenerationMethods", []):
            print(m["name"])
else:
    print(r.text[:400])
