"""
fetch_garmin.py — fetches essential Garmin data for the running dashboard.
Place at: .github/scripts/fetch_garmin.py
"""
import garminconnect
import json
import os
import time
from datetime import date, timedelta, datetime

email    = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

# ── Login with retry (handles Garmin's IP rate limiting) ──────────────────
def login_with_retry(email, password, attempts=3, delay=15):
    for i in range(attempts):
        try:
            client = garminconnect.Garmin(email, password)
            client.login()
            print("Logged in to Garmin Connect")
            return client
        except Exception as e:
            print(f"Login attempt {i+1} failed: {e}")
            if i < attempts - 1:
                print(f"Waiting {delay}s before retry...")
                time.sleep(delay)
    raise Exception("Could not log in after multiple attempts")

client = login_with_retry(email, password)

today     = date.today()
yesterday = today - timedelta(days=1)
t         = today.isoformat()
y         = yesterday.isoformat()

# ── Helper: fetch with fallback ────────────────────────────────────────────
def safe_fetch(label, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        print(f"OK: {label}")
        return result
    except Exception as e:
        print(f"SKIP: {label} — {e}")
        return None

# ── Fetch only what matters ────────────────────────────────────────────────
daily      = safe_fetch("Daily summary",     client.get_stats,            t)

# Sleep: Garmin stores last night's sleep under today's calendar date.
# Try today first; if empty/missing fall back to yesterday.
sleep = safe_fetch("Sleep (today)",    client.get_sleep_data, t)
if not sleep or not sleep.get("dailySleepDTO", {}).get("sleepTimeSeconds"):
    print("  → today sleep empty, trying yesterday")
    sleep = safe_fetch("Sleep (yesterday)", client.get_sleep_data, y)

# HRV: same pattern — Garmin attaches last night's HRV to today's date
hrv = safe_fetch("HRV (today)",    client.get_hrv_data, t)
if not hrv or not hrv.get("hrvSummary"):
    print("  → today HRV empty, trying yesterday")
    hrv = safe_fetch("HRV (yesterday)", client.get_hrv_data, y)

bb         = safe_fetch("Body battery",      client.get_body_battery,     t)
stress     = safe_fetch("Stress",            client.get_stress_data,      t)
vo2        = safe_fetch("VO2max",            client.get_max_metrics,      t)
lt         = safe_fetch("Lactate threshold", client.get_lactate_threshold)
activities = safe_fetch("Activities",        client.get_activities,       0, 100)

# Log what we got for sleep/HRV so it's easy to verify in Actions logs
if sleep:
    dto = sleep.get("dailySleepDTO", {})
    score = dto.get("sleepScores", {}).get("overall", {}).get("value", "?")
    print(f"  Sleep score: {score} | date: {dto.get('calendarDate','?')}")
if hrv:
    s = hrv.get("hrvSummary", {})
    print(f"  HRV last night: {s.get('lastNightAvg','?')} | 7d avg: {s.get('weeklyAvg','?')}")

# ── Build output ───────────────────────────────────────────────────────────
now = datetime.utcnow()
data = {
    "updated":           t,
    "updatedTime":       now.strftime("%H:%M"),
    "updatedISO":        now.isoformat() + "Z",
    "daily_summary":     daily      or {},
    "sleep":             sleep      or {},
    "hrv":               hrv        or {},
    "body_battery":      bb         or [],
    "stress":            stress     or {},
    "vo2max":            vo2        or {},
    "lactate_threshold": lt         or [],
    "activities":        activities or [],
}

os.makedirs("public", exist_ok=True)
with open("public/garmin_data.json", "w") as f:
    json.dump(data, f)

act_count = len(activities) if activities else 0
print(f"Done — {act_count} activities saved to public/garmin_data.json")
print(f"Timestamp: {now.strftime('%Y-%m-%d %H:%M')} UTC")
