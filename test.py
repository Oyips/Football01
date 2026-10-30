import requests
from datetime import date, timedelta

KEY = "3cb2e6b66f4f47a59f5168969681d2f6"
today = date.today()
tomorrow = today + timedelta(days=1)

url = f"https://api.football-data.org/v4/matches?dateFrom={today}&dateTo={tomorrow}"
r = requests.get(url, headers={"X-Auth-Token": KEY}, timeout=30)
print("Status:", r.status_code)
print(r.text[:500])
