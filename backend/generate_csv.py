import csv
from datetime import datetime, timedelta
import random
import os

csv_path = os.path.join(os.path.dirname(__file__), "user_data.csv")
start_date = datetime.now() - timedelta(days=60)

with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "RPE", "Duration_mins", "Sleep", "Fatigue"])
    for i in range(60):
        current = start_date + timedelta(days=i)
        # Days 1-53: Nominal (Safe ACWR zone ~ 0.8 - 1.2)
        if i < 53:
            rpe = random.randint(4, 6)
            duration = random.choice([45, 60, 75])
            sleep = random.randint(7, 9)
            fatigue = random.randint(2, 4)
        # Days 53-60: Extreme Spike to trigger ACWR > 1.5
        else:
            rpe = random.randint(8, 10)
            duration = random.choice([100, 120])
            sleep = random.randint(3, 5)
            fatigue = random.randint(7, 9)
        writer.writerow([current.strftime("%Y-%m-%d"), rpe, duration, sleep, fatigue])
print("user_data.csv generated successfully.")
