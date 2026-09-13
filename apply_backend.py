import sqlite3
import os
import re

# 1. Update database.py
with open('backend/database.py', 'r', encoding='utf-8') as f:
    db_code = f.read()

db_code = db_code.replace("'sport_type': 'TEXT DEFAULT \"Soccer\"',", "'sport_type': 'TEXT DEFAULT \"Soccer\"',\n        'active_goal': 'TEXT DEFAULT \"Stay Fit\"',")
db_code = db_code.replace("'completed_at': 'TIMESTAMP'", "'completed_at': 'TIMESTAMP',\n        'target_steps': 'INTEGER DEFAULT 10000',\n        'target_calories': 'INTEGER DEFAULT 2500'")

with open('backend/database.py', 'w', encoding='utf-8') as f:
    f.write(db_code)


# 2. Update agent.py
with open('backend/agent.py', 'r', encoding='utf-8') as f:
    agent_code = f.read()

agent_code = agent_code.replace("def generate_weekly_plan(athlete_id: int, start_date_str: str, fatigue: int = None, sleep: int = None) -> dict:", "def generate_weekly_plan(athlete_id: int, start_date_str: str, fatigue: int = None, sleep: int = None, active_goal: str = 'Stay Fit') -> dict:")
agent_code = agent_code.replace(" - 'duration_mins': int", " - 'duration_mins': int\\n\"\n                \" - 'target_steps': int\\n\"\n                \" - 'target_calories': int")
agent_code = agent_code.replace("f\"Current Constraints:\\n\"", "f\"Current Goal: {active_goal}\\n\"\n                f\"Current Constraints:\\n\"")

with open('backend/agent.py', 'w', encoding='utf-8') as f:
    f.write(agent_code)

print("Backend updated.")
