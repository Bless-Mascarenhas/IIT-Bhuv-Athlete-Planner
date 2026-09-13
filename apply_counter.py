import sqlite3
import os
import re

# 1. Update Database (add goal_end_date)
conn = sqlite3.connect('backend/athlete_planner.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE users ADD COLUMN goal_end_date DATE")
    conn.commit()
except sqlite3.OperationalError:
    pass # Column already exists
conn.close()

# 2. Update main.py
with open('backend/main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# Update POST /api/user/goal to set goal_end_date
old_update_goal = """@app.post("/api/user/goal")
def update_user_goal(goal: str = Body(..., embed=True), user_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active_goal = ? WHERE id = ?", (goal, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Goal updated successfully", "active_goal": goal}"""

new_update_goal = """@app.post("/api/user/goal")
def update_user_goal(goal: str = Body(..., embed=True), user_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    end_date = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d")
    cursor.execute("UPDATE users SET active_goal = ?, goal_end_date = ? WHERE id = ?", (goal, end_date, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Goal updated successfully", "active_goal": goal, "goal_end_date": end_date}

@app.post("/api/user/goal/complete")
def complete_user_goal(user_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active_goal = NULL, goal_end_date = NULL WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Goal completed"}"""

main_code = main_code.replace(old_update_goal, new_update_goal)

# Update user profile SELECT to include goal_end_date
main_code = main_code.replace("SELECT id, name, email, daily_streak, current_streak, sport_type, active_goal\n", "SELECT id, name, email, daily_streak, current_streak, sport_type, active_goal, goal_end_date\n")
main_code = main_code.replace('"active_goal": user_dict.get("active_goal", "Stay Fit")', '"active_goal": user_dict.get("active_goal", "Stay Fit"),\n        "goal_end_date": user_dict.get("goal_end_date")')

# Update get_today_plan to enforce exactly 7 days
old_get_plan = """    quests = [dict(r) for r in rows]
    return {
        "status": "success",
        "plan_date": target_date_str,
        "quests": quests
    }"""

new_get_plan = """    quests = [dict(r) for r in rows]
    
    # ENFORCE ROLLING 7 DAYS: If less than 7 days exist from today onward, regenerate to top it up!
    # A single day could have multiple quests, so we count unique dates.
    unique_dates = set(q['plan_date'] for q in quests)
    if len(unique_dates) < 7 and target_date_str == date.today().strftime("%Y-%m-%d"):
        cursor.execute("SELECT active_goal FROM users WHERE id = ?", (athlete_id,))
        user_row = cursor.fetchone()
        active_goal = user_row["active_goal"] if user_row and user_row["active_goal"] else "Stay Fit"
        
        from agent import generate_weekly_plan
        plan_response = generate_weekly_plan(athlete_id, target_date_str, None, None, active_goal)
        
        # Clear existing uncompleted entries from today forward
        cursor.execute("DELETE FROM training_plans WHERE athlete_id = ? AND plan_date >= ?", (athlete_id, target_date_str))
        
        for day in plan_response.get("weekly_plan", []):
            plan_date = day["date"]
            cursor.execute('''
                INSERT INTO training_plans (
                    athlete_id, plan_date, intensity_category, target_load, 
                    status, revision_reason, quest_title, session_description, task_type, target_rpe, duration_minutes, target_steps, target_calories, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                athlete_id, plan_date, day["intensity"], day.get("target_rpe", 5) * day.get("duration_mins", 30),
                "planned", ", ".join(plan_response.get("constraint_reasons", [])) if plan_response.get("was_revised") else "",
                f"{day['intensity']} Training", day["session_description"], "workout", 
                day.get("target_rpe", 5), day.get("duration_mins", 30), day.get("target_steps", 10000), day.get("target_calories", 2500)
            ))
        conn.commit()
        
        # Refetch the newly generated 7 days
        cursor.execute('''
            SELECT id, athlete_id, plan_date, intensity_category, target_load, status,
                   revision_reason, quest_title, session_description, task_type,
                   target_rpe, duration_minutes, target_steps, target_calories, is_completed, completed_at
            FROM training_plans
            WHERE athlete_id = ? AND plan_date >= ?
            ORDER BY plan_date ASC, id ASC
        ''', (athlete_id, target_date_str))
        rows = cursor.fetchall()
        quests = [dict(r) for r in rows]

    return {
        "status": "success",
        "plan_date": target_date_str,
        "quests": quests
    }"""

main_code = main_code.replace(old_get_plan, new_get_plan)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)

print("Backend updated.")
