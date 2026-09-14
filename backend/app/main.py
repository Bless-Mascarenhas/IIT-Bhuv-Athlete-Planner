import os
import csv
from datetime import date, datetime, timedelta
from typing import List, Optional, Union, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import get_onboarding_response, generate_daily_quests, generate_weekly_plan
from .database import init_db, get_db_connection
from .intent_router import process_chat

# Initialize tables and dynamic migrations on startup
init_db()

app = FastAPI(title="Pace - Autonomous Athlete Performance Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Lightweight endpoint to wake up the server."""
    return {"status": "awake"}

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class OnboardingRequest(BaseModel):
    name: str
    sport_type: str
    position: str
    active_goal: str
    athlete_tier: Optional[str] = "Semi-Pro"

@app.post("/auth/register")
def register_user(req: RegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, is_guest) VALUES (%s, %s, %s, false) RETURNING id",
            (req.name, req.email, req.password)
        )
        user_id = cursor.fetchone()['id']
        conn.commit()
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.post("/auth/login")
def login_user(req: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s AND password_hash = %s", (req.email, req.password))
    u = cursor.fetchone()
    conn.close()
    if u:
        return {"status": "success", "user_id": u['id']}
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/auth/guest")
def guest_login():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, sport_type, is_guest) VALUES ('Guest', 'General', true) RETURNING id"
    )
    user_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()
    return {"status": "success", "user_id": user_id}

@app.put("/auth/upgrade/{user_id}")
def upgrade_guest(user_id: int, req: RegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET email = %s, password_hash = %s, is_guest = false WHERE id = %s",
            (req.email, req.password, user_id)
        )
        conn.commit()
        return {"status": "success", "message": "Account upgraded successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.put("/profile/{user_id}")
def update_profile(user_id: int, req: OnboardingRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    end_date = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d")
    cursor.execute('''
        UPDATE users 
        SET name = %s, sport_type = %s, position = %s, active_goal = %s, goal_end_date = %s, athlete_tier = %s
        WHERE id = %s
    ''', (req.name, req.sport_type, req.position, req.active_goal, end_date, req.athlete_tier, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Profile updated successfully"}


# --- Pydantic Models for Input Validation ---

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    history: List[ChatMessage]


class ChatMessageRequest(BaseModel):
    athlete_id: Optional[int] = 1
    message: str
    history: Optional[List[dict]] = []


class DailyLog(BaseModel):
    athlete_id: int
    log_date: date
    rpe: int
    duration_minutes: int
    sleep_quality: int
    fatigue: int
    soreness: int


class Event(BaseModel):
    athlete_id: int
    event_date: date
    event_type: str
    duration_minutes: Optional[int] = 0


class PlanRequest(BaseModel):
    active_goal: Optional[str] = None
    athlete_id: Optional[int] = 1
    target_date: Optional[Union[date, str]] = None
    current_fatigue: Optional[int] = None
    current_sleep: Optional[int] = None


class QuestCompleteRequest(BaseModel):
    is_completed: Optional[bool] = True
    quest_id: Optional[int] = None
    athlete_id: Optional[int] = 1


class HealthSyncRequest(BaseModel):
    user_id: Optional[int] = 1
    log_date: Optional[Union[date, str]] = None
    steps: Optional[int] = 0
    active_calories: Optional[float] = 0.0
    distance_meters: Optional[float] = 0.0
    sleep_minutes: Optional[int] = 0
    resting_hr: Optional[float] = 0.0
    hrv: Optional[float] = 0.0
    source: Optional[str] = "google_fit"


# --- Core Routes ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Athlete Planner API is running. Ready for Capacitor UI."}


@app.get("/api/data/acwr_history")
def get_acwr_history():
    """Reads user_data.csv and returns calculated ACWR history for Chart.js"""
    csv_path = os.path.join(os.path.dirname(__file__), "user_data.csv")
    history = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        return {"status": "error", "message": "user_data.csv not found"}
        
    for i in range(27, len(rows)):
        current_day = rows[i]
        acute_sum = sum(float(rows[j]['RPE']) * float(rows[j]['Duration_mins']) for j in range(i-6, i+1))
        chronic_sum = sum(float(rows[j]['RPE']) * float(rows[j]['Duration_mins']) for j in range(i-27, i+1))
        chronic_weekly_avg = chronic_sum / 4.0
        
        acwr = round(acute_sum / chronic_weekly_avg, 2) if chronic_weekly_avg > 0 else 0
        history.append({
            "date": current_day['Date'],
            "acwr": acwr,
            "workload": float(current_day['RPE']) * float(current_day['Duration_mins'])
        })
        
    return {"status": "success", "history": history}


@app.post("/api/onboard/chat")
def onboard_chat(request: ChatRequest):
    """Endpoint for the 'Grill' Agent."""
    history = [{"role": m.role, "content": m.content} for m in request.history]
    try:
        response = get_onboarding_response(history)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat_endpoint(payload: ChatMessageRequest):
    """AI Intent Router endpoint: classifies chat and executes autonomous DB updates."""
    try:
        result = process_chat(
            athlete_id=payload.athlete_id or 1,
            message=payload.message,
            history=payload.history or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- R1: 1-Day Rolling Quests Generator ---

@app.post("/api/plan/generate")
def generate_plan(
    payload: Optional[PlanRequest] = Body(None),
    athlete_id: Optional[int] = Query(None),
    target_date: Optional[str] = Query(None),
    current_fatigue: Optional[int] = Query(None),
    current_sleep: Optional[int] = Query(None)
):
    """
    Generates a 1-day rolling Quests plan.
    Accepts input via query parameters OR JSON body.
    Persists exactly one day of quests to SQLite training_plans table.
    """
    try:
        # Resolve athlete_id
        aid = 1
        if payload and payload.athlete_id is not None:
            aid = payload.athlete_id
        elif athlete_id is not None:
            aid = athlete_id

        # Resolve target_date
        raw_date = None
        if payload and payload.target_date is not None:
            raw_date = payload.target_date
        elif target_date is not None:
            raw_date = target_date

        if isinstance(raw_date, date):
            target_date_str = raw_date.strftime("%Y-%m-%d")
        elif isinstance(raw_date, str) and raw_date.strip():
            target_date_str = raw_date.strip()
        else:
            target_date_str = date.today().strftime("%Y-%m-%d")

        # Resolve fatigue and sleep
        fatigue = payload.current_fatigue if (payload and payload.current_fatigue is not None) else current_fatigue
        sleep = payload.current_sleep if (payload and payload.current_sleep is not None) else current_sleep

        # Generate 1-day rolling quests
        plan_response = generate_daily_quests(aid, target_date_str, fatigue, sleep)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing uncompleted/planned entries for this target date to ensure exactly one day of active quests
        cursor.execute(
            "DELETE FROM training_plans WHERE athlete_id = %s AND plan_date = ?",
            (aid, target_date_str)
        )

        inserted_quests = []
        for quest in plan_response.get("quests", []):
            task_type = quest.get("task_type", "workout")
            target_rpe = int(quest.get("target_rpe", 5))
            duration_minutes = int(quest.get("duration_minutes", 30))
            intensity_cat = quest.get("intensity_category", plan_response.get("intensity", "Moderate"))
            target_load = float(quest.get("target_load", target_rpe * duration_minutes))
            quest_title = quest.get("quest_title", "Daily Quest")
            session_desc = quest.get("session_description", "")
            reasoning = quest.get("agent_reasoning", "")

            cursor.execute('''
                INSERT INTO training_plans 
                (athlete_id, plan_date, intensity_category, target_load, status, revision_reason,
                 quest_title, session_description, task_type, target_rpe, duration_minutes, is_completed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            ''', (
                aid,
                target_date_str,
                intensity_cat,
                target_load,
                "planned",
                reasoning,
                quest_title,
                session_desc,
                task_type,
                target_rpe,
                duration_minutes
            ))
            q_id = cursor.lastrowid

            inserted_quests.append({
                "id": q_id,
                "athlete_id": aid,
                "plan_date": target_date_str,
                "quest_title": quest_title,
                "session_description": session_desc,
                "task_type": task_type,
                "intensity_category": intensity_cat,
                "target_rpe": target_rpe,
                "duration_minutes": duration_minutes,
                "target_load": target_load,
                "is_completed": 0,
                "completed_at": None,
                "agent_reasoning": reasoning
            })

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "plan_date": target_date_str,
            "intensity": plan_response.get("intensity", "Moderate"),
            "was_revised": plan_response.get("was_revised", False),
            "constraint_reasons": plan_response.get("constraint_reasons", []),
            "quests": inserted_quests
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/plan/today")
def get_today_plan(athlete_id: int = 1, plan_date: Optional[str] = None):
    """Returns 7-day rolling Quests."""
    target_date_str = plan_date if plan_date else date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, athlete_id, plan_date, intensity_category, target_load, status,
               revision_reason, quest_title, session_description, task_type,
               target_rpe, duration_minutes, target_steps, target_calories, is_completed, completed_at
        FROM training_plans
        WHERE athlete_id = %s AND plan_date >= %s
        ORDER BY plan_date ASC, id ASC
    ''', (athlete_id, target_date_str))
    rows = cursor.fetchall()
    conn.close()

    quests = [dict(r) for r in rows]
    
    # ENFORCE ROLLING 7 DAYS: If less than 7 days exist from today onward, regenerate to top it up!
    # A single day could have multiple quests, so we count unique dates.
    unique_dates = set(q['plan_date'] for q in quests)
    if len(unique_dates) < 7 and target_date_str == date.today().strftime("%Y-%m-%d"):
        cursor.execute("SELECT active_goal FROM users WHERE id = ?", (athlete_id,))
        user_row = cursor.fetchone()
        active_goal = user_row["active_goal"] if user_row and user_row["active_goal"] else "Stay Fit"
        
        from .agent import generate_weekly_plan
        plan_response = generate_weekly_plan(athlete_id, target_date_str, None, None, active_goal)
        
        # Clear existing uncompleted entries from today forward
        cursor.execute("DELETE FROM training_plans WHERE athlete_id = %s AND plan_date >= ?", (athlete_id, target_date_str))
        
        for day in plan_response.get("weekly_plan", []):
            plan_date = day["date"]
            cursor.execute('''
                INSERT INTO training_plans (
                    athlete_id, plan_date, intensity_category, target_load, 
                    status, revision_reason, quest_title, session_description, task_type, target_rpe, duration_minutes, target_steps, target_calories, is_completed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
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
            WHERE athlete_id = %s AND plan_date >= %s
            ORDER BY plan_date ASC, id ASC
        ''', (athlete_id, target_date_str))
        rows = cursor.fetchall()
        quests = [dict(r) for r in rows]

    return {
        "status": "success",
        "plan_date": target_date_str,
        "quests": quests
    }


# --- R1: Quest Completion & Streak Tracking ---

def _complete_quest_logic(quest_id: int, athlete_id: Optional[int] = None, is_completed: bool = True):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find quest
    cursor.execute("SELECT id, athlete_id, plan_date, is_completed FROM training_plans WHERE id = ?", (quest_id,))
    quest = cursor.fetchone()
    if not quest:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Quest with id {quest_id} not found")

    aid = quest['athlete_id'] or athlete_id or 1
    plan_date_str = quest['plan_date']
    today_str = date.today().strftime("%Y-%m-%d")

    completed_int = 1 if is_completed else 0
    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_completed else None
    status_str = "completed" if is_completed else "planned"

    # Update training_plans table
    cursor.execute('''
        UPDATE training_plans
        SET is_completed = %s, completed_at = %s, status = %s
        WHERE id = %s
    ''', (completed_int, now_ts, status_str, quest_id))
    conn.commit() # Commit early to prevent race conditions when completing multiple tasks quickly

    # Retrieve athlete / user streak
    cursor.execute("SELECT id, daily_streak, current_streak, last_streak_date, last_active_date FROM users WHERE id = ?", (aid,))
    user = cursor.fetchone()
    if not user:
        # Fallback to user 1
        cursor.execute("SELECT id, daily_streak, current_streak, last_streak_date, last_active_date FROM users WHERE id = 1")
        user = cursor.fetchone()

    daily_streak = user['daily_streak'] if (user and user['daily_streak'] is not None) else 0

    # Always check stats to determine all_completed
    cursor.execute('''
        SELECT COUNT(*) as total, SUM(is_completed) as completed
        FROM training_plans
        WHERE athlete_id = %s AND plan_date = %s
    ''', (aid, plan_date_str))
    stats = cursor.fetchone()
    all_completed = (stats['total'] > 0 and stats['total'] == stats['completed'])
    
    last_streak = user['last_streak_date'] if user else None

    if is_completed:
        # Increment streak only if ALL quests for today are completed
        if all_completed and last_streak != today_str:
            daily_streak += 1
            last_streak = today_str
    else:
        # Decrement streak if they unchecked a task and it was previously all completed today
        if not all_completed and last_streak == today_str:
            daily_streak = max(0, daily_streak - 1)
            # Roll back last_streak_date to yesterday so it can be re-earned
            last_streak = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if user:
        cursor.execute('''
            UPDATE users
            SET daily_streak = %s, current_streak = %s, last_streak_date = %s, last_active_date = %s
            WHERE id = %s
        ''', (daily_streak, daily_streak, last_streak, today_str, user['id']))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "quest_id": quest_id,
        "is_completed": completed_int,
        "daily_streak": daily_streak,
        "current_streak": daily_streak
    }


@app.post("/api/quests/{quest_id}/complete")
def complete_quest(quest_id: int, payload: Optional[QuestCompleteRequest] = Body(None)):
    """Toggles completion state of a daily quest and updates user streak."""
    is_completed = payload.is_completed if (payload and payload.is_completed is not None) else True
    aid = payload.athlete_id if (payload and payload.athlete_id is not None) else None
    return _complete_quest_logic(quest_id, aid, is_completed)


@app.post("/api/plan/quest/{quest_id}/complete")
def complete_quest_alt(quest_id: int, payload: Optional[QuestCompleteRequest] = Body(None)):
    """Alternate URL route for quest completion."""
    return complete_quest(quest_id, payload)


@app.post("/api/plan/complete-quest")
def complete_quest_body(payload: QuestCompleteRequest):
    """Body-based endpoint for quest completion."""
    if not payload.quest_id:
        raise HTTPException(status_code=400, detail="quest_id is required in body")
    is_completed = payload.is_completed if payload.is_completed is not None else True
    return _complete_quest_logic(payload.quest_id, payload.athlete_id, is_completed)


# --- User Profile & Streak API ---

@app.post("/api/user/goal")
def update_user_goal(goal: str = Body(..., embed=True), user_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    end_date = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d")
    cursor.execute("UPDATE users SET active_goal = %s, goal_end_date = %s WHERE id = %s", (goal, end_date, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Goal updated successfully", "active_goal": goal, "goal_end_date": end_date}

@app.post("/api/user/goal/complete")
def complete_user_goal(user_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active_goal = NULL, goal_end_date = NULL WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Goal completed"}



@app.get("/api/user/profile")
def get_user_profile(user_id: int = 1):
    """Returns athlete profile and current streak information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, daily_streak, current_streak, sport_type, position, athlete_tier, active_goal, last_active_date, last_streak_date, created_at FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = dict(user)

    # Streak loss logic: If the last time they completed a daily streak was more than 1 day ago, reset it to 0
    if user_dict['last_streak_date']:
        try:
            last_streak_d = user_dict['last_streak_date']
            if isinstance(last_streak_d, str):
                last_streak_d = datetime.strptime(last_streak_d, "%Y-%m-%d").date()
            if (date.today() - last_streak_d).days > 1:
                cursor.execute("UPDATE users SET daily_streak = 0, current_streak = 0 WHERE id = %s", (user_id,))
                conn.commit()
                user_dict['daily_streak'] = 0
                user_dict['current_streak'] = 0
        except Exception:
            pass
    return {
        "status": "success",
        "user": user_dict,
        "id": user_dict["id"],
        "name": user_dict["name"],
        "daily_streak": user_dict["daily_streak"],
        "current_streak": user_dict["current_streak"],
        "active_goal": user_dict.get("active_goal", "Stay Fit"),
        "goal_end_date": user_dict.get("goal_end_date"),
        "athlete_tier": user_dict.get("athlete_tier", "Semi-Pro")
    }


@app.get("/api/user/streak")
def get_user_streak(user_id: int = 1):
    """Returns user daily streak counter."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, daily_streak, current_streak, last_streak_date FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"status": "success", "id": 1, "daily_streak": 12, "current_streak": 12}

    user_dict = dict(user)
    if user_dict['last_streak_date']:
        try:
            last_streak_d = user_dict['last_streak_date']
            if isinstance(last_streak_d, str):
                last_streak_d = datetime.strptime(last_streak_d, "%Y-%m-%d").date()
            if (date.today() - last_streak_d).days > 1:
                cursor.execute("UPDATE users SET daily_streak = 0, current_streak = 0 WHERE id = %s", (user_id,))
                conn.commit()
                user_dict['daily_streak'] = 0
                user_dict['current_streak'] = 0
        except Exception:
            pass

    return {
        "status": "success",
        "id": user_dict["id"],
        "name": user_dict["name"],
        "daily_streak": user_dict["daily_streak"],
        "current_streak": user_dict["current_streak"],
        "last_streak_date": user_dict["last_streak_date"]
    }


# --- Health & Telemetry Routes ---

@app.post("/api/health/sync")
def sync_health_telemetry(payload: HealthSyncRequest):
    """Ingests biometric telemetry from Google Fit or Mock Provider into google_fit_logs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    log_d = payload.log_date
    if isinstance(log_d, date):
        log_date_str = log_d.strftime("%Y-%m-%d")
    elif isinstance(log_d, str) and log_d.strip():
        log_date_str = log_d.strip()
    else:
        log_date_str = date.today().strftime("%Y-%m-%d")

    cursor.execute('''
        INSERT INTO google_fit_logs
        (user_id, log_date, steps, active_calories, calories_burned, distance_meters, sleep_minutes, resting_hr, heart_rate_resting, hrv, source, synced_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, log_date) DO UPDATE SET
        steps = EXCLUDED.steps,
        active_calories = EXCLUDED.active_calories,
        calories_burned = EXCLUDED.calories_burned,
        distance_meters = EXCLUDED.distance_meters,
        sleep_minutes = EXCLUDED.sleep_minutes,
        resting_hr = EXCLUDED.resting_hr,
        heart_rate_resting = EXCLUDED.heart_rate_resting,
        hrv = EXCLUDED.hrv,
        source = EXCLUDED.source,
        synced_at = CURRENT_TIMESTAMP
    ''', (
        payload.user_id or 1,
        log_date_str,
        payload.steps or 0,
        payload.active_calories or 0.0,
        payload.active_calories or 0.0,
        payload.distance_meters or 0.0,
        payload.sleep_minutes or 0,
        payload.resting_hr or 0.0,
        payload.resting_hr or 0.0,
        payload.hrv or 0.0,
        payload.source or "google_fit"
    ))
    conn.commit()
    conn.close()

    return {"status": "success", "message": "Health telemetry synchronized successfully."}


@app.get("/api/health/today")
def get_today_health(user_id: int = 1, log_date: Optional[str] = None):
    """Retrieves biometric telemetry log for today."""
    target_date_str = log_date if log_date else date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM google_fit_logs WHERE user_id = %s AND log_date = %s
    ''', (user_id, target_date_str))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "status": "success",
            "log_date": target_date_str,
            "data": None
        }
    return {
        "status": "success",
        "log_date": target_date_str,
        "data": dict(row)
    }


# --- Logs & Events Routes (Preserved) ---

@app.post("/api/logs/submit")
def submit_daily_log(log: DailyLog):
    """Receives data from 'Pull from device' or 'Enter Manually' UI."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        acute_workload = log.rpe * log.duration_minutes
        
        cursor.execute('''
            INSERT INTO daily_logs (athlete_id, log_date, rpe, duration_minutes, sleep_quality, fatigue, soreness, acute_workload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (log.athlete_id, log.log_date.strftime("%Y-%m-%d"), log.rpe, log.duration_minutes, log.sleep_quality, log.fatigue, log.soreness, acute_workload))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Daily log recorded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
def get_events(athlete_id: int = 1):
    """Returns calendar events / matches for the athlete."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, athlete_id, event_date, event_type, duration_minutes FROM events WHERE athlete_id = %s ORDER BY event_date ASC", (athlete_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    """Deletes an event by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Event {event_id} deleted."}


@app.post("/api/events/add")
def add_event(event: Event):
    """Adds an upcoming match or training to the calendar."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (athlete_id, event_date, event_type, duration_minutes)
            VALUES (%s, %s, %s, %s)
        ''', (event.athlete_id, event.event_date.strftime("%Y-%m-%d"), event.event_type, event.duration_minutes))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Event added."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import random

@app.get("/api/data/dataset_health")
def get_dataset_health():
    """Pulls a random mock health metric object from Datasets/sports_performance_data.csv"""
    import os, csv
    csv_path = os.path.join(os.path.dirname(__file__), "..", "Datasets", "sports_performance_data.csv")
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            if not reader:
                raise Exception("Empty CSV")
            row = random.choice(reader)
            
            def parse_float(val, default):
                try: return float(val) if val else default
                except: return default

            hr_avg = parse_float(row.get('Average_Heart_Rate'), 64)
            hr_rest = parse_float(row.get('Resting_Heart_Rate'), 54)
            sleep_hours = parse_float(row.get('Sleep_Hours_per_Night'), 7.8)
            cal_intake = parse_float(row.get('Daily_Caloric_Intake'), 2500)
            train_hours = parse_float(row.get('Training_Hours_per_Week'), 10)
            
            return {
                "status": "success",
                "data": {
                    "steps": int((train_hours / 7.0) * 10000), 
                    "activeCalories": int(cal_intake * 0.25),
                    "caloriesBurned": int(cal_intake * 0.9),
                    "distanceMeters": int((train_hours / 7.0) * 8000),
                    "sleepMinutes": int(sleep_hours * 60),
                    "sleepHours": round(sleep_hours, 1),
                    "restingHeartRate": int(hr_rest),
                    "currentHeartRate": int(hr_avg),
                    "hrvMs": 65,
                    "date": date.today().strftime("%Y-%m-%d"),
                    "source": "dataset",
                    "athlete_name": row.get('Athlete_Name', 'Unknown')
                }
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/admin/restore-streaks")
def restore_streaks():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Restore existing accounts to a streak of 12
    cursor.execute("UPDATE users SET current_streak = 12, daily_streak = 12 WHERE is_guest = false")
    # Make sure guest accounts stay at 0
    cursor.execute("UPDATE users SET current_streak = 0, daily_streak = 0 WHERE is_guest = true")
    conn.commit()
    conn.close()
    return {"message": "Existing accounts restored to 12"}
