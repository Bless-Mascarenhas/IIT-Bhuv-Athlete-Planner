import requests
import sqlite3
import os
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
DB_PATH = os.path.join(os.path.dirname(__file__), "athlete_planner.db")

print("Waiting for server to be ready...")
time.sleep(2) # Give FastAPI a moment if it just restarted

# 1. Setup Dummy Athlete
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("INSERT INTO athletes (name, sport_type) VALUES ('Simulator Athlete', 'Soccer')")
athlete_id = cursor.lastrowid
conn.commit()
conn.close()

print(f"Created Athlete ID: {athlete_id}")

# 2. Simulate 28 days of Normal Load (Chronic Baseline)
# RPE 5, 60 mins -> Daily load = 300
start_date = datetime.now() - timedelta(days=35)

print("Injecting 28 days of baseline 'Device' data (Nominal Load)...")
for i in range(28):
    current_date = start_date + timedelta(days=i)
    payload = {
        "athlete_id": athlete_id,
        "log_date": current_date.strftime("%Y-%m-%d"),
        "rpe": 5, 
        "duration_minutes": 60,
        "sleep_quality": 8, # Good sleep
        "fatigue": 3,       # Low fatigue
        "soreness": 3
    }
    requests.post(f"{BASE_URL}/api/logs/submit", json=payload)

# 3. Request Nominal Plan
nominal_date = start_date + timedelta(days=28)
print(f"\n--- TEST 1: Requesting Plan for {nominal_date.strftime('%Y-%m-%d')} (Nominal State) ---")
res = requests.post(f"{BASE_URL}/api/plan/generate?athlete_id={athlete_id}&target_date={nominal_date.strftime('%Y-%m-%d')}&current_fatigue=3&current_sleep=8")
try:
    print(res.json()['plan'])
except Exception:
    print(res.text)

# 4. Simulate ACWR Spike & High Fatigue (Last 7 Days)
# RPE 9, 120 mins -> Daily load = 1080
print("\nInjecting ACWR Spike & High Fatigue data for the last 7 days...")
for i in range(28, 35):
    current_date = start_date + timedelta(days=i)
    payload = {
        "athlete_id": athlete_id,
        "log_date": current_date.strftime("%Y-%m-%d"),
        "rpe": 9, 
        "duration_minutes": 120,
        "sleep_quality": 4, # Poor sleep -> Triggers Rule 3
        "fatigue": 8,       # High fatigue -> Triggers Rule 3
        "soreness": 8
    }
    requests.post(f"{BASE_URL}/api/logs/submit", json=payload)

# 5. Request Revised Plan
spike_date = start_date + timedelta(days=35)
print(f"\n--- TEST 2: Requesting Revised Plan for {spike_date.strftime('%Y-%m-%d')} (After Load Spike) ---")
# Sending fatigue=8 and sleep=4 which triggers Rule 3, and the backend calculates ACWR > 1.5 which triggers Rule 4
res2 = requests.post(f"{BASE_URL}/api/plan/generate?athlete_id={athlete_id}&target_date={spike_date.strftime('%Y-%m-%d')}&current_fatigue=8&current_sleep=4")
try:
    print(res2.json()['plan'])
except Exception:
    print(res2.text)
