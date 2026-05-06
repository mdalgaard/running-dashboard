import garminconnect, json, os
from datetime import date, timedelta

email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

client = garminconnect.Garmin(email, password)
client.login()

today = date.today().isoformat()
yesterday = (date.today() - timedelta(days=1)).isoformat()

data = {
    "updated": today,
    "activities": client.get_activities(0, 14),
    "sleep": client.get_sleep_data(yesterday),
    "hrv": client.get_hrv_data(yesterday),
    "daily_summary": client.get_stats(today),
    "vo2max": client.get_max_metrics(today),
    "body_battery": client.get_body_battery(today),
    "stress": client.get_stress_data(today),
}

with open("public/garmin_data.json", "w") as f:
    json.dump(data, f)

print("Data fetched and saved.")
