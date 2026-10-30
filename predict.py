import time
import requests
from datetime import date, timedelta

FOOTBALL_KEY = "3cb2e6b66f4f47a59f5168969681d2f6"
GEMINI_KEY = "AQ.Ab8RN6JLUNii5T4pDVCErAJ5RjvkUyVBk9drja7Xucsu6dCg4g"

FB = "https://api.football-data.org/v4"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
tables = {}

def fb_get(path):
    for _ in range(3):
        r = requests.get(FB + path, headers={"X-Auth-Token": FOOTBALL_KEY}, timeout=30)
        time.sleep(7)
        if r.status_code == 429:
            time.sleep(30)
            continue
        if r.status_code != 200:
            print("Football API error:", r.status_code, r.text[:200])
            return None
        return r.json()
    return None

def ask_gemini(prompt):
    for _ in range(3):
        r = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": GEMINI_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        if r.status_code == 429:
            time.sleep(30)
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return "Gemini limit reached."

def score(m):
    s = m["score"]["fullTime"]
    return f"{m['homeTeam']['name']} {s['home']}-{s['away']} {m['awayTeam']['name']}"

def table_row(code, tid):
    if code not in tables:
        d = fb_get(f"/competitions/{code}/standings")
        try:
            tables[code] = d["standings"][0]["table"]
        except (TypeError, KeyError, IndexError):
            tables[code] = []
    for r in tables[code]:
        if r["team"]["id"] == tid:
            return (f"position {r['position']}, played {r['playedGames']}, "
                    f"W{r['won']} D{r['draw']} L{r['lost']}, "
                    f"goals {r['goalsFor']}-{r['goalsAgainst']}, points {r['points']}")
    return "not available"

def form(tid):
    d = fb_get(f"/teams/{tid}/matches?status=FINISHED")
    if not d:
        return "not available"
    games = sorted(d["matches"], key=lambda m: m["utcDate"])[-5:]
    return "; ".join(score(m) for m in games) or "not available"

def h2h(mid):
    d = fb_get(f"/matches/{mid}/head2head?limit=5")
    if not d or not d.get("matches"):
        return "not available"
    return "; ".join(score(m) for m in d["matches"])

def analyze(m):
    h, a, code = m["homeTeam"], m["awayTeam"], m["competition"]["code"]
    prompt = (
        f"{m['competition']['name']}: {h['name']} vs {a['name']}\n"
        f"{h['name']} table: {table_row(code, h['id'])}\n"
        f"{a['name']} table: {table_row(code, a['id'])}\n"
        f"{h['name']} last 5: {form(h['id'])}\n"
        f"{a['name']} last 5: {form(a['id'])}\n"
        f"Head-to-head: {h2h(m['id'])}\n\n"
        "Using only this data, predict the result (home win/draw/away win) "
        "with a likely scoreline, a confidence level and short reasoning. "
        "Say clearly where data is missing."
    )
    return f"{h['name']} vs {a['name']}\n{ask_gemini(prompt)}\n{'-'*40}\n"

today = date.today().isoformat()
tomorrow = (date.today() + timedelta(days=1)).isoformat()
d = fb_get(f"/matches?dateFrom={today}&dateTo={tomorrow}")
matches = d["matches"] if d else []
matches = [m for m in matches if m["status"] in ("SCHEDULED", "TIMED")]
print(f"Found {len(matches)} upcoming matches")

filename = f"predictions_{today}.txt"
with open(filename, "w", encoding="utf-8") as f:
    for i, m in enumerate(matches, 1):
        name = f"{m['homeTeam']['name']} vs {m['awayTeam']['name']}"
        print(f"Analyzing {i}/{len(matches)}: {name}")
        try:
            f.write(analyze(m))
        except Exception as e:
            f.write(f"{name}\nFailed: {e}\n{'-'*40}\n")
        f.flush()

print("Done. Saved to", filename)
