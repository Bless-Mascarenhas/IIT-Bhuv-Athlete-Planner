import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_func_pattern = r'@app\.get\("/api/plan/today"\)[\s\S]*?return \{[\s\S]*?"quests": quests\n    \}'

new_func = """@app.get("/api/plan/today")
def get_today_plan(athlete_id: int = 1, plan_date: Optional[str] = None):
    \"\"\"Returns 7-day rolling Quests.\"\"\"
    target_date_str = plan_date if plan_date else date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, athlete_id, plan_date, intensity_category, target_load, status,
               revision_reason, quest_title, session_description, task_type,
               target_rpe, duration_minutes, target_steps, target_calories, is_completed, completed_at
        FROM training_plans
        WHERE athlete_id = ? AND plan_date >= ?
        ORDER BY plan_date ASC, id ASC
    ''', (athlete_id, target_date_str))
    rows = cursor.fetchall()
    conn.close()

    quests = [dict(r) for r in rows]
    return {
        "status": "success",
        "plan_date": target_date_str,
        "quests": quests
    }"""

code = re.sub(old_func_pattern, new_func, code)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated main.py")
