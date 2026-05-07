"""
fetch_garmin.py — fetches all data needed by the upgraded dashboard.
Place at: .github/scripts/fetch_garmin.py
"""
import garminconnect, json, os
from datetime import date, timedelta, datetime

email    = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

client = garminconnect.Garmin(email, password)
client.login()

today     = date.today()
yesterday = today - timedelta(days=1)
t         = today.isoformat()
y         = yesterday.isoformat()
jan1      = date(today.year, 1, 1).isoformat()

print("Fetching daily summary…")
daily = client.get_stats(t)

print("Fetching sleep…")
sleep = client.get_sleep_data(y)

print("Fetching HRV…")
hrv = client.get_hrv_data(y)

print("Fetching body battery…")
bb = client.get_body_battery(t)

print("Fetching stress…")
stress = client.get_stress_data(t)

print("Fetching VO2max (today + history)…")
vo2 = client.get_max_metrics(t)
vo2_history = []

print("Fetching race predictions…")
race_preds = client.get_race_predictions()

print("Fetching lactate threshold…")
lt = client.get_lactate_threshold()

print("Fetching personal records…")
prs = client.get_personal_records()

print("Fetching activities (last 100)…")
activities = client.get_activities(0, 100)

print("Fetching resting HR trend (90 days)…")
ninety_ago = (today - timedelta(days=90)).isoformat()
rhr_trend = client.get_resting_heart_rate(t)

now = datetime.utcnow()
data = {
    "updated":       t,
    "updatedTime":   now.strftime("%H:%M"),
    "updatedISO":    now.isoformat() + "Z",
    "daily_summary": daily,
    "sleep":         sleep,
    "hrv":           hrv,
    "body_battery":  bb,
    "stress":        stress,
    "vo2max":        vo2,
    "vo2max_history": vo2_history,
    "race_predictions": race_preds,
    "lactate_threshold": lt,
    "personal_records": prs,
    "activities":    activities,
    "resting_hr":    rhr_trend,
}

os.makedirs("public", exist_ok=True)
with open("public/garmin_data.json", "w") as f:
    json.dump(data, f)

print(f"✅ Done — {len(activities)} activities, saved to public/garmin_data.json")
