import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# Add active_goal to PlanRequest
main_code = main_code.replace("class PlanRequest(BaseModel):", "class PlanRequest(BaseModel):\n    active_goal: Optional[str] = None")

# Add /api/user/goal endpoint
goal_endpoint = """
@app.post("/api/user/goal")
def update_user_goal(goal: str = Body(..., embed=True), user_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active_goal = ? WHERE id = ?", (goal, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Goal updated successfully", "active_goal": goal}

"""
main_code = main_code.replace("# --- User Profile & Streak API ---", "# --- User Profile & Streak API ---\n" + goal_endpoint)

# Fix profile endpoint to return active_goal
main_code = main_code.replace("SELECT id, name, email, daily_streak, current_streak, sport_type", "SELECT id, name, email, daily_streak, current_streak, sport_type, active_goal")
main_code = main_code.replace('"current_streak": user_dict["current_streak"]', '"current_streak": user_dict["current_streak"],\n        "active_goal": user_dict.get("active_goal", "Stay Fit")')

# Modify /api/plan/generate logic
old_plan_generate = """        # Generate 1-day rolling quests
        plan_response = generate_daily_quests(aid, target_date_str, fatigue, sleep)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing uncompleted/planned entries for this target date to ensure exactly one day of active quests
        cursor.execute(
            "DELETE FROM training_plans WHERE athlete_id = ? AND plan_date = ?",
            (aid, target_date_str)
        )

        for q in plan_response["quests"]:
            cursor.execute('''
                INSERT INTO training_plans (
                    athlete_id, plan_date, intensity_category, target_load, 
                    status, revision_reason, quest_title, session_description, task_type, target_rpe, duration_minutes, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                aid, target_date_str, q["intensity_category"], q["target_load"],
                "planned", ", ".join(plan_response["constraint_reasons"]) if plan_response["was_revised"] else "",
                q["quest_title"], q["session_description"], q["task_type"], q["target_rpe"], q["duration_minutes"]
            ))

        conn.commit()
        conn.close()

        return plan_response"""

new_plan_generate = """        # Fetch user's active goal
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT active_goal FROM users WHERE id = ?", (aid,))
        user_row = cursor.fetchone()
        active_goal = user_row["active_goal"] if user_row and user_row["active_goal"] else "Stay Fit"
        
        # Override goal if provided in payload
        if payload and payload.active_goal:
            active_goal = payload.active_goal
            cursor.execute("UPDATE users SET active_goal = ? WHERE id = ?", (active_goal, aid))
            conn.commit()

        # Generate 7-day rolling plan
        from agent import generate_weekly_plan
        plan_response = generate_weekly_plan(aid, target_date_str, fatigue, sleep, active_goal)

        # Clear existing uncompleted entries from today forward
        cursor.execute(
            "DELETE FROM training_plans WHERE athlete_id = ? AND plan_date >= ?",
            (aid, target_date_str)
        )

        for day in plan_response.get("weekly_plan", []):
            plan_date = day["date"]
            cursor.execute('''
                INSERT INTO training_plans (
                    athlete_id, plan_date, intensity_category, target_load, 
                    status, revision_reason, quest_title, session_description, task_type, target_rpe, duration_minutes, target_steps, target_calories, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                aid, plan_date, day["intensity"], day.get("target_rpe", 5) * day.get("duration_mins", 30),
                "planned", ", ".join(plan_response.get("constraint_reasons", [])) if plan_response.get("was_revised") else "",
                f"{day['intensity']} Training", day["session_description"], "workout", 
                day.get("target_rpe", 5), day.get("duration_mins", 30), day.get("target_steps", 10000), day.get("target_calories", 2500)
            ))

        conn.commit()
        conn.close()

        return plan_response"""

main_code = main_code.replace(old_plan_generate, new_plan_generate)

# Update GET /api/plan endpoint to fetch 7 days instead of just target_date
old_get_plan = """    cursor.execute('''
        SELECT id, plan_date, intensity_category, target_load, status, revision_reason, 
               quest_title, session_description, task_type, target_rpe, duration_minutes, is_completed
        FROM training_plans 
        WHERE athlete_id = ? AND plan_date = ?
    ''', (athlete_id, target_date_str))"""

new_get_plan = """    cursor.execute('''
        SELECT id, plan_date, intensity_category, target_load, status, revision_reason, 
               quest_title, session_description, task_type, target_rpe, duration_minutes, target_steps, target_calories, is_completed
        FROM training_plans 
        WHERE athlete_id = ? AND plan_date >= ? ORDER BY plan_date ASC LIMIT 7
    ''', (athlete_id, target_date_str))"""

main_code = main_code.replace(old_get_plan, new_get_plan)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)

print("Main API updated.")
