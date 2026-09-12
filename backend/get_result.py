import requests
import json

BASE_URL = "http://localhost:8000"

try:
    res = requests.post(f"{BASE_URL}/api/plan/generate?athlete_id=3&target_date=2026-09-13&current_fatigue=8&current_sleep=4")
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(res.json(), f, indent=2)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
