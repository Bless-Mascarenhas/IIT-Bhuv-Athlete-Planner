from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from agent import get_onboarding_response, generate_weekly_plan
from algorithm import get_db_connection

app = FastAPI(title="Athlete Performance Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for Input Validation
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Athlete Planner API is running. Ready for Capacitor UI."}

@app.post("/api/onboard/chat")
def onboard_chat(request: ChatRequest):
    """Endpoint for the 'Grill' Agent."""
    history = [{"role": m.role, "content": m.content} for m in request.history]
    try:
        response = get_onboarding_response(history)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plan/generate")
def generate_plan(athlete_id: int, target_date: date, current_fatigue: Optional[int] = None, current_sleep: Optional[int] = None):
    """Generates a 7-day rolling plan using constraints + Groq."""
    try:
        plan_response = generate_weekly_plan(athlete_id, target_date.strftime("%Y-%m-%d"), current_fatigue, current_sleep)
        
        # Save generated 7-day plan to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for day_plan in plan_response.get('weekly_plan', []):
            cursor.execute('''
                INSERT INTO training_plans (athlete_id, plan_date, intensity_category, target_load, status, revision_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                athlete_id, 
                day_plan.get('date'), 
                day_plan.get('intensity', 'Rest'),
                day_plan.get('target_rpe', 0) * day_plan.get('duration_mins', 0),
                'planned',
                day_plan.get('agent_reasoning', '')
            ))
        conn.commit()
        conn.close()
        
        return {"status": "success", "plan": plan_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/logs/submit")
def submit_daily_log(log: DailyLog):
    """Receives data from 'Pull from device' or 'Enter Manually' UI."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        acute_workload = log.rpe * log.duration_minutes
        
        cursor.execute('''
            INSERT INTO daily_logs (athlete_id, log_date, rpe, duration_minutes, sleep_quality, fatigue, soreness, acute_workload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log.athlete_id, log.log_date.strftime("%Y-%m-%d"), log.rpe, log.duration_minutes, log.sleep_quality, log.fatigue, log.soreness, acute_workload))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Daily log recorded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/add")
def add_event(event: Event):
    """Adds an upcoming match or training to the calendar."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (athlete_id, event_date, event_type, duration_minutes)
            VALUES (?, ?, ?, ?)
        ''', (event.athlete_id, event.event_date.strftime("%Y-%m-%d"), event.event_type, event.duration_minutes))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Event added."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
